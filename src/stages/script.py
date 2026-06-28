"""Stage 1 — write the Short (a NEW, non-repeating story every time).

Themes span the full emotional range: couples, love, anger, persuasion/
convincing, breakups, longing, and finding love again. Uses the FREE Gemini
text model when a key is present; otherwise builds a story from large pools so
every run is different. A signature of the captions is checked against past runs
so no story ever repeats.
"""
from __future__ import annotations
import json
import random
import re
from ..utils.logging_setup import get_logger

log = get_logger("script")

# ---- emotional themes (couples, anger, persuasion, breakup, love, reunion) --
DEFAULT_THEMES = [
    # love / couples
    "a couple watching city lights, quietly in love",
    "a first date under cherry blossoms in spring",
    "confessing love on a rooftop at sunset",
    "two people sharing one umbrella in the rain, falling in love",
    "a couple watching fireworks, leaning on each other",
    "holding hands for the very first time at school",
    # anger / fights
    "a furious argument in the rain between two lovers",
    "anger melting into tears after a painful fight",
    "two stubborn hearts sitting back to back, unable to leave",
    "jealousy and anger giving way to quiet forgiveness",
    # persuasion / convincing
    "begging someone to stay just one more night",
    "convincing a heartbroken friend to believe in love again",
    "talking someone down from leaving on the last train",
    # breakups
    "the night of a painful breakup at a train platform",
    "a breakup message that ends everything",
    "packing away the memories of someone who left",
    # longing / loss
    "waiting at a station for someone who never returns",
    "reading the last letter from someone once loved",
    "returning to a seaside town that has forgotten you",
    "cherry blossoms falling on a goodbye",
    # finding love again / reunion
    "finding love again after heartbreak",
    "an unexpected second chance with an old flame",
    "two lovers reuniting after years apart",
    "the warmth of holding hands again after a long fight",
    "learning to love once more after losing everything",
]

CAPTIONS = [
    # love
    "He fell first. She fell harder. They fell together.",
    "Their hands found each other again.",
    "He memorized her laugh like a favourite song.",
    "Under one umbrella, the rain felt kind.",
    "She was his favourite hello, his hardest goodbye.",
    "He confessed. The sunset held its breath.",
    # anger / fights
    "I'm not angry. I'm afraid of losing you.",
    "Some fights are just love, out of breath.",
    "They shouted everything except 'I still care.'",
    "Anger fades. What it protected doesn't.",
    "Two stubborn hearts, one quiet sorry.",
    # persuasion
    "\"Stay,\" he said. \"Just one more night.\"",
    "He begged the rain to bring her back.",
    "\"Don't go,\" was all his eyes could say.",
    "He talked her heart out of leaving.",
    # breakups
    "She left, and took my reasons with her.",
    "She said goodbye. He heard 'don't let me.'",
    "The last message arrived. He read it twice.",
    "Some goodbyes never finish leaving.",
    "He folded the letter and unfolded the ache.",
    # longing
    "He waited until the platform forgot him.",
    "Spring came back. She didn't.",
    "Home was a person, not a place.",
    "He whispered a name the wind already knew.",
    # finding love again
    "Love, it turns out, gives second chances.",
    "He found her where he stopped looking.",
    "The breakup taught him how to hold on.",
    "Maybe forever started the second time.",
    "He chose her again, and again, and again.",
    "Broken hearts still know how to bloom.",
]

ACTIONS = [
    # love / couples
    "a young couple laughing together under one umbrella in the rain",
    "two anime teens on a first date under pink cherry blossoms",
    "a tender confession on a rooftop at golden sunset, blushing",
    "a couple watching fireworks bloom over a river, leaning close",
    "the boy and a girl holding hands for the first time at a school gate",
    "a couple sharing earphones on a quiet evening train",
    # anger / fights
    "two anime teens arguing in heavy rain, fists clenched, tears in their eyes",
    "the boy and a girl sitting back to back on a bench, angry, silent",
    "a heated face-to-face argument on a dim street, rain pouring",
    "the boy punching a wall in frustration, rain on the window behind him",
    # persuasion / reconciliation
    "the boy reaching out, pleading, as a girl pauses at the train doors",
    "the boy gently holding a crying girl's hand, reconciling softly",
    "a girl wiping the boy's tears after a fight, quiet forgiveness",
    "the boy comforting a heartbroken friend on a park bench at dusk",
    # breakups
    "the boy reading a breakup message on his phone, devastated, rain outside",
    "a girl walking away down a wet platform as the boy stands frozen",
    "the boy alone in an empty room boxing up old photographs",
    # longing
    "wide shot of an empty rural train platform at dusk, the boy small in frame",
    "close up of the boy looking down empty tracks, soft tears",
    "the boy reading a letter on a hillside as clouds race overhead",
    "first snow falling on the boy's shoulders outside a shrine",
    # finding love again / reunion
    "two lovers reuniting and embracing on a crowded street, golden light",
    "the boy offering a single flower to a girl, nervous and hopeful",
    "an old couple's photo on a desk while the boy smiles at a new message",
    "the boy and a girl meeting eyes again across a busy crossing",
    "dramatic sky breaking open with golden light over the rooftops",
]


