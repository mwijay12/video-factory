# -*- coding: utf-8 -*-
"""
src/utils/voice_catalog.py — VideoFactory Voice Catalog

Provides a unified catalog of all available TTS voices across every provider.
Results are cached in memory for 6 hours. No API credits consumed for catalog
listing (only Edge TTS list is fetched — it's free).

Usage:
    from src.utils.voice_catalog import get_all_voices, preview_voice
"""

import asyncio
import time
import uuid
import tempfile
from pathlib import Path
from typing import Optional

_CACHE_TTL_SEC = 6 * 3600   # 6 hours
_voice_cache: dict = {"ts": 0, "voices": []}

# Preview files stored here (cleaned up after 1 hour)
PREVIEW_DIR = Path("output/previews")


# ─── Voice Catalog ────────────────────────────────────────────────────────────

async def get_all_voices(force_refresh: bool = False) -> list[dict]:
    """
    Returns a list of all available voices across all providers.
    Results are cached for 6 hours.

    Each voice dict has:
        provider (str): edge-tts | puter | elevenlabs | direct-gemini
        voice_id (str): the voice identifier to pass to the TTS engine
        display_name (str): human-readable name
        language (str): BCP-47 code e.g. "sw-TZ", "en-US"
        lang_code (str): 2-letter code e.g. "sw", "en"
        gender (str): Female | Male | Neutral
        is_free (bool): True if no API key / credits required
    """
    now = time.time()
    if not force_refresh and (now - _voice_cache["ts"]) < _CACHE_TTL_SEC and _voice_cache["voices"]:
        return _voice_cache["voices"]

    voices: list[dict] = []

    # 1. Edge TTS voices (free, live fetch)
    edge_voices = await _fetch_edge_voices()
    voices.extend(edge_voices)

    # 2. Direct Gemini voices (static list, no API call needed)
    voices.extend(_gemini_static_voices())

    # 3. Puter voices (static list, no API call)
    voices.extend(_puter_static_voices())

    # 4. ElevenLabs popular voices (static, no API call for list)
    voices.extend(_elevenlabs_static_voices())

    _voice_cache["ts"] = time.time()
    _voice_cache["voices"] = voices
    return voices


async def _fetch_edge_voices() -> list[dict]:
    """Fetches live Edge TTS voice list (free, always available)."""
    try:
        import edge_tts
        raw = await edge_tts.list_voices()
        result = []
        for v in raw:
            short_name = v.get("ShortName", "")
            # Filter out robotic Swahili voices requested by user
            if short_name in ["sw-TZ-RehemaNeural", "sw-TZ-DaudiNeural", "sw-TZ-Daudi"]:
                continue
            locale = v.get("Locale", "")
            lang_code = locale.split("-")[0].lower() if locale else "?"
            result.append({
                "provider":     "edge-tts",
                "voice_id":     short_name,
                "display_name": v.get("FriendlyName", short_name),
                "language":     locale,
                "lang_code":    lang_code,
                "gender":       v.get("Gender", "Neutral"),
                "is_free":      True,
                "quality":      "Neural",
            })
        return result
    except Exception as e:
        print(f"  [VoiceCatalog] Edge TTS list failed: {e}")
        return _edge_swahili_fallback()


def _edge_swahili_fallback() -> list[dict]:
    """Hardcoded Swahili + common English Edge voices in case of network error."""
    VOICES = [
        ("sw-KE-RafikiNeural", "Rafiki (Kenya, Male)",     "sw-KE", "sw", "Male"),
        ("sw-KE-ZuriNeural",   "Zuri (Kenya, Female)",     "sw-KE", "sw", "Female"),
        ("en-US-AriaNeural",   "Aria (US, Female)",        "en-US", "en", "Female"),
        ("en-US-GuyNeural",    "Guy (US, Male)",           "en-US", "en", "Male"),
        ("en-US-JennyNeural",  "Jenny (US, Female)",       "en-US", "en", "Female"),
        ("en-GB-SoniaNeural",  "Sonia (GB, Female)",       "en-GB", "en", "Female"),
    ]
    return [{
        "provider": "edge-tts", "voice_id": vid, "display_name": name,
        "language": lang, "lang_code": lc, "gender": gender,
        "is_free": True, "quality": "Neural"
    } for vid, name, lang, lc, gender in VOICES]


