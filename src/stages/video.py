"""Stage 3 — the FREE "AI video" engine (pure FFmpeg, no paid services).

For each still image it creates a 5-second cinematic clip:
  * slow camera push-in / pull-out (alternating)  -> "zoom in and out a little"
  * animated falling rain overlay                 -> "rain falling naturally"
  * subtle vignette + warm color grade            -> "cinematic lighting"
  * a fade-in/out caption (the story line)
Then it crossfades all the clips together and lays a soft music bed under them,
producing a vertical 1080x1920 Short of ~45-55s.

All of this matches the reference look (slow push, gentle zoom, rain, cinematic
breathing) without any paid video-generation API.
"""
from __future__ import annotations
import os
import random
import shutil
import subprocess
import textwrap
from pathlib import Path
from ..utils.logging_setup import get_logger

log = get_logger("video")


def _run(cmd: list[str]):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        log.error("ffmpeg failed:\n%s", p.stderr[-1500:])
        raise RuntimeError("ffmpeg command failed")
    return p


def _font(cfg) -> str:
    f = cfg.path(cfg.get("video.caption.font", "assets/fonts/caption.ttf"))
    if Path(f).exists():
        return str(f)
    # fall back to a bundled-by-OS bold font
    for cand in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        if Path(cand).exists():
            return cand
    return "DejaVuSans-Bold"


def _ff(path: str) -> str:
    """Escape a path for use inside an ffmpeg filter (Windows drive colons etc.)."""
    return path.replace("\\", "/").replace(":", "\\:")


# --------------------------- rain overlay (generated) ------------------------
def _ensure_rain(cfg, cache: Path) -> Path:
    rain_mp4 = cache / "rain.mp4"
    if rain_mp4.exists():
        return rain_mp4
    from PIL import Image, ImageDraw, ImageFilter
    W = cfg.get("video.width", 1080)
    tex = cache / "rain_tex.png"
    img = Image.new("RGB", (W, 2160), (0, 0, 0))
    d = ImageDraw.Draw(img)
    random.seed(7)
    for _ in range(750):
        x = random.randint(0, W); y = random.randint(0, 2160)
        ln = random.randint(18, 42); g = random.randint(90, 185)
        d.line([(x, y), (x - 4, y + ln)], fill=(g, g, g), width=1)
    img.filter(ImageFilter.GaussianBlur(0.4)).save(tex)
    _run(["ffmpeg", "-y", "-loop", "1", "-i", str(tex), "-t", "6", "-r",
          str(cfg.get("video.fps", 30)), "-filter_complex",
          f"scale={W}:2160,scroll=vertical=0.012,crop={W}:{cfg.get('video.height',1920)}:0:0,format=yuv420p",
          "-an", str(rain_mp4)])
    return rain_mp4


# ------------------------------- one scene -----------------------------------
def _render_scene(cfg, img_path: Path, caption: str, idx: int,
                  rain: Path, out: Path):
    W = cfg.get("video.width", 1080); H = cfg.get("video.height", 1920)
    FPS = cfg.get("video.fps", 30)
    dur = float(cfg.get("content.seconds_per_scene", 5.0))
    frames = int(dur * FPS)
    zs = float(cfg.get("video.zoom_strength", 0.12))
    step = zs / frames
    if idx % 2 == 0:
        zexpr = f"min(zoom+{step:.6f},{1+zs:.4f})"           # push in
    else:
        zexpr = f"if(lte(zoom,1.0),{1+zs:.4f},max(zoom-{step:.6f},1.0))"  # pull out

    base = (f"[0:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
            f"crop={W*2}:{H*2},"
            f"zoompan=z='{zexpr}':d={frames}:x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},")
    if cfg.get("video.grade", True):
        base += "eq=contrast=1.06:saturation=1.12,"
    base += "setsar=1[base];"

    # rain
    rain_op = float(cfg.get("video.rain_opacity", 0.35)) if cfg.get("video.rain", True) else 0.0
    graph = base + f"[1:v]scale={W}:{H},setsar=1[rain];"
    graph += (f"[base][rain]blend=all_mode=screen:all_opacity={rain_op},"
              "format=yuv420p[mix];")

    # vignette + caption
    chain = "[mix]"
    if cfg.get("video.vignette", True):
        chain += "vignette=PI/5,"
    if cfg.get("video.caption.enabled", True) and caption.strip():
        cap_file = out.parent / f"cap_{idx:02d}.txt"
        wrapped = "\n".join(textwrap.wrap(caption.strip(), width=22)[:3])
        cap_file.write_text(wrapped, encoding="utf-8")
        fs = cfg.get("video.caption.size", 58)
        box = cfg.get("video.caption.box_opacity", 0.35)
        yr = cfg.get("video.caption.y_ratio", 0.72)
        fade = (f"if(lt(t,0.5),t/0.5,if(gt(t,{dur-0.5:.2f}),({dur:.2f}-t)/0.5,1))")
        chain += (f"drawtext=fontfile='{_ff(_font(cfg))}':textfile='{_ff(str(cap_file))}':"
                  f"fontcolor=white:fontsize={fs}:line_spacing=12:box=1:"
                  f"boxcolor=black@{box}:boxborderw=26:x=(w-text_w)/2:"
                  f"y=h*{yr}:alpha='{fade}',")
    chain = chain.rstrip(",") + "[outv]"
    graph += chain

    _run(["ffmpeg", "-y", "-i", str(img_path), "-i", str(rain),
          "-filter_complex", graph, "-map", "[outv]", "-t", f"{dur}",
          "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
          "-preset", "ultrafast", str(out)])


