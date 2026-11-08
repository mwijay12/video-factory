# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY - SOCIAL MEDIA STRATEGY & VIRAL KIT GENERATOR
# Generates platform-optimized titles, captions, hooks, CTAs,
# and high-converting hashtag bundles for TikTok, Reels & Shorts.
# ================================================================

import json
import re
from pathlib import Path
from datetime import datetime


# Niche-specific viral hashtag bundles
HASHTAG_POOLS = {
    "gospel_swahili": [
        "#SwahiliGospel", "#GospelMusic", "#PianoSifa", "#AmapianoGospel",
        "#NyimboZaInjili", "#MunguNiMwema", "#GospelTanzania", "#GospelKenya",
        "#WorshipVibes", "#ChristianTikTok", "#YesuNiBwana", "#Injili",
        "#GospelBeat", "#PraiseAndWorship", "#GospelTok"
    ],
    "gospel_english": [
        "#GospelMusic", "#ChristianTikTok", "#WorshipMusic", "#PraiseAndWorship",
        "#GospelVibes", "#PianoSifa", "#JesusIsKing", "#FaithOverFear",
        "#ChristianReels", "#GospelBeats", "#HolySpirit", "#WorshipLeader",
        "#GospelShorts", "#ChurchVibes", "#JesusTok"
    ],
    "prayer": [
        "#DailyPrayer", "#MorningPrayer", "#BedtimePrayer", "#PrayerWarriors",
        "#PowerOfPrayer", "#ChristianMotivation", "#GodIsGood", "#TrustGod",
        "#SpiritualAwakening", "#PrayerChangesThings", "#JesusLovesYou"
    ],
    "praise": [
        "#PraiseBreak", "#JoyInTheLord", "#GospelDance", "#SundayService",
        "#ThankfulHeart", "#PraiseTheLord", "#HighPraise", "#GospelGroove"
    ],
    "motivational": [
        "#ChristianMotivation", "#FaithJourney", "#NeverGiveUp", "#GodsPlan",
        "#DailyInspiration", "#BlessedAndGrateful", "#Overcomer", "#KeepGoing"
    ]
}

CALL_TO_ACTIONS = {
    "swahili": [
        "Andika 'AMEN' ikiwa unaamini Mungu anafungua milango yako leo! 🙏✨",
        "Save hii sauti kwa maombi yako ya asubuhi na jioni 🌅🤍",
        "Mtumie mtu mmoja anayehitaji kutiwa moyo na wimbo huu leo! 🕊️❤️",
        "Gusa like mara mbili kama wimbo huu umegusa moyo wako! 🔥✝️",
        "Weka alama ya ❤️ kwenye comments kumtukuza Mungu!",
    ],
    "english": [
        "Type 'AMEN' if you believe God is making a way for you right now! 🙏✨",
        "Save this sound to your daily worship playlist! 🌅🤍",
        "Share this with someone who needs peace and strength today! 🕊️❤️",
        "Double tap if this song touched your spirit! 🔥✝️",
        "Drop a ❤️ in the comments to give praise today!",
    ]
}


def clean_title_from_stem(stem: str) -> str:
    """Cleans raw song filename stem into a clean display title."""
    clean = stem
    for prefix in ["song_", "web_gospel_", "gospel_", "trend_"]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    # Remove timestamps like _20260818_123456
    clean = re.sub(r'_\d{8}_\d{6}', '', clean)
    clean = clean.replace('_', ' ').replace('-', ' ').strip()
    # Remove redundant tags
    clean = re.sub(r'\s+(best|amen|piano|final|mp3)\b', '', clean, flags=re.IGNORECASE).strip()
    return clean.title() if clean else "Gospel Anthem"


