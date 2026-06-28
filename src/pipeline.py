"""End-to-end pipeline for ONE Short:
   script -> images -> video -> (optional) YouTube upload.
Each run creates a timestamped folder under data/output/ holding everything.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from .config import Config
from .utils.logging_setup import get_logger
from .stages import script as script_stage
from .stages import images as images_stage
from .stages import video as video_stage
from .stages import publish as publish_stage

log = get_logger("pipeline")


def run_once(upload: bool = True) -> dict:
    cfg = Config()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = cfg.path(cfg.get("paths.output", "data/output"), stamp)
    outdir.mkdir(parents=True, exist_ok=True)
    log.info("=== NEW SHORT -> %s ===", outdir)

    # 1) script
    script = script_stage.make_script(cfg)
    (outdir / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2),
                                        encoding="utf-8")

    # 2) images
    imgs = images_stage.make_images(cfg, script, outdir / "images")

    # 3) video
    video = video_stage.make_video(cfg, script, imgs, outdir)

    # 4) upload
    video_id = None
    if upload:
        video_id = publish_stage.upload_youtube(video, script, cfg)

    result = {
        "title": script.get("title"),
        "scenes": len(script.get("scenes", [])),
        "video": str(video),
        "youtube_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}" if video_id else None,
        "used_fallback_story": script.get("fallback", False),
    }
    (outdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    log.info("=== DONE: %s ===", result.get("youtube_url") or video)
    return result
