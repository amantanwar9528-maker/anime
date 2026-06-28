"""Entry point. Makes and uploads ONE Short.

Usage:
    python -m src.main             # make + upload one Short
    python -m src.main --no-upload # make only (great for first local test)
"""
import sys
from .pipeline import run_once

if __name__ == "__main__":
    upload = "--no-upload" not in sys.argv
    run_once(upload=upload)
