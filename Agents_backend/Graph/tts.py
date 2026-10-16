"""
tts.py — keyless text-to-speech and the ffmpeg binary the media stack needs.

WHY THIS MODULE EXISTS
----------------------
Speech synthesis was the only part of the pipeline with no free path. The
podcast needed OpenAI `tts-1-hd` (paid per character) and the video voiceover
needed `gemini-2.5-flash-preview-tts`, whose free tier allows roughly three
requests a minute — a 20-turn podcast script cannot be synthesised under that
limit without the run taking longer than the demo it is for.

Microsoft's Edge read-aloud endpoint serves the same neural voices Edge uses,
needs no credential, and is not rate-limited in any way that a single run will
notice. It is the primary synthesiser here; the per-provider fallbacks stay in
their own modules.

Everything returns 24 kHz, 16-bit, mono PCM — the format the podcast merger and
`video.save_pcm_as_wav` already assume — so no call site has to learn a second
audio layout.

FFMPEG
------
`openai-whisper` shells out to a bare `ffmpeg` and `moviepy` looks for one too,
but this project installs ffmpeg as a Python wheel (`imageio-ffmpeg`) whose
binary is not on PATH. `ensure_ffmpeg_on_path()` puts it there, which is what
makes local Whisper — the free word-timestamp path — actually usable.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Optional

logger = logging.getLogger("blog_pipeline")

# The audio layout every consumer in this project expects.
SAMPLE_RATE = 24_000
SAMPLE_WIDTH = 2      # bytes, 16-bit
CHANNELS = 1

# Edge voices chosen for contrast, so two podcast hosts are audibly distinct:
# Aria is bright and forward, Guy is lower and slower.
EDGE_VOICE_HOST_A = os.getenv("EDGE_TTS_VOICE_A", "en-US-AriaNeural")
EDGE_VOICE_HOST_B = os.getenv("EDGE_TTS_VOICE_B", "en-US-GuyNeural")
EDGE_VOICE_NARRATOR = os.getenv("EDGE_TTS_VOICE_NARRATOR", "en-US-ChristopherNeural")

# Gemini and OpenAI voice names appear in call sites that predate this module.
# Mapping them keeps those call sites unchanged instead of threading a new
# vocabulary through video.py and podcast_studio.py.
_VOICE_ALIASES = {
    # Gemini prebuilt voices
    "puck": EDGE_VOICE_NARRATOR,
    "aoede": EDGE_VOICE_HOST_A,
    "charon": EDGE_VOICE_HOST_B,
    "kore": EDGE_VOICE_HOST_A,
    "fenrir": EDGE_VOICE_HOST_B,
    # OpenAI voices
    "nova": EDGE_VOICE_HOST_A,
    "onyx": EDGE_VOICE_HOST_B,
    "alloy": EDGE_VOICE_NARRATOR,
    "shimmer": EDGE_VOICE_HOST_A,
    "echo": EDGE_VOICE_HOST_B,
}


def resolve_voice(voice: Optional[str]) -> str:
    """Translate a provider-specific voice name into an Edge voice.

    An unrecognised name that already looks like an Edge voice (they all
    contain a locale and end in "Neural") is passed through, so a user can set
    EDGE_TTS_VOICE_A to any voice `edge-tts --list-voices` reports.
    """
    if not voice:
        return EDGE_VOICE_NARRATOR
    if "Neural" in voice:
        return voice
    return _VOICE_ALIASES.get(voice.strip().lower(), EDGE_VOICE_NARRATOR)


# ---------------------------------------------------------------------------
# FFMPEG
# ---------------------------------------------------------------------------

def ffmpeg_exe() -> Optional[str]:
    """Absolute path to an ffmpeg binary, preferring one already on PATH."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        logger.warning(f"No ffmpeg available: {e}")
        return None


