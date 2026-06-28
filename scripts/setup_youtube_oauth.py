"""Run this ONCE on your own computer to authorize YouTube uploads.

Steps (full screen-reader-friendly walkthrough is in SETUP_GUIDE.md):
  1. In Google Cloud Console: create an OAuth client (type: Desktop app) and
     enable "YouTube Data API v3".
  2. Download the client secret JSON and save it as:
         secrets/yt_client_secret.json
  3. Run:   python scripts/setup_youtube_oauth.py
     A browser opens; sign in with the Google account that owns your YouTube
     channel and approve. A token is written to secrets/yt_token.json.
  4. Paste the contents of those two files into GitHub Secrets
     (YT_CLIENT_SECRET_JSON and YT_TOKEN_JSON) so the cloud can upload for you.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import Config
from src.stages.publish import _yt_service

if __name__ == "__main__":
    yt = _yt_service(Config())
    me = yt.channels().list(part="snippet", mine=True).execute()
    print("Authorized channel:", me["items"][0]["snippet"]["title"])
    print("Token saved to secrets/yt_token.json. You're ready to upload.")