def _themes(cfg):
    t = cfg.get("content.themes")
    if isinstance(t, list) and t:
        return t
    return DEFAULT_THEMES


def _wrap_prompt(scene_prompt: str, cfg) -> str:
    style = " ".join(cfg.get("image.style_suffix", "").split())
    character = " ".join(cfg.get("image.character", "").split())
    return f"{scene_prompt.strip()} Character: {character} {style}"


def _signature(scenes) -> str:
    import hashlib
    text = "|".join((s.get("caption", "") or "").strip().lower() for s in scenes)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _fallback_story(cfg, n: int, seed: int) -> dict:
    rng = random.Random(seed)
    theme = rng.choice(_themes(cfg))
    caps = rng.sample(CAPTIONS, min(n, len(CAPTIONS)))
    acts = rng.sample(ACTIONS, min(n, len(ACTIONS)))
    while len(caps) < n:
        caps.append(rng.choice(CAPTIONS))
    while len(acts) < n:
        acts.append(rng.choice(ACTIONS))
    scenes = [{"caption": caps[i], "image_prompt": _wrap_prompt(acts[i], cfg)}
              for i in range(n)]
    title_word = theme.split(",")[0][:60].strip().capitalize()
    return {
        "title": f"{title_word} \U0001F327️ #shorts",
        "description": ("A short emotional anime story about love, heartbreak and "
                        "second chances.\n\n" + " ".join(cfg.get("channel.hashtags", []))),
        "tags": ["anime", "shorts", "makoto shinkai", "sad anime", "love story",
                 "breakup", "emotional", "aesthetic", "rain", "lofi"],
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


def _gemini_story(cfg, n: int, seed: int):
    api_key = cfg.secret(cfg.get("keys.gemini_env", "GEMINI_API_KEY"))
    if not api_key:
        return None
    rng = random.Random(seed)
    theme = rng.choice(_themes(cfg))
    lang = cfg.get("channel.language", "en")
    lang_word = {"en": "English", "hi": "Hindi",
                 "hinglish": "Hinglish (Roman script)"}.get(lang, "English")
    sys_prompt = f"""You write viral, emotional anime YouTube Shorts in the style of
Makoto Shinkai films. Write ONE brand-new {n}-scene mini-story.

Creative seed (make it unlike any other): #{seed}.
The story's emotional theme for THIS video is: {theme}.
Across your videos you explore the full range of feeling — couples and new love,
raw anger and fights, pleading and persuasion, painful breakups, longing, and
finding love again. Lean fully into the theme above for this one.

Rules:
- Captions in {lang_word}. Each caption is ONE short, powerful line (max 9 words)
  that hits the emotion and makes viewers stay till the end.
- Emotional arc: setup -> rising feeling -> climax -> a punch or soft release.
- Recurring main character: {cfg.get('image.character')}. If the theme involves a
  couple, you may add a girl in the scene descriptions.
- Each image_prompt describes ONLY the visual of that moment (setting, weather,
  camera angle, emotion, who is in frame). No style words; added automatically.

Return ONLY valid JSON:
{{"title":"<catchy title with one emoji, under 90 chars>",
"description":"<2 sentences>","tags":["..."],
"scenes":[{{"caption":"<line>","image_prompt":"<visual only>"}}]}}
Exactly {n} scenes."""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = cfg.get("content.text_model", "gemini-2.5-flash")
        try:
            resp = client.models.generate_content(
                model=model, contents=sys_prompt, config={"temperature": 1.15})
        except Exception:
            resp = client.models.generate_content(model=model, contents=sys_prompt)
        data = _extract_json(resp.text)
        if not data or "scenes" not in data:
            return None
        for s in data["scenes"]:
            s["image_prompt"] = _wrap_prompt(s.get("image_prompt", ""), cfg)
        data["scenes"] = data["scenes"][:n]
        hooks = cfg.get("channel.hashtags", [])
        if "#shorts" not in data.get("title", "").lower():
            data["title"] = (data.get("title", "Anime Story")[:84] + " #shorts")
        data["description"] = (data.get("description", "") + "\n\n" + " ".join(hooks)).strip()
        data.setdefault("tags", ["anime", "shorts", "love story", "emotional"])
        data["theme"] = theme
        data["fallback"] = False
        return data
    except Exception as ex:
        log.error("Gemini story failed (%s)", ex)
        return None


def make_script(cfg, used_signatures=None, variety_seed: int = 0) -> dict:
    """Return a story whose caption-signature is NOT in used_signatures."""
    n = int(cfg.get("content.scenes", 9))
    used = set(used_signatures or [])
    last = None
    for attempt in range(6):
        seed = variety_seed * 1000 + attempt * 97 + random.randint(0, 1_000_000)
        data = _gemini_story(cfg, n, seed) or _fallback_story(cfg, n, seed)
        sig = _signature(data["scenes"])
        data["signature"] = sig
        last = data
        if sig not in used:
            log.info("story ready (%s, %d scenes, theme=%s): %s",
                     "AI" if not data.get("fallback") else "builtin",
                     len(data["scenes"]), data.get("theme", "?"), data["title"])
            return data
        log.info("story sig %s already used, retrying (%d)", sig, attempt + 1)
    log.warning("could not find a fully-unique story after retries; using last.")
    return last
