"""
Tests for Graph/tts.py — keyless speech synthesis and ffmpeg resolution.

This module exists because speech was the only part of the pipeline with no
free path: the podcast needed paid OpenAI `tts-1-hd`, and the video voiceover
needed Gemini TTS, whose free tier allows a few requests per minute — not
enough for a 20-turn podcast script.
"""
import os
import sys
import wave
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from Graph import tts


class TestVoiceMapping:
    """Call sites keep their provider's voice vocabulary; this module translates.

    video.py asks for Gemini's "Puck" and podcast_studio.py for OpenAI's "nova".
    Mapping here means neither had to learn a third naming scheme when the
    synthesiser changed.
    """

    def test_openai_and_gemini_voice_names_are_translated(self):
        for name in ("nova", "onyx", "Puck", "Aoede", "alloy"):
            resolved = tts.resolve_voice(name)
            assert "Neural" in resolved, f"{name!r} resolved to {resolved!r}"

    def test_the_two_podcast_hosts_get_different_voices(self):
        """A two-host episode read in one voice stops sounding like a conversation."""
        assert tts.resolve_voice("nova") != tts.resolve_voice("onyx")

    def test_an_edge_voice_passes_through_unchanged(self):
        """So EDGE_TTS_VOICE_A can name any voice `edge-tts --list-voices` reports."""
        assert tts.resolve_voice("en-GB-SoniaNeural") == "en-GB-SoniaNeural"

    def test_an_unknown_name_falls_back_rather_than_failing(self):
        assert tts.resolve_voice("no-such-voice") == tts.EDGE_VOICE_NARRATOR
        assert tts.resolve_voice(None) == tts.EDGE_VOICE_NARRATOR
        assert tts.resolve_voice("") == tts.EDGE_VOICE_NARRATOR


class TestFfmpegResolution:
    """Whisper and moviepy shell out to a bare `ffmpeg`.

    This project installs ffmpeg as a Python wheel whose binary is neither on
    PATH nor named `ffmpeg`, and the resulting FileNotFoundError surfaces as
    "audio file could not be read" — indistinguishable from a corrupt input.
    """

    def test_an_ffmpeg_binary_is_discoverable(self):
        exe = tts.ffmpeg_exe()
        assert exe, "no ffmpeg found; install it or keep imageio-ffmpeg installed"
        assert Path(exe).exists()

    def test_ensure_ffmpeg_on_path_makes_the_bare_name_resolvable(self):
        import shutil

        assert tts.ensure_ffmpeg_on_path()
        assert shutil.which("ffmpeg"), (
            "the bare command name must resolve, because Whisper invokes "
            "`ffmpeg`, not the wheel's versioned filename"
        )


class TestAudioLayout:
    """Every synthesiser in the project returns one PCM layout.

    The podcast merger and video.save_pcm_as_wav both assume 24 kHz, 16-bit,
    mono. A second layout anywhere would concatenate into noise.
    """

    def test_layout_constants_match_what_the_consumers_assume(self):
        assert (tts.SAMPLE_RATE, tts.SAMPLE_WIDTH, tts.CHANNELS) == (24_000, 2, 1)

    def test_wav_writer_uses_that_layout(self, tmp_path):
        out = tmp_path / "probe.wav"
        # 0.5 s of silence at the module's layout.
        tts.save_pcm_as_wav(b"\x00" * (24_000 * 2 // 2), str(out))

        with wave.open(str(out)) as handle:
            assert handle.getframerate() == tts.SAMPLE_RATE
            assert handle.getsampwidth() == tts.SAMPLE_WIDTH
            assert handle.getnchannels() == tts.CHANNELS
            assert handle.getnframes() == 12_000

    def test_wav_writer_creates_missing_parent_directories(self, tmp_path):
        """Callers pass a path inside a per-run blog folder that may not exist."""
        out = tmp_path / "nested" / "deeper" / "probe.wav"
        tts.save_pcm_as_wav(b"\x00" * 100, str(out))
        assert out.exists()


class TestGracefulDegradation:
    """Speech is optional output; its absence must not raise into the graph."""

    def test_empty_text_returns_none_rather_than_calling_the_service(self, monkeypatch):
        assert tts.synthesize_mp3("") is None
        assert tts.synthesize_mp3("   ") is None
        assert tts.synthesize_mp3(None) is None

    def test_missing_edge_tts_reports_unavailable_instead_of_raising(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def blocked(name, *args, **kwargs):
            if name == "edge_tts":
                raise ImportError("no edge_tts")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", blocked)
        assert tts.synthesize_mp3("hello") is None
        assert tts.is_available() is False

    def test_is_available_requires_both_edge_tts_and_ffmpeg(self, monkeypatch):
        """MP3 is what edge-tts returns; PCM is what the callers need. Both links matter."""
        monkeypatch.setattr(tts, "ffmpeg_exe", lambda: None)
        assert tts.is_available() is False

    def test_failed_decode_returns_none(self, monkeypatch):
        monkeypatch.setattr(tts, "synthesize_mp3", lambda *a, **k: b"not actually mp3")
        monkeypatch.setattr(tts, "mp3_to_pcm", lambda *a, **k: None)
        assert tts.synthesize_pcm("hello") is None
        assert tts.synthesize_to_wav("hello") is None


@pytest.mark.skipif(
    os.getenv("SKIP_NETWORK_TESTS") == "1",
    reason="reaches Microsoft's Edge read-aloud endpoint",
)
class TestLiveSynthesis:
    """One end-to-end check that the keyless path actually produces audio.

    Mocked tests cannot catch the failure that matters here — the endpoint
    changing shape — so this makes one real request. It needs no credential,
    which is the whole point of the module.
    """

    def test_synthesis_produces_playable_audio(self, tmp_path):
        if not tts.is_available():
            pytest.skip("edge-tts or ffmpeg unavailable")

        path = tts.synthesize_to_wav(
            "Retrieval augmented generation grounds a model in your own documents.",
            str(tmp_path / "live.wav"),
            voice="nova",
        )
        if path is None:
            pytest.skip("Edge TTS endpoint unreachable from this network")

        with wave.open(path) as handle:
            seconds = handle.getnframes() / handle.getframerate()
        assert seconds > 1.0, f"only {seconds:.2f}s of audio produced"
