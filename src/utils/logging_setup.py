"""Tiny logging helper: prints to console AND appends to data/logs/<date>.log."""
import logging
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    global _CONFIGURED
    if not _CONFIGURED:
        logdir = ROOT / "data" / "logs"
        logdir.mkdir(parents=True, exist_ok=True)
        handlers = [
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logdir / f"{date.today().isoformat()}.log", encoding="utf-8"),
        ]
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
            handlers=handlers,
        )
        _CONFIGURED = True
    return logging.getLogger(name)
