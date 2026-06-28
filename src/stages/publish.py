"""Stage 4 — upload the finished Short to YouTube via the official Data API v3.

Auth is OAuth (run scripts/setup_youtube_oauth.py ONCE locally to create the
token). In the cloud the token + client secret are injected from GitHub Secrets.
Uploading a video costs ~100 quota units; the free 10,000/day budget easily
covers 2 Shorts per day.
"""
from __future__ import annotations
from pathlib import Path
from ..utils.logging_setup import get_logger

log = get_logger("publish")
ROOT = Path(__file__).resolve().parent.parent.parent


def _yt_service(cfg):
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/youtube.upload",
              "https://www.googleapis.com/auth/youtube"]
    token_file = ROOT / cfg.get("keys.youtube_token_file", "secrets/yt_token.json")
    client_file = ROOT / cfg.get("keys.youtube_client_secret_file", "secrets/yt_client_secret.json")

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes)
            creds = flow.run_local_server(port=0)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def upload_youtube(video_path, script, cfg):
    if not cfg.get("publish.youtube.enabled", True):
        log.info("YouTube publishing disabled in config; skipping upload.")
        return None

    # Friendly pre-check: is the one-time YouTube authorization done?
    token_file = ROOT / cfg.get("keys.youtube_token_file", "secrets/yt_token.json")
    client_file = ROOT / cfg.get("keys.youtube_client_secret_file", "secrets/yt_client_secret.json")
    for f, what in [(client_file, "YT_CLIENT_SECRET_JSON"),
                    (token_file, "YT_TOKEN_JSON")]:
        if (not f.exists()) or len(f.read_text(encoding="utf-8").strip()) < 5:
            log.warning("YouTube not authorized yet: %s is missing/empty. "
                        "Complete Part B in SETUP_GUIDE.md (authorize once), then "
                        "add the GitHub secret '%s'. The video was still created "
                        "and saved as a build artifact.", f.name, what)
            return None

    try:
        from googleapiclient.http import MediaFileUpload
        yt = _yt_service(cfg)

        title = script.get("title", "Anime Short")
        if "#shorts" not in title.lower():
            title = (title[:88] + " #Shorts")
        desc = script.get("description", "")
        status = {
            "privacyStatus": cfg.get("publish.youtube.privacy", "public"),
            "selfDeclaredMadeForKids": cfg.get("publish.youtube.made_for_kids", False),
        }
        body = {
            "snippet": {
                "title": title[:100],
                "description": desc[:4900],
                "tags": script.get("tags", [])[:30],
                "categoryId": str(cfg.get("publish.youtube.category_id", "1")),
            },
            "status": status,
        }
        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True,
                                mimetype="video/mp4")
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        vid = resp["id"]
        log.info("YouTube uploaded: https://youtu.be/%s", vid)
        return vid
    except Exception as ex:
        log.error("YouTube upload failed: %s", ex)
        return None
