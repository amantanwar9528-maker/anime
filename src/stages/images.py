"""Stage 2 — generate one image per scene with Gemini's FREE image model.

Free tier (no credit card) gives ~500 images/day, far more than the 18-20 a
day this bot needs for 2 Shorts. If the key/model is unavailable, a tasteful
gradient-sky placeholder is generated so the rest of the pipeline still runs
and you can see the motion/rain/captions working end to end.
"""
from __future__ import annotations
import math
import random
from pathlib import Path
from ..utils.logging_setup import get_logger

log = get_logger("images")


# --------------------------- Gemini image call -------------------------------
def _gemini_image(prompt: str, api_key: str, model_name: str) -> bytes | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(
            prompt,
            generation_config={"response_modalities": ["TEXT", "IMAGE"]},
        )
        for cand in resp.candidates:
            for part in cand.content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    return inline.data
        log.warning("Gemini returned no image part for a scene.")
        return None
    except Exception as ex:
        log.error("Gemini image call failed: %s", ex)
        return None


# --------------------------- placeholder fallback ----------------------------
def _placeholder(path: Path, idx: int, w: int, h: int):
    """A soft anime-ish vertical gradient sky + horizon + silhouette.
    Only used when no real image is available (e.g. no API key during testing)."""
    from PIL import Image, ImageDraw, ImageFilter

    palettes = [
        ((255, 183, 130), (120, 90, 170), (40, 40, 80)),   # sunset
        ((130, 200, 255), (90, 130, 220), (30, 50, 110)),  # blue hour
        ((255, 150, 160), (150, 110, 190), (50, 40, 90)),  # rose dusk
        ((180, 220, 200), (90, 140, 160), (30, 60, 80)),   # teal calm
    ]
    top, mid, bot = palettes[idx % len(palettes)]
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / h
        if t < 0.5:
            f = t / 0.5
            c = tuple(int(top[i] + (mid[i] - top[i]) * f) for i in range(3))
        else:
            f = (t - 0.5) / 0.5
            c = tuple(int(mid[i] + (bot[i] - mid[i]) * f) for i in range(3))
        for x in range(w):
            px[x, y] = c
    d = ImageDraw.Draw(img)
    # a soft sun/moon
    r = int(w * 0.16)
    cx, cy = int(w * (0.3 + 0.4 * random.random())), int(h * 0.3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 245, 220))
    # horizon ground
    horizon = int(h * 0.74)
    d.rectangle([0, horizon, w, h], fill=(20, 22, 35))
    # a simple standing figure silhouette (the recurring boy)
    fx, fy = int(w * 0.5), horizon
    fh = int(h * 0.20)
    d.ellipse([fx - fh * 0.12, fy - fh, fx + fh * 0.12, fy - fh * 0.78],
              fill=(10, 10, 18))                      # head
    d.polygon([(fx - fh * 0.16, fy - fh * 0.78), (fx + fh * 0.16, fy - fh * 0.78),
               (fx + fh * 0.20, fy), (fx - fh * 0.20, fy)], fill=(10, 10, 18))  # body
    img = img.filter(ImageFilter.GaussianBlur(2))
    img.save(path, "PNG")


# --------------------------------- main --------------------------------------
def make_images(cfg, script: dict, outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    api_key = cfg.secret(cfg.get("keys.gemini_env", "GEMINI_API_KEY"))
    model_name = cfg.get("image.model", "gemini-2.0-flash-preview-image-generation")
    w, h = cfg.get("video.width", 1080), cfg.get("video.height", 1920)

    paths: list[Path] = []
    for i, scene in enumerate(script["scenes"]):
        dest = outdir / f"scene_{i:02d}.png"
        data = None
        if api_key:
            data = _gemini_image(scene["image_prompt"], api_key, model_name)
        if data:
            dest.write_bytes(data)
            # normalise to PNG / size handled later by ffmpeg
            log.info("scene %d image OK (%d bytes)", i, len(data))
        else:
            _placeholder(dest, i, w, h)
            log.info("scene %d placeholder image", i)
        paths.append(dest)
    return paths