def _gemini_static_voices() -> list[dict]:
    """Gemini TTS voices (multilingual direct API, supports Swahili & English)."""
    VOICES = [
        ("Aoede",   "Aoede — Melodic & Expressive (Recommended)", "sw-TZ", "sw", "Female"),
        ("Puck",    "Puck — Clear & Engaging Natural",             "sw-TZ", "sw", "Male"),
        ("Zephyr",  "Zephyr — Peaceful & Warm",                    "sw-TZ", "sw", "Female"),
        ("Fenrir",  "Fenrir — Strong & Powerful",                  "sw-TZ", "sw", "Male"),
        ("Kore",    "Kore — Soft & Gentle",                        "sw-TZ", "sw", "Female"),
        ("Charon",  "Charon — Deep & Resonant",                    "sw-TZ", "sw", "Male"),
        ("Leda",    "Leda — Smooth & Calming",                     "sw-TZ", "sw", "Female"),
        ("Enceladus","Enceladus — Narrative Pro",                  "sw-TZ", "sw", "Male"),
    ]
    result = []
    # Add Swahili entries
    for name, desc, lang, lc, gender in VOICES:
        result.append({
            "provider": "direct-gemini", "voice_id": f"direct-gemini:{name}",
            "display_name": f"[GEMINI Swahili] {desc}", "language": "sw-TZ", "lang_code": "sw",
            "gender": gender, "is_free": True, "quality": "Gemini TTS"
        })
    # Add English entries
    for name, desc, lang, lc, gender in VOICES:
        result.append({
            "provider": "direct-gemini", "voice_id": f"direct-gemini:{name}",
            "display_name": f"[GEMINI English] {desc}", "language": "en-US", "lang_code": "en",
            "gender": gender, "is_free": True, "quality": "Gemini TTS"
        })
    return result


def _puter_static_voices() -> list[dict]:
    """Puter TTS voices (Gemini + OpenAI sub-providers via Puter)."""
    entries = []
    # Gemini via Puter
    for name in ["Puck", "Charon", "Kore", "Fenrir", "Aoede", "Leda", "Zephyr", "Enceladus"]:
        entries.append({
            "provider": "puter", "voice_id": f"puter:gemini:{name}",
            "display_name": f"[PUTER/Gemini] {name}", "language": "en-US",
            "lang_code": "en", "gender": "Neutral", "is_free": True, "quality": "Gemini"
        })
    # OpenAI via Puter
    for name in ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]:
        entries.append({
            "provider": "puter", "voice_id": f"puter:openai:{name}",
            "display_name": f"[PUTER/OpenAI] {name.capitalize()}", "language": "en-US",
            "lang_code": "en", "gender": "Neutral", "is_free": True, "quality": "OpenAI TTS"
        })
    return entries


def _elevenlabs_static_voices() -> list[dict]:
    """Verified working ElevenLabs premade voices on free/pro API tiers."""
    VOICES = [
        ("EXAVITQu4vr4xnSDxMaL", "Bella — Soft, Heartfelt Gospel Female",   "sw-TZ", "sw", "Female"),
        ("JBFqnCBsd6RMkjVDRZzb", "George — Warm Narrative Storyteller",      "en-US", "en", "Male"),
        ("onwK4e9ZLuTAKqWW03F9", "Daniel — Deep Authoritative Male",         "en-US", "en", "Male"),
        ("N2lVS1w4EtoT3dr4eOWO", "Callum — Expressive, Rich Male",           "en-US", "en", "Male"),
        ("TX3LPaxmHKxFdv7VOQHJ", "Liam — Articulate & Clear Male",           "en-US", "en", "Male"),
        ("Xb7hH8MSUJpSbSDYk0k2", "Alice — Confident, Inspiring Female",      "en-US", "en", "Female"),
        ("pqHfZKP75CvOlQylNhV4", "Bill — Wise, Reverent Old Male",           "en-US", "en", "Male"),
        ("nPczCjzI2devNBz1zQrb", "Brian — Deep Resonant Narrator",           "en-US", "en", "Male"),
        ("iP95p4xoKVk53GoZ742B", "Chris — Natural Everyday Male",            "en-US", "en", "Male"),
        ("cgSgspJ2msm6clMCkdW9", "Jessica — Youthful & Sincere Female",      "en-US", "en", "Female"),
        ("pFZP5JQG7iQjIQuC4Bku", "Lily — Warm & Uplifting Female",           "en-US", "en", "Female"),
        ("XrExE9yKIg1WjnnlVkGX", "Matilda — Motherly & Comforting Female",   "en-US", "en", "Female"),
        ("bIHbv24MWmeRgasZH58o", "Will — Relaxed & Calming Male",            "en-US", "en", "Male"),
    ]
    entries = []
    for vid, desc, lang, lc, gender in VOICES:
        entries.append({
            "provider": "elevenlabs",
            "voice_id": f"elevenlabs:{vid}",
            "display_name": f"[11Labs] {desc}",
            "language": lang,
            "lang_code": lc,
            "gender": gender,
            "is_free": False,
            "quality": "ElevenLabs Multilingual v2"
        })
    return entries


