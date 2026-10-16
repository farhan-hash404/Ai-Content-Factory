import io
import json
import os
import re
import time
import random
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage

from Graph.state import State, GlobalImagePlan
from Graph.templates import DECIDE_IMAGES_SYSTEM
from .utils import logger, llm, _job, _emit, _safe_slug


def decide_images(state: State) -> dict:
    """
    Plans image placement based on the user's requested `num_images` count.
    If generate_images is False or num_images is 0, returns an empty image spec list.
    """
    generate_images = state.get("generate_images", True)
    num_images = state.get("num_images", 2)

    if not generate_images or num_images <= 0:
        logger.info("⏭️ Image generation disabled by user (num_images=0)")
        _emit(_job(state), "images", "completed", "Image generation skipped (user requested 0 images)", {"count": 0})
        return {"image_specs": []}

    _emit(_job(state), "images", "started", f"Planning {num_images} image placement(s)...")
    logger.info(f"🖼️ PLANNING {num_images} IMAGES ---")
    planner = llm.with_structured_output(GlobalImagePlan)

    custom_system_prompt = (
        f"{DECIDE_IMAGES_SYSTEM}\n\n"
        f"CRITICAL CONSTRAINT: You MUST plan EXACTLY {num_images} image(s) (no more, no less)."
    )

    image_plan = planner.invoke([
        SystemMessage(content=custom_system_prompt),
        HumanMessage(content=(
            f"Topic: {state.get('topic')}\n"
            f"Current Blog Content:\n{state.get('merged_md', '')}"
        )),
    ])

    specs = [img.model_dump() for img in image_plan.images[:num_images]]
    _emit(_job(state), "images", "working", f"Planned {len(specs)} image(s)", {"count": len(specs)})
    return {"image_specs": specs}


def _generate_image_openai_dalle(prompt: str, model: str | None = "dall-e-3", size: str | None = "1024x1024", quality: str | None = "standard", style: str | None = "vivid") -> Optional[bytes]:
    """Generates image using OpenAI DALL-E model with configured parameters."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = model or "dall-e-3"
    size = size or "1024x1024"
    quality = quality or "standard"
    style = style or "vivid"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        kwargs = {
            "model": model,
            "prompt": prompt[:1000],
            "n": 1,
            "size": size
        }
        if model == "dall-e-3":
            kwargs["quality"] = quality

        try:
            response = client.images.generate(**kwargs)
        except Exception as err:
            err_msg = str(err).lower()
            if "style" in err_msg or "quality" in err_msg or "unknown parameter" in err_msg:
                kwargs.pop("style", None)
                kwargs.pop("quality", None)
                response = client.images.generate(**kwargs)
            else:
                raise err
        if response.data and len(response.data) > 0:
            img_obj = response.data[0]
            if hasattr(img_obj, "b64_json") and img_obj.b64_json:
                import base64
                return base64.b64decode(img_obj.b64_json)
            if hasattr(img_obj, "url") and img_obj.url:
                req = urllib.request.Request(
                    img_obj.url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI Content Factory Engine"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return resp.read()
    except Exception as e:
        logger.warning(f"OpenAI image generation ({model}) failed: {e}")
    return None


def _generate_image_bytes_google(prompt: str) -> Optional[bytes]:
    """Generates image using Google GenAI (Gemini) with retries for rate limits."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)

        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image"),
                    contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                )
                if resp.candidates and resp.candidates[0].content.parts:
                    for part in resp.candidates[0].content.parts:
                        if part.inline_data:
                            return part.inline_data.data
                return None
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                    continue
                break
    except Exception as e:
        logger.warning(f"Google Gemini image generation skipped: {e}")
    return None


# Pollinations models to try, in order. `turbo` leads because `flux` is no
# longer free for anonymous callers — it answers
#   HTTP Error 402: Payment Required
# which is a hard paywall, not congestion, so retrying it is wasted time. It
# stays in the list after turbo so a POLLINATIONS_TOKEN holder still gets the
# better model, and `POLLINATIONS_MODELS=flux` restores the old behaviour.
_POLLINATIONS_MODELS = [
    m.strip() for m in os.getenv("POLLINATIONS_MODELS", "turbo,flux").split(",") if m.strip()
]


