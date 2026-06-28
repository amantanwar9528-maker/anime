"""Stage 1 — write the Short.

Uses the FREE Gemini text model to produce an emotional anime mini-story:
  - a title + description + tags (for YouTube)
  - N scenes, each with:
       caption     -> one short line shown on screen for that scene
       image_prompt-> a Makoto-Shinkai-style prompt for that exact moment

Every image_prompt is automatically wrapped with the shared style + character
description from config, so all images look like one consistent film.

If the API key is missing or the call is rate-limited, a built-in fallback story
is used so the pipeline still produces a complete video.
"""
from __future__ import annotations
import json
import random
import re
from ..utils.logging_setup import get_logger

log = get_logger("script")

THEMES = [
    "a boy waiting at a train station for someone who will never come back",
    "a boy revisiting his old school on the last day before it is demolished",
    "a boy and a fading summer, the friend who moved away",
    "a boy who keeps a promise to watch the first snow every year alone",
    "a boy reading the last letter from someone he loved",
    "a boy walking home in the rain remembering a lost friend",
    "a boy on a rooftop at sunset, letting go of a childhood dream",
    "a boy returning to a seaside town that no longer remembers him",
]


def _wrap_prompt(scene_prompt: str, cfg) -> str:
    style = " ".join(cfg.get("image.style_suffix", "").split())
    character = " ".join(cfg.get("image.character", "").split())
    return f"{scene_prompt.strip()} Character: {character} {style}"


def _fallback_story(cfg, n: int) -> dict:
    theme = random.choice(THEMES)
    captions = [
        "He came back when the rain did.",
        "The platform still smelled of that summer.",
        "Every bench held a memory he couldn't sit on.",
        "He waited, the way he always had.",
        "The sky cried so he wouldn't have to.",
        "Somewhere, a train was leaving without her.",
        "He whispered a name the wind already knew.",
        "Maybe goodbye was just a longer hello.",
        "He smiled. The rain finally stopped.",
        "Some people stay, even after they go.",
    ]
    scene_actions = [
        "wide shot of an empty rural train platform at dusk, distant city lights",
        "close up of the boy's face looking down the empty tracks, soft tears",
        "the boy sitting alone on a wet wooden bench, reflection in a puddle",
        "low angle of the boy standing, holding an old paper ticket in the rain",
        "dramatic sky breaking open with golden light over the rooftops",
        "a single train disappearing into the distance, glowing windows",
        "the boy closing his eyes, wind moving his black messy hair",
        "the boy looking up at the clearing sky, faint rainbow",
        "the boy walking away down the platform, calm and at peace",
        "wide cinematic shot of the town at golden hour, the boy small in frame",
    ]
    scenes = []
    for i in range(n):
        scenes.append({
            "caption": captions[i % len(captions)],
            "image_prompt": _wrap_prompt(scene_actions[i % len(scene_actions)], cfg),
        })
    return {
        "title": "He Came Back When The Rain Did \U0001F327️ #shorts",
        "description": ("A quiet anime story about waiting, memory, and letting go.\n\n"
                        + " ".join(cfg.get("channel.hashtags", []))),
        "tags": ["anime", "shorts", "makoto shinkai", "sad anime", "aesthetic",
                 "emotional", "rain", "lofi"],
        "scenes": scenes,
        "theme": theme,
        "fallback": True,
    }


def _extract_json(text: str):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def make_script(cfg) -> dict:
    n = int(cfg.get("content.scenes", 9))
    api_key = cfg.secret(cfg.get("keys.gemini_env", "GEMINI_API_KEY"))
    if not api_key:
        log.warning("No GEMINI_API_KEY -> using built-in fallback story.")
        return _fallback_story(cfg, n)

    lang = cfg.get("channel.language", "en")
    lang_word = {"en": "English", "hi": "Hindi",
                 "hinglish": "Hinglish (Roman script)"}.get(lang, "English")

    sys_prompt = f"""You are a writer of viral, emotional anime YouTube Shorts in the
style of Makoto Shinkai films. Write ONE original {n}-scene mini-story.

Rules:
- Captions in {lang_word}. Each caption is ONE short poetic line (max 9 words),
  the kind that makes viewers feel something and stay till the end.
- The arc must build emotion: setup -> longing -> climax -> bittersweet release.
- The recurring character is: {cfg.get('image.character')}
- For each scene give an image_prompt describing only the VISUAL of that moment
  (setting, weather, camera angle, emotion). Do NOT include style words; they
  are added automatically.
- Make the final caption land like a punch or a soft exhale.

Return ONLY valid JSON, no markdown, shaped exactly like:
{{
  "title": "<catchy YouTube title with one emoji, under 90 chars>",
  "description": "<2 sentence description>",
  "tags": ["...", "..."],
  "scenes": [
    {{"caption": "<line>", "image_prompt": "<visual only>"}}
  ]
}}
Exactly {n} scenes."""

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        text_model = cfg.get("content.text_model", "gemini-2.5-flash")
        resp = client.models.generate_content(model=text_model, contents=sys_prompt)
        data = _extract_json(resp.text)
        if not data or "scenes" not in data:
            raise ValueError("model did not return usable JSON")
        for s in data["scenes"]:
            s["image_prompt"] = _wrap_prompt(s.get("image_prompt", ""), cfg)
        data["scenes"] = data["scenes"][:n]
        hooks = cfg.get("channel.hashtags", [])
        if "#shorts" not in data.get("title", "").lower():
            data["title"] = (data.get("title", "Anime Story")[:84] + " #shorts")
        data["description"] = (data.get("description", "") + "\n\n" + " ".join(hooks)).strip()
        data.setdefault("tags", ["anime", "shorts", "makoto shinkai", "emotional"])
        data["fallback"] = False
        log.info("Gemini wrote story: %s (%d scenes)", data["title"], len(data["scenes"]))
        return data
    except Exception as ex:
        log.error("Gemini script failed (%s) -> fallback story.", ex)
        return _fallback_story(cfg, n)
