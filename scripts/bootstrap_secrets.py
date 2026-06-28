"""Rebuild secret FILES from GitHub Encrypted Secrets (env vars) at runtime.

GitHub keeps these encrypted and injects them only during the Action run; they
never touch the repo. This materializes the YouTube OAuth JSONs into secrets/.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEC = ROOT / "secrets"
SEC.mkdir(exist_ok=True)

MAP = {
    "YT_CLIENT_SECRET_JSON": "yt_client_secret.json",
    "YT_TOKEN_JSON": "yt_token.json",
}

for env_name, filename in MAP.items():
    val = os.environ.get(env_name)
    if val and val.strip():
        (SEC / filename).write_text(val, encoding="utf-8")
        print(f"restored secrets/{filename}")
    else:
        print(f"(skip) {env_name} not set")
print("bootstrap done")