def _generate_image_pollinations(prompt: str) -> Optional[bytes]:
    """
    AI image generator using Pollinations.ai (free, zero API key required).

    This is the last link in the provider chain and — with no OPENAI_API_KEY and
    no paid Gemini tier — the only one that actually serves, so a single failure
    here is the difference between an illustrated article and an unillustrated
    one. Observed on a 2-image run that reported "Generated 1/2 images".

    Two distinct failure modes, handled differently:
      * 402 Payment Required — that model is paywalled. Move to the next model
        immediately; retrying cannot help.
      * timeout / 5xx / a suspiciously small body — the free queue is busy.
        Retry the same model with backoff.
    """
    encoded_prompt = urllib.parse.quote(prompt[:500])
    # Bounded worst case: attempts x timeout x models. At 3x90x2 a single image
    # could hold the node for nine minutes before reaching the Pexels fallback
    # that was always going to serve it; one observed timeout alone cost 90s.
    # 2x45x2 caps it at three minutes.
    attempts = int(os.getenv("POLLINATIONS_ATTEMPTS", "2"))
    timeout = float(os.getenv("POLLINATIONS_TIMEOUT", "45"))
    token = (os.getenv("POLLINATIONS_TOKEN") or "").strip()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI Content Factory Engine"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for model in _POLLINATIONS_MODELS:
        for attempt in range(1, attempts + 1):
            seed = random.randint(1000, 999999)
            url = (
                f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                f"?width=1024&height=600&model={model}&nologo=true&seed={seed}"
            )
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    data = response.read() if response.status == 200 else b""
                # The queue occasionally answers 200 with a tiny error page;
                # nothing under 1 KB is a 1024x600 render.
                if len(data) > 1024:
                    return data
                logger.warning(
                    f"Pollinations ({model}) returned {len(data)} bytes on attempt "
                    f"{attempt} — too small to be an image."
                )
            except urllib.error.HTTPError as e:
                if e.code in (401, 402, 403):
                    logger.warning(
                        f"Pollinations model {model!r} is not available without payment "
                        f"(HTTP {e.code}). Trying the next model."
                    )
                    break
                logger.warning(f"Pollinations ({model}) attempt {attempt}/{attempts} failed: {e}")
            except Exception as e:
                logger.warning(f"Pollinations ({model}) attempt {attempt}/{attempts} failed: {e}")

            if attempt < attempts:
                time.sleep((2 ** attempt) + random.random())

    logger.warning("Pollinations image generation failed on every model.")
    return None


_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "for", "with", "in", "on", "to", "at",
    "by", "from", "into", "over", "this", "that", "these", "those", "is", "are",
    "be", "as", "its", "it", "showing", "depicting", "illustration", "image",
    "diagram", "photo", "picture", "style", "clean", "modern", "minimal",
    "professional", "high", "quality", "detailed", "background", "colour",
    "color", "palette", "sleek", "minimalist", "render", "rendering",
    "vibrant", "futuristic", "photorealistic", "cinematic", "concept", "art",
    "shot", "view", "closeup", "close-up", "wide", "bright", "dark", "soft",
    "lighting", "aesthetic", "sharp", "crisp", "elegant", "abstract",
}


def _search_query_from_prompt(prompt: str, max_words: int = 4) -> str:
    """Reduce a long image prompt to a few content words for a stock search.

    Stock photo search is keyword-based, not prompt-based: handing it a
    paragraph of art direction returns nothing, while three or four nouns from
    the same text return something usable.
    """
    words = re.findall(r"[A-Za-z][A-Za-z-]{2,}", prompt or "")
    keep = [w for w in words if w.lower() not in _STOPWORDS]
    return " ".join((keep or words)[:max_words]) or "abstract technology"


