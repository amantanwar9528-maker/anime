"""Stage 2 — generate one image per scene.

IMPORTANT (2026): Google shut down FREE Gemini image generation. So the default
backend here is **Pollinations** — a free image service that needs NO account and
NO API key. You request a URL and it returns an anime image (Flux model).

Backends (config -> image.backend):
  * "pollinations"  free, no key  (DEFAULT, recommended)
  * "gemini"        only if you have a PAID Gemini image plan (Nano Banana)

If a backend fails for a scene, a soft gradient placeholder is used so the video
still renders. The recurring character description is baked into every prompt by
the script stage, which keeps the look consistent across scenes.
"""
from __future__ import annotations
import time
import urllib.parse
from pathlib import Path
from ..utils.logging_setup import get_logger

log = get_logger("images")

BASE_SEED = 4242   # fixed base so runs are reproducible; +i per scene for variety


# --------------------------- Pollinations (free) -----------------------------
def _pollinations(prompt: str, w: int, h: int, seed: int, model: str):
    import requests
    q = urllib.parse.quote(prompt[:1800], safe="")
    url = (f"https://image.pollinations.ai/prompt/{q}"
           f"?width={w}&height={h}&model={model}&seed={seed}"
           f"&nologo=true&enhance=true&private=true")
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=180, headers={"User-Agent": "Mozilla/5.0"})
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ct.startswith("image") and len(r.content) > 5000:
                return r.content
            log.warning("pollinations attempt %d: status=%s type=%s size=%d",
                        attempt + 1, r.status_code, ct, len(r.content))
        except Exception as ex:
            log.warning("pollinations attempt %d error: %s", attempt + 1, ex)
        time.sleep(4 * (attempt + 1))
    return None


# --------------------------- Gemini (paid plans) -----------------------------
def _gemini_image(prompt: str, api_key: str, model_name: str):
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model_name, contents=prompt)
        for cand in resp.candidates:
            for part in cand.content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    return inline.data
        log.warning("Gemini returned no image part.")
    except Exception as ex:
        log.error("Gemini image call failed: %s", ex)
    return None


# --------------------------- placeholder fallback ----------------------------
def _placeholder(path: Path, idx: int, w: int, h: int):
    from PIL import Image, ImageDraw, ImageFilter
    palettes = [
        ((255, 183, 130), (120, 90, 170), (40, 40, 80)),
        ((130, 200, 255), (90, 130, 220), (30, 50, 110)),
        ((255, 150, 160), (150, 110, 190), (50, 40, 90)),
        ((180, 220, 200), (90, 140, 160), (30, 60, 80)),
    ]
    top, mid, bot = palettes[idx % len(palettes)]
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / h
        if t < 0.5:
            f = t / 0.5
            c = tuple(int(top[i] + (mid[i] - top[i]) * f) for i in range(3))
        else:
            f = (t - 0.5) / 0.5
            c = tuple(int(mid[i] + (bot[i] - mid[i]) * f) for i in range(3))
        col.putpixel((0, y), c)
    img = col.resize((w, h))
    d = ImageDraw.Draw(img)
    r = int(w * 0.16)
    d.ellipse([int(w*0.3)-r, int(h*0.3)-r, int(w*0.3)+r, int(h*0.3)+r], fill=(255, 245, 220))
    hz = int(h * 0.74)
    d.rectangle([0, hz, w, h], fill=(20, 22, 35))
    fx, fy, fh = int(w*0.5), hz, int(h*0.20)
    d.ellipse([fx-fh*0.12, fy-fh, fx+fh*0.12, fy-fh*0.78], fill=(10, 10, 18))
    d.polygon([(fx-fh*0.16, fy-fh*0.78), (fx+fh*0.16, fy-fh*0.78),
               (fx+fh*0.20, fy), (fx-fh*0.20, fy)], fill=(10, 10, 18))
    img.filter(ImageFilter.GaussianBlur(2)).save(path, "PNG")


# --------------------------------- main --------------------------------------
def make_images(cfg, script: dict, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    backend = cfg.get("image.backend", "pollinations")
    w, h = cfg.get("video.width", 1080), cfg.get("video.height", 1920)
    api_key = cfg.secret(cfg.get("keys.gemini_env", "GEMINI_API_KEY"))
    gem_model = cfg.get("image.gemini_model", "gemini-2.5-flash-image")
    poll_model = cfg.get("image.pollinations_model", "flux")

    paths = []
    for i, scene in enumerate(script["scenes"]):
        dest = outdir / f"scene_{i:02d}.png"
        prompt = scene["image_prompt"]
        data = None
        if backend == "gemini" and api_key:
            data = _gemini_image(prompt, api_key, gem_model)
        else:
            data = _pollinations(prompt, w, h, BASE_SEED + i, poll_model)
            if not data and api_key:
                data = _gemini_image(prompt, api_key, gem_model)
        if data:
            dest.write_bytes(data)
            log.info("scene %d image OK via %s (%d bytes)", i, backend, len(data))
        else:
            _placeholder(dest, i, w, h)
            log.info("scene %d placeholder (image backend unavailable)", i)
        paths.append(dest)
    return paths