# ------------------------------- music bed -----------------------------------
def _music(cfg, cache: Path, duration: float) -> Path | None:
    if not cfg.get("video.music.enabled", True):
        return None
    out = cache / "music.m4a"
    folder = cfg.path(cfg.get("video.music.folder", "assets/music"))
    tracks = []
    if Path(folder).exists():
        tracks = [p for p in Path(folder).iterdir()
                  if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".ogg")]
    vol = cfg.get("video.music.volume", 0.7)
    if tracks:
        t = random.choice(tracks)
        log.info("music: %s", t.name)
        _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(t), "-t", f"{duration}",
              "-filter:a", f"volume={vol},afade=t=in:st=0:d=1.5,"
              f"afade=t=out:st={max(0,duration-2):.2f}:d=2",
              "-c:a", "aac", str(out)])
        return out
    # no track provided -> synthesize a soft ambient pad (royalty-free, generated)
    log.info("no music files found -> generating ambient bed")
    _run(["ffmpeg", "-y",
          "-f", "lavfi", "-i", f"sine=frequency=196:duration={duration}",
          "-f", "lavfi", "-i", f"sine=frequency=294:duration={duration}",
          "-filter_complex",
          f"[0:a]volume=0.5[a0];[1:a]volume=0.35[a1];[a0][a1]amix=inputs=2,"
          f"tremolo=f=0.15:d=0.6,lowpass=f=900,volume={vol},"
          f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(0,duration-2):.2f}:d=2[am]",
          "-map", "[am]", "-c:a", "aac", str(out)])
    return out


# --------------------------------- main --------------------------------------
def make_video(cfg, script: dict, images: list[Path], outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    cache = outdir / "_work"; cache.mkdir(exist_ok=True)
    rain = _ensure_rain(cfg, cache)

    dur = float(cfg.get("content.seconds_per_scene", 5.0))
    T = float(cfg.get("content.transition_seconds", 0.6))

    clips: list[Path] = []
    for i, img in enumerate(images):
        cap = script["scenes"][i].get("caption", "") if i < len(script["scenes"]) else ""
        clip = cache / f"clip_{i:02d}.mp4"
        _render_scene(cfg, img, cap, i, rain, clip)
        clips.append(clip)
        log.info("scene %d/%d rendered", i + 1, len(images))

    # crossfade chain
    silent = cache / "silent.mp4"
    if len(clips) == 1:
        shutil.copy(clips[0], silent)
        total = dur
    else:
        inputs = []
        for c in clips:
            inputs += ["-i", str(c)]
        fc = ""
        prev = "[0:v]"
        for k in range(1, len(clips)):
            off = k * (dur - T)
            label = "[v]" if k == len(clips) - 1 else f"[x{k}]"
            fc += (f"{prev}[{k}:v]xfade=transition=fade:duration={T}:"
                   f"offset={off:.3f}{label};")
            prev = f"[x{k}]"
        fc = fc.rstrip(";")
        if not fc.endswith("[v]"):
            fc += ",format=yuv420p[v]"
        else:
            fc = fc[:-3] + ",format=yuv420p[v]"
        _run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]",
              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
              str(silent)])
        total = len(clips) * dur - (len(clips) - 1) * T

    music = _music(cfg, cache, total)
    final = outdir / "short.mp4"
    if music:
        _run(["ffmpeg", "-y", "-i", str(silent), "-i", str(music),
              "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
              "-shortest", str(final)])
    else:
        shutil.copy(silent, final)
    log.info("FINAL Short: %s (%.1fs)", final, total)
    return final