def _fetch_pexels_photo(prompt: str) -> Optional[bytes]:
    """Download a landscape stock photo matching `prompt` from Pexels.

    NOT an AI-generated image, and the caller says so in the log. It is here
    because it is the only *reliable* free option: Pollinations' anonymous tier
    starts answering 402 after a couple of images, Gemini's image models have no
    free tier at all, and DALL-E needs credit. A relevant photograph beats an
    article with an empty figure slot.
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key or api_key.startswith("your-"):
        return None

    query = _search_query_from_prompt(prompt)
    url = (
        "https://api.pexels.com/v1/search"
        f"?query={urllib.parse.quote(query)}&orientation=landscape&per_page=5"
    )
    try:
        # The User-Agent is NOT optional. Pexels answers 403 Forbidden to
        # urllib's default "Python-urllib/3.x" while accepting the identical
        # request with a browser UA — the failure looks like a bad API key.
        req = urllib.request.Request(url, headers={
            "Authorization": api_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI Content Factory Engine",
        })
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        photos = payload.get("photos") or []
        if not photos:
            logger.info(f"  Pexels has no photo for query {query!r}.")
            return None
        # Vary which result is used so a run with several images does not place
        # the same photograph twice.
        photo = random.choice(photos)
        src = photo.get("src") or {}
        image_url = src.get("large") or src.get("original") or src.get("medium")
        if not image_url:
            return None
        with urllib.request.urlopen(
            urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=30,
        ) as response:
            data = response.read()
        if len(data) > 1024:
            logger.info(f"  📷 Stock photo from Pexels (query: {query!r}, "
                        f"by {photo.get('photographer', 'unknown')})")
            return data
    except Exception as e:
        logger.warning(f"Pexels photo search failed for {query!r}: {e}")
    return None


def _render_figure_locally(prompt: str) -> Optional[bytes]:
    """Draw a captioned gradient figure with Pillow. Never touches the network.

    The last link in the chain, and the only one that cannot fail for an
    external reason. Its job is to make the article's figure slots legible
    rather than to look generated: a blank slot renders as a broken-image icon
    in the UI and in every export, which reads as a bug.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    width, height = 1024, 600
    try:
        # Deterministic hue per prompt, so the same figure keeps its colour
        # across regenerations instead of flickering.
        base = abs(hash(prompt)) % 360
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)

        # Vertical gradient between two hues a little apart on the wheel.
        import colorsys
        top = colorsys.hls_to_rgb(base / 360.0, 0.30, 0.55)
        bottom = colorsys.hls_to_rgb(((base + 40) % 360) / 360.0, 0.14, 0.50)
        for y in range(height):
            t = y / (height - 1)
            draw.line(
                [(0, y), (width, y)],
                fill=tuple(int(255 * (a + (b - a) * t)) for a, b in zip(top, bottom)),
            )

        caption = _search_query_from_prompt(prompt, max_words=8).title()
        try:
            font = ImageFont.truetype("arial.ttf", 46)
        except Exception:
            font = ImageFont.load_default()

        # Wrap to roughly 26 characters a line so long captions stay on canvas.
        import textwrap
        lines = textwrap.wrap(caption, width=26) or [caption]
        line_height = 58
        start_y = (height - line_height * len(lines)) // 2
        for idx, line in enumerate(lines):
            box = draw.textbbox((0, 0), line, font=font)
            x = (width - (box[2] - box[0])) // 2
            y = start_y + idx * line_height
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
            draw.text((x, y), line, font=font, fill=(255, 255, 255))

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception as e:
        logger.warning(f"Local figure rendering failed: {e}")
        return None


def _generate_image_multi_provider(prompt: str, model: str | None = "dall-e-3", size: str | None = "1024x1024", quality: str | None = "standard", style: str | None = "vivid") -> Optional[bytes]:
    """
    Multi-provider image generation, tried in order until one returns bytes.

    `model` selects where the chain STARTS, not the only provider used, so a
    quota error never costs the run its illustrations:

        dall-e-2 / dall-e-3 / gpt-image-*  → OpenAI, Gemini, then the free tail
        gemini-* / imagen-*                → Gemini, then the free tail
        anything else (including the default when no OPENAI_API_KEY is set)
                                           → the free tail only

    The free tail is Pollinations → Pexels → a locally rendered figure, in
    descending order of "actually generated" and ascending order of
    reliability. Pollinations is genuine AI generation and needs no credential,
    but its anonymous tier starts returning 402 after a couple of images.
    Pexels returns a real photograph rather than generated art, which the log
    states plainly. The local renderer cannot fail for an external reason, so
    the article never ships with an empty figure slot — a slot that renders as
    a broken-image icon in the UI and in every export, and reads as a bug.
    """
    model = model or "dall-e-3"
    size = size or "1024x1024"
    quality = quality or "standard"
    style = style or "vivid"

    lowered = model.lower()
    is_openai_model = lowered.startswith(("dall-e", "gpt-image"))
    is_gemini_model = lowered.startswith(("gemini", "imagen"))

    # 1. OpenAI DALL-E — skipped unless an OpenAI image model was actually asked
    #    for. Previously this ran on every image: with no OPENAI_API_KEY it was
    #    a cheap no-op, but with a Gemini key mistakenly placed in
    #    OPENAI_API_KEY it became a slow 401 per image.
    if is_openai_model:
        image_bytes = _generate_image_openai_dalle(prompt, model=model, size=size, quality=quality, style=style)
        if image_bytes:
            logger.info(f"  🎨 Image generated via OpenAI {model}")
            return image_bytes

    # 2. Google Gemini
    if is_openai_model or is_gemini_model:
        image_bytes = _generate_image_bytes_google(prompt)
        if image_bytes:
            logger.info("  🎨 Image generated via Google Gemini")
            return image_bytes

    # 3. Pollinations — real AI generation, no credential, but a small
    #    anonymous quota that answers 402 once spent.
    image_bytes = _generate_image_pollinations(prompt)
    if image_bytes:
        logger.info("  🎨 Image generated via Pollinations AI (Free Zero-Key Engine)")
        return image_bytes

    # 4. Pexels — a real photograph, not generated art. Free and reliable.
    image_bytes = _fetch_pexels_photo(prompt)
    if image_bytes:
        return image_bytes

    # 5. Locally rendered figure — offline, and therefore cannot fail for an
    #    external reason. Keeps the figure slot from rendering as a broken image.
    image_bytes = _render_figure_locally(prompt)
    if image_bytes:
        logger.info("  🖍️ Rendered a local placeholder figure (no image provider available)")
        return image_bytes

    return None


