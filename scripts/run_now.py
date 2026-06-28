"""Make one Short right now WITHOUT uploading (for local testing / preview).
Run:  python scripts/run_now.py
The finished file is data/output/<timestamp>/short.mp4
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import run_once

if __name__ == "__main__":
    res = run_once(upload=False)
    print("\nFinished:", res["video"])
