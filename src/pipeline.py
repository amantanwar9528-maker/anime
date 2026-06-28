"""End-to-end pipeline for ONE Short:
   pick music (sequential) -> write a NEW story -> images -> video -> upload.
State (run counter, music index, used stories) persists across runs so nothing
repeats and music continues in order even the next day.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from .config import Config
from .utils.logging_setup import get_logger
from .utils import state as st
from .stages import script as script_stage
from .stages import images as images_stage
from .stages import video as video_stage
from .stages import publish as publish_stage

log = get_logger("pipeline")

AUDIO_EXT = (".mp3", ".m4a", ".wav", ".ogg")


def _next_music(cfg, state) -> tuple:
    """Return (track_path or None, new_index). Plays the folder in order, looping,
    and resumes from where the last run stopped."""
    folder = cfg.path(cfg.get("video.music.folder", "assets/music"))
    tracks = sorted([p for p in Path(folder).iterdir() if p.suffix.lower() in AUDIO_EXT],
                    key=lambda p: p.name.lower()) if Path(folder).exists() else []
    if not tracks:
        log.info("no music files in %s -> will use generated ambient bed", folder)
        return None, state.get("music_index", 0)
    idx = state.get("music_index", 0)
    track = tracks[idx % len(tracks)]
    log.info("music %d/%d (sequential): %s", (idx % len(tracks)) + 1, len(tracks), track.name)
    return track, idx + 1


def run_once(upload: bool = True) -> dict:
    cfg = Config()
    state = st.load()
    run_no = state.get("run_counter", 0)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = cfg.path(cfg.get("paths.output", "data/output"), stamp)
    outdir.mkdir(parents=True, exist_ok=True)
    log.info("=== NEW SHORT #%d -> %s ===", run_no + 1, outdir)

    # music first (so we know which song this video uses)
    track, next_idx = _next_music(cfg, state)

    # 1) a NEW, non-repeating story
    script = script_stage.make_script(
        cfg, used_signatures=state.get("used_signatures", []), variety_seed=run_no)
    (outdir / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2),
                                        encoding="utf-8")

    # 2) images — per-run seed base so every video looks different
    seed_base = 1000 + run_no * 50
    imgs = images_stage.make_images(cfg, script, outdir / "images", seed_base=seed_base)

    # 3) video with this run's sequential song
    video = video_stage.make_video(cfg, script, imgs, outdir, music_file=track)

    # 4) upload
    video_id = None
    if upload:
        video_id = publish_stage.upload_youtube(video, script, cfg)

    # 5) advance + persist state (only now, so a crash doesn't skip a song/seed)
    state["run_counter"] = run_no + 1
    state["music_index"] = next_idx
    st.mark_used(state, script.get("signature", st.signature(script["scenes"])))
    st.save(state)

    result = {
        "short_number": run_no + 1,
        "title": script.get("title"),
        "scenes": len(script.get("scenes", [])),
        "music": track.name if track else "generated ambient",
        "signature": script.get("signature"),
        "video": str(video),
        "youtube_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}" if video_id else None,
        "used_builtin_story": script.get("fallback", False),
    }
    (outdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    log.info("=== DONE #%d: %s | music=%s ===",
             run_no + 1, result.get("youtube_url") or video, result["music"])
    return result