def generate_social_package(
    song_name: str,
    lyrics_text: str = "",
    subtitles: list = None,
    niche: str = "gospel",
    language: str = "swahili",
    mood: str = "peaceful"
) -> dict:
    """
    Creates a full multi-platform social media distribution kit.
    Tailored for TikTok, Instagram Reels, YouTube Shorts, and Facebook Reels.
    """
    is_swahili = (language.lower() in ["swahili", "sw"] or niche == "swahili")
    clean_title = clean_title_from_stem(song_name)

    # Extract punchline / hook snippet from lyrics
    punchline = ""
    if subtitles and len(subtitles) > 0:
        first_subs = [s["text"] for s in subtitles[:3] if s.get("text") and not s["text"].startswith("🎵")]
        if first_subs:
            punchline = " • ".join(first_subs[:2])
    elif lyrics_text:
        lines = [l.strip() for l in lyrics_text.splitlines() if l.strip() and not l.strip().startswith("🎵")]
        if lines:
            punchline = " • ".join(lines[:2])

    if not punchline:
        punchline = f"Kazi ya Kipekee ya Sifa | {clean_title}" if is_swahili else f"Anointed Worship & Praise | {clean_title}"

    # Pick CTAs
    cta_pool = CALL_TO_ACTIONS["swahili"] if is_swahili else CALL_TO_ACTIONS["english"]
    import random
    cta = random.choice(cta_pool)

    # Hashtags
    pool_key = "gospel_swahili" if is_swahili else "gospel_english"
    if niche in HASHTAG_POOLS:
        pool_key = niche
    hashtags = HASHTAG_POOLS.get(pool_key, HASHTAG_POOLS["gospel_swahili"])
    hashtag_string = " ".join(hashtags[:12])

    # 1. TIKTOK STRATEGY
    tiktok_hook = f"Huu wimbo utakubariki siku nzima 😭🙏 | {clean_title}" if is_swahili else f"This song will renew your spirit today 🙌🔥 | {clean_title}"
    tiktok_caption = f"{tiktok_hook}\n\n\"{punchline}\"\n\n{cta}\n\n{hashtag_string}"

    # 2. INSTAGRAM REELS STRATEGY
    ig_title = f"✨ {clean_title} — Piano Sifa Worship Session"
    ig_caption = (
        f"{ig_title}\n\n"
        f"📖 \"{punchline}\"\n\n"
        f"{cta}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎵 Wimbo: {clean_title}\n"
        f"🎹 Brand: Piano Sifa | VideoFactory Production\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtag_string}"
    )

    # 3. YOUTUBE SHORTS STRATEGY
    shorts_title = f"{clean_title} - Powerful Gospel Worship 🙏🔥 #Shorts #PianoSifa"
    shorts_description = (
        f"{clean_title} | Piano Sifa Official Gospel Reel\n\n"
        f"Lyrics Highlight:\n{punchline}\n\n"
        f"{cta}\n\n"
        f"Subscribe for daily Gospel Amapiano, Worship sessions, and Spiritual uplifting.\n\n"
        f"{hashtag_string}"
    )

    # 4. SOUND ATTRIBUTION
    sound_title = f"Piano Sifa - {clean_title} (Official Sound)"

    # Best posting time recommendation (EAT / GMT+3 and EST)
    best_times = [
        "06:30 AM - 08:30 AM (Morning devotion & commute)",
        "12:30 PM - 02:00 PM (Lunchtime inspiration)",
        "07:30 PM - 09:30 PM (Evening reflection & bedtime praise)"
    ]

    return {
        "song_name": song_name,
        "clean_title": clean_title,
        "punchline": punchline,
        "language": "swahili" if is_swahili else "english",
        "niche": niche,
        "sound_attribution": sound_title,
        "tiktok": {
            "hook": tiktok_hook,
            "caption": tiktok_caption,
            "hashtags": hashtags[:10]
        },
        "instagram": {
            "title": ig_title,
            "caption": ig_caption,
            "hashtags": hashtags[:15]
        },
        "youtube_shorts": {
            "title": shorts_title,
            "description": shorts_description,
            "tags": [h.replace("#", "") for h in hashtags[:15]]
        },
        "best_posting_times": best_times,
        "generated_at": datetime.now().isoformat()
    }


def save_social_kit(video_path: str, social_data: dict) -> dict:
    """Saves companion .json and .txt social media files alongside the rendered video."""
    v_path = Path(video_path)
    output_dir = v_path.parent
    base_stem = v_path.stem

    json_path = output_dir / f"{base_stem}_social_kit.json"
    txt_path = output_dir / f"{base_stem}_social_kit.txt"

    # Save JSON
    try:
        json_path.write_text(json.dumps(social_data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  Warning saving social kit json: {e}")

    # Save Clean Copy-Paste TXT
    try:
        txt_content = f"""================================================================
VIRAL SOCIAL MEDIA KIT - {social_data.get('clean_title', 'Reel')}
Generated by VideoFactory Social Engine
================================================================

🎵 RECOMMENDED SOUND TITLE:
{social_data.get('sound_attribution', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 TIKTOK CAPTION (Copy & Paste):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{social_data.get('tiktok', {}).get('caption', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 INSTAGRAM REELS CAPTION (Copy & Paste):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{social_data.get('instagram', {}).get('caption', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▶️ YOUTUBE SHORTS (Title & Description):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TITLE:
{social_data.get('youtube_shorts', {}).get('title', '')}

DESCRIPTION:
{social_data.get('youtube_shorts', {}).get('description', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ RECOMMENDED POSTING SCHEDULE (EAT / Global):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Morning: 06:30 AM - 08:30 AM
- Midday:  12:30 PM - 02:00 PM
- Evening: 07:30 PM - 09:30 PM
================================================================
"""
        txt_path.write_text(txt_content, encoding="utf-8")
    except Exception as e:
        print(f"  Warning saving social kit txt: {e}")

    return {
        "json_path": str(json_path),
        "txt_path": str(txt_path)
    }


def print_social_kit_banner(social_data: dict):
    """Prints an aesthetic terminal summary of the generated social media kit."""
    title = social_data.get("clean_title", "Gospel Reel")
    sound = social_data.get("sound_attribution", "")
    tt_cap = social_data.get("tiktok", {}).get("caption", "").splitlines()[0]
    
    print("")
    print("=" * 62)
    print("  🚀 VIRAL SOCIAL MEDIA KIT READY")
    print("=" * 62)
    print(f"  Song Title:   {title}")
    print(f"  Sound Name:   {sound}")
    print(f"  TikTok Hook:  {tt_cap}")
    print(f"  Reels Ready:  Yes (Captions & Hashtags saved)")
    print(f"  Shorts SEO:   Yes (Optimized title generated)")
    print("=" * 62)
    print("")
