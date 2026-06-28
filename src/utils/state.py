"""Persistent state that survives across cloud runs (committed back to the repo).

Tracks:
  * run_counter      -> how many Shorts made ever (used to vary image seeds)
  * music_index      -> next song to use (sequential, resumes across days)
  * used_signatures  -> fingerprints of past stories so none ever repeats

Stored as data/state/state.json. The GitHub workflow commits this file back
after each run, so the next run (even tomorrow) continues where this left off.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = ROOT / "data" / "state" / "state.json"

_DEFAULT = {"run_counter": 0, "music_index": 0, "used_signatures": []}


def load() -> dict:
    try:
        d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        for k, v in _DEFAULT.items():
            d.setdefault(k, v)
        return d
    except Exception:
        return dict(_DEFAULT)


def save(d: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def signature(scenes: list) -> str:
    """A stable fingerprint of a story from its captions."""
    text = "|".join((s.get("caption", "") or "").strip().lower() for s in scenes)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def is_used(d: dict, sig: str) -> bool:
    return sig in d.get("used_signatures", [])


def mark_used(d: dict, sig: str, keep: int = 500):
    used = d.setdefault("used_signatures", [])
    if sig not in used:
        used.append(sig)
    # keep only the most recent N to stop the file growing forever
    if len(used) > keep:
        d["used_signatures"] = used[-keep:]