def generate_and_place_images(state: State) -> dict:
    """Generate images, save them, and insert portable Markdown into the article."""
    image_specs = state.get("image_specs", [])
    merged_md = state.get("merged_md", "")

    if not image_specs:
        logger.info("⏭️ No image specs to process")
        _emit(_job(state), "images", "completed", "No images requested")
        return {}

    _emit(_job(state), "images", "working", f"Generating {len(image_specs)} AI image(s)...")
    logger.info(f"🎨 GENERATING {len(image_specs)} AI IMAGES ---")

    base_path = state.get("blog_folder", ".")
    assets_path = f"{base_path}/assets/images"
    Path(assets_path).mkdir(parents=True, exist_ok=True)

    generated_count = 0
    updated_md = merged_md

    # Default provider follows the credentials actually present. Defaulting to
    # "dall-e-3" with no OPENAI_API_KEY meant every image made a doomed OpenAI
    # attempt before reaching the free provider that was always going to serve
    # it. See _generate_image_multi_provider for the ordering this selects.
    _default_image_model = "dall-e-3" if os.getenv("OPENAI_API_KEY") else "pollinations-flux"
    image_model = state.get("image_model") or _default_image_model
    image_size = state.get("image_size") or "1024x1024"
    image_quality = state.get("image_quality") or "standard"
    image_style = state.get("image_style") or "vivid"

    for idx, img in enumerate(image_specs):
        logger.info(f"Processing image {idx+1}/{len(image_specs)}: {img.get('filename')}")
        img_bytes = _generate_image_multi_provider(
            img["prompt"],
            model=image_model,
            size=image_size,
            quality=image_quality,
            style=image_style
        )

        if img_bytes:
            img_slug = _safe_slug(img.get("filename", f"image_{idx+1}"))
            if not img_slug.endswith(".png"):
                img_slug += ".png"
            if idx > 0:
                img_filename = f"{idx+1}_{img_slug}"
            else:
                img_filename = img_slug

            full_path = Path(f"{assets_path}/{img_filename}")
            full_path.write_bytes(img_bytes)
            generated_count += 1
            logger.info(f"✅ Saved AI image: {img_filename}")

            # Standard Markdown renders safely in the UI and remains portable in exports.
            alt_str = img.get("alt", "Blog Image").strip()
            alt_str = alt_str.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
            caption_str = img.get("caption", "").strip()
            caption_markdown = (
                f"\n\n*{caption_str}*"
                if caption_str else ""
            )
            image_markdown = (
                f"\n\n![{alt_str}](assets/images/{img_filename})"
                f"{caption_markdown}\n\n"
            )

            # Insert image Markdown into updated_md.
            target = img.get("target_paragraph", "").strip()
            inserted = False
            if target and len(target) > 5 and target in updated_md:
                pos = updated_md.find(target)
                end_p = updated_md.find("\n\n", pos)
                if end_p != -1:
                    updated_md = updated_md[:end_p] + image_markdown + updated_md[end_p:]
                    inserted = True
                else:
                    updated_md += image_markdown
                    inserted = True

            if not inserted:
                if idx == 0:
                    # Hero image placement: insert right after H1 title line
                    first_nl = updated_md.find("\n\n")
                    if first_nl != -1:
                        updated_md = updated_md[:first_nl] + image_markdown + updated_md[first_nl:]
                    else:
                        updated_md += image_markdown
                else:
                    updated_md += image_markdown
        else:
            logger.error(f"❌ Failed image generation for spec: {img.get('filename')}")

    _emit(_job(state), "images", "completed", f"Generated {generated_count}/{len(image_specs)} images")

    if updated_md != merged_md:
        return {"merged_md": updated_md, "final": updated_md}
    return {}