def ensure_ffmpeg_on_path() -> Optional[str]:
    """Make the bundled ffmpeg discoverable by tools that shell out to it.

    Whisper runs `ffmpeg -i ... -f s16le -` through subprocess and reports a
    FileNotFoundError as "audio file could not be read", which reads like a
    corrupt input rather than a missing dependency. Prepending the wheel's
    binary directory to PATH removes that failure mode for the whole process.
    """
    exe = ffmpeg_exe()
    if not exe:
        return None
    bin_dir = str(Path(exe).parent)
    path = os.environ.get("PATH", "")
    if bin_dir not in path.split(os.pathsep):
        os.environ["PATH"] = bin_dir + os.pathsep + path

    # Whisper and moviepy invoke the command name, not the path, and the wheel
    # ships the binary under a versioned name (ffmpeg-win-x86_64-v7.1.exe).
    # Provide a plain `ffmpeg` alongside it so the bare name resolves.
    plain = Path(bin_dir) / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not plain.exists():
        try:
            shutil.copy2(exe, plain)
            logger.info(f"   🔧 Exposed bundled ffmpeg as {plain}")
        except Exception as e:
            logger.warning(f"Could not expose ffmpeg as a plain name: {e}")
    return exe


# ---------------------------------------------------------------------------
# SYNTHESIS
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Run `coro` to completion whether or not a loop is already running.

    The pipeline calls into this from LangGraph worker threads, which have no
    event loop, and from FastAPI's thread pool, which does not either — but a
    CLI run under `asyncio.run` would. Handle both rather than assuming.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # A loop is already running in this thread: hand the coroutine to a fresh
    # loop on a separate thread rather than raising.
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def synthesize_mp3(text: str, voice: Optional[str] = None) -> Optional[bytes]:
    """Synthesise `text` with Edge TTS and return MP3 bytes, or None."""
    try:
        import edge_tts
    except ImportError:
        logger.warning("edge-tts not installed — keyless TTS unavailable. "
                       "Run: pip install edge-tts")
        return None

    clean = (text or "").strip()
    if not clean:
        return None

    edge_voice = resolve_voice(voice)

    async def _collect() -> bytes:
        chunks: list[bytes] = []
        communicate = edge_tts.Communicate(clean, edge_voice)
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                chunks.append(chunk["data"])
        return b"".join(chunks)

    try:
        audio = _run_async(_collect())
    except Exception as e:
        logger.warning(f"Edge TTS synthesis failed ({voice} → {edge_voice}): {e}")
        return None

    if not audio:
        logger.warning(f"Edge TTS returned no audio for voice {edge_voice}.")
        return None
    return audio


def mp3_to_pcm(mp3_bytes: bytes) -> Optional[bytes]:
    """Decode MP3 to raw 24 kHz 16-bit mono PCM using ffmpeg.

    Raw PCM rather than a WAV file because the podcast merger concatenates
    turns with silence between them and writes one header at the end; handing
    it framed WAVs would mean stripping headers back out.
    """
    exe = ffmpeg_exe()
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "-hide_banner", "-loglevel", "error",
             "-i", "pipe:0",
             "-f", "s16le", "-acodec", "pcm_s16le",
             "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
             "pipe:1"],
            input=mp3_bytes, capture_output=True, check=True,
        )
        return proc.stdout or None
    except subprocess.CalledProcessError as e:
        logger.warning(f"ffmpeg MP3→PCM decode failed: {e.stderr[:300].decode(errors='replace')}")
    except Exception as e:
        logger.warning(f"ffmpeg MP3→PCM decode failed: {e}")
    return None


def synthesize_pcm(text: str, voice: Optional[str] = None) -> Optional[bytes]:
    """Synthesise `text` and return raw 24 kHz 16-bit mono PCM, or None."""
    mp3 = synthesize_mp3(text, voice)
    if not mp3:
        return None
    return mp3_to_pcm(mp3)


def save_pcm_as_wav(pcm_bytes: bytes, output_path: str) -> None:
    """Write raw PCM to a WAV container with this module's audio layout."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)


def synthesize_to_wav(text: str, output_path: Optional[str] = None,
                      voice: Optional[str] = None) -> Optional[str]:
    """Synthesise `text` to a WAV file. Returns the path, or None on failure.

    With no `output_path` a temporary file is created — the shape
    `video.generate_tts_voiceover` already returns.
    """
    pcm = synthesize_pcm(text, voice)
    if not pcm:
        return None
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
    try:
        save_pcm_as_wav(pcm, output_path)
        return output_path
    except Exception as e:
        logger.warning(f"Failed to write WAV to {output_path}: {e}")
        return None


def is_available() -> bool:
    """True when keyless TTS can actually run: edge-tts plus an ffmpeg."""
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return False
    return ffmpeg_exe() is not None
