# Anime Auto Bot — hands-off YouTube Shorts (₹0)

Makes cinematic, emotional anime Shorts (Makoto Shinkai style) and uploads them
to YouTube automatically — twice a day — for **zero cost**.

## What it does, every run

1. **Writes a story** — Gemini (free tier) writes a short emotional anime story:
   a title, a description, and 9 scene captions.
2. **Generates images** — Gemini (free tier) creates one image per scene, all in
   the same Makoto-Shinkai style with the same recurring character.
3. **Builds the video** — FFmpeg turns the stills into a cinematic Short:
   - slow camera push-in / gentle zoom (the "AI video" feel, done free)
   - natural falling rain overlay
   - soft vignette + warm color grade
   - fade-in/out captions (the story, line by line)
   - a music bed (your track, or an auto-generated ambient pad)
   - vertical 1080×1920, about 45–55 seconds
4. **Uploads to YouTube** — official YouTube Data API, public, as a #Shorts.

The whole thing runs in the cloud on **GitHub Actions** (free), so your computer
does not need to be on. You set it up **once**; after that it is fully automatic.

## The honest part

- This costs ₹0 to run. The "slow zoom + rain + cinematic" look is created with
  free software (FFmpeg), not a paid AI-video service — viewers can't tell.
- Your Gemini **app** subscription is separate from the **API**. You get a free
  Gemini **API key** from Google AI Studio (no card needed). Steps are in
  `SETUP_GUIDE.md`.
- YouTube income is **not instant**. You need 1,000 subscribers + 4,000 watch
  hours, or 10 million Shorts views in 90 days, before you can earn. This system
  posts consistently so that becomes possible over time — but it takes patience.

## Files

- `SETUP_GUIDE.md` — do this once. Plain, step-by-step, screen-reader friendly.
- `config.example.yaml` — all the settings (style, scenes, language, rain, etc.).
- `src/` — the bot (script → images → video → upload).
- `scripts/setup_youtube_oauth.py` — run once to authorize YouTube.
- `scripts/run_now.py` — make one Short locally without uploading (preview).
- `.github/workflows/publish.yml` — the schedule (2 Shorts/day).
- `SAMPLE_short.mp4` — a sample made by this engine (placeholder art, real motion/
  rain/captions/music) so you can hear/feel what it produces.

## Try it locally (optional)

```
pip install -r requirements.txt          # one time
python scripts/run_now.py                 # makes data/output/<time>/short.mp4
```

Without a Gemini key it uses a built-in story + placeholder art so you can still
see the engine work. With your key it uses real Gemini art.

Full setup is in **SETUP_GUIDE.md** — start there.