# ─── Preview Generation ───────────────────────────────────────────────────────

async def preview_voice(voice_id: str, text: str, rate: str = "+0%") -> Optional[str]:
    """
    Generates a TTS preview audio file and returns the web-accessible URL path.

    Args:
        voice_id: The voice identifier (same format as ACTIVE_VOICE in settings)
        text:     Preview text (max 200 chars used)
        rate:     Speech rate modifier (e.g. "+0%", "+10%")

    Returns:
        URL path string like "/output/previews/preview_abc123.mp3"
        or None on failure.
    """
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    preview_id  = uuid.uuid4().hex[:10]
    out_path    = PREVIEW_DIR / f"preview_{preview_id}.mp3"
    safe_text   = text.strip()[:200] or "Mungu ni mwema."

    mp3_bytes: Optional[bytes] = None

    try:
        if voice_id.startswith("puter:"):
            from src.audio.tts_engine import generate_puter_tts
            import config.settings
            token = getattr(config.settings, "PUTER_TOKEN", "")
            mp3_bytes = await generate_puter_tts(safe_text, voice_id, token)

        elif voice_id.startswith("direct-gemini:"):
            from src.audio.tts_engine import generate_gemini_tts_with_fallback
            import config.settings
            primary_key = getattr(config.settings, "GEMINI_API_KEY", "")
            mp3_bytes = await generate_gemini_tts_with_fallback(safe_text, voice_id, primary_key)

        elif voice_id.startswith("elevenlabs:"):
            from src.audio.tts_engine import generate_elevenlabs_tts
            import config.settings
            keys     = getattr(config.settings, "ELEVENLABS_KEYS", [])
            api_key  = keys[0] if keys else ""
            raw_id   = voice_id.split(":", 1)[1]
            mp3_bytes = await generate_elevenlabs_tts(safe_text, raw_id, api_key)

        else:
            # Default: Edge TTS
            import edge_tts
            import io
            communicate = edge_tts.Communicate(text=safe_text, voice=voice_id, rate=rate)
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            mp3_bytes = buf.getvalue()

        if not mp3_bytes:
            return None

        out_path.write_bytes(mp3_bytes)
        return f"/output/previews/preview_{preview_id}.mp3"

    except Exception as e:
        print(f"  [VoiceCatalog] Preview failed for {voice_id}: {e}")
        return None


def cleanup_old_previews(max_age_minutes: int = 60) -> int:
    """Deletes preview files older than max_age_minutes. Returns count deleted."""
    if not PREVIEW_DIR.exists():
        return 0
    cutoff = time.time() - (max_age_minutes * 60)
    deleted = 0
    for f in PREVIEW_DIR.glob("preview_*.mp3"):
        if f.stat().st_mtime < cutoff:
            try:
                f.unlink()
                deleted += 1
            except Exception:
                pass
    return deleted


if __name__ == "__main__":
    async def _test():
        voices = await get_all_voices()
        sw = [v for v in voices if v["lang_code"] == "sw"]
        print(f"Total voices: {len(voices)}")
        print(f"Swahili voices: {len(sw)}")
        for v in sw[:6]:
            print(f"  {v['provider']:15s} {v['voice_id']:35s} {v['gender']}")

    asyncio.run(_test())
