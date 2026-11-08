"""
PIANO SIFA TRENDS PICKER
========================
Uses Cloudflare Workers AI to score trends from VideoFactory's
trends cache and recommend the most timely song topics.

Free tier: 70k neurons/day across 7 accounts.
"""
import json
import os
import re
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from collections import Counter
from datetime import datetime
import random


# ============================================================
# CLOUDFLARE TOKEN POOL
# Reads from auth.json (credential_pool.cloudflare) first, then falls
# back to hermes .env. Updated 2026-07-01 because tokens moved out of
# the flat .env into the structured credential pool.
# ============================================================
def load_tokens():
    tokens = {}

    # 1) auth.json — primary source (Hermes credential pool)
    auth_path = Path(r"C:\Users\MWIJAY TECH\AppData\Local\hermes\auth.json")
    if auth_path.exists():
        try:
            data = json.loads(auth_path.read_text(encoding="utf-8", errors="ignore"))
            pool = data.get("credential_pool", {}).get("cloudflare", [])
            for i, entry in enumerate(pool, 1):
                tok = (entry.get("access_token") or "").strip()
                if not tok:
                    continue
                # Filter out tokens that hit a hard 401 (invalid) recently
                err_code = entry.get("last_error_code")
                if err_code in (401, 403):
                    continue
                tokens[i] = {
                    "token": tok,
                    "account_id": (entry.get("account_id") or "").strip() or "0e243591b6978f1d2a86fd50074cb8fd",
                    "label": entry.get("label", f"cf-key-{i}"),
                }
        except Exception as e:
            print(f"   warn: auth.json read failed: {e}")

    # 2) Fallback: hermes .env (legacy flat format)
    if not tokens:
        env_path = Path(r"C:\Users\MWIJAY TECH\AppData\Local\hermes\.env")
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8", errors="ignore")
            for i in range(1, 10):
                m_tok = re.search(rf"^CLOUDFLARE_API_TOKEN(?:_{i})?=(.*?)$", content, re.MULTILINE)
                m_id = re.search(rf"^CF_ACCOUNT_ID(?:_{i})?=(.*?)$", content, re.MULTILINE)
                if m_tok and m_tok.group(1).strip() and not m_tok.group(1).strip().startswith("#"):
                    tokens[i] = {
                        "token": m_tok.group(1).strip(),
                        "account_id": m_id.group(1).strip() if m_id else "0e243591b6978f1d2a86fd50074cb8fd",
                    }
    return tokens


TOKENS = load_tokens()


# ============================================================
# CLOUDFLARE INFERENCE
# ============================================================
MODELS = {
    "fast": "@cf/meta/llama-3.1-8b-instruct-fast",
    "default": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "swahili": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "code": "@cf/qwen/qwen2.5-coder-32b-instruct",
    "reason": "@cf/qwen/qwq-32b",
    "long": "@cf/moonshotai/kimi-k2.5",
    "image": "@cf/black-forest-labs/flux-1-schnell",
    "embed": "@cf/baai/bge-m3",
    "whisper": "@cf/openai/whisper-large-v3-turbo",
}


def cloudflare_chat(prompt: str, model: str = "default", max_tokens: int = 2000, _retries: int = 0) -> str:
    """Chat completion via Cloudflare Workers AI. Auto-rotates tokens."""
    if model not in MODELS:
        raise ValueError(f"Unknown model: {model}. Choices: {list(MODELS.keys())}")
    model_id = MODELS[model]

    if _retries >= len(TOKENS):
        raise RuntimeError(f"All {len(TOKENS)} Cloudflare tokens exhausted")

    idx = list(TOKENS.keys())[_retries]
    cfg = TOKENS[idx]
    url = f"https://api.cloudflare.com/client/v4/accounts/{cfg['account_id']}/ai/run/{model_id}"

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {cfg['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            if data.get("success"):
                return data["result"]["response"]
            else:
                return cloudflare_chat(prompt, model, max_tokens, _retries=_retries + 1)
    except urllib.error.HTTPError as e:
        if e.code in (401, 429):
            return cloudflare_chat(prompt, model, max_tokens, _retries=_retries + 1)
        raise


# ============================================================
# TRENDS CACHE + FILTERING
# ============================================================
def load_trends() -> list:
    cache = Path(r"C:\Users\MWIJAY TECH\VideoFactory\output\.trends_cache.json")
    if not cache.exists():
        return []
    data = json.loads(cache.read_text(encoding="utf-8", errors="ignore"))
    return data.get("trends", [])


def score_for_piano_sifa(trend: dict) -> int:
    """Score a trend 0-100 by relevance to Piano Sifa brand."""
    title = trend.get("title", "").lower()
    cat = trend.get("category", "").lower()
    source = trend.get("source", "")

    score = 0

    # Category bonus
    cat_scores = {
        "gospel_music": 80,
        "megachurch": 60,
        "church_news": 50,
        "celebrity": 40,
        "revival": 40,
        "bible_news": 35,
        "african_christian": 70,
        "persecution": 30,
        "unity": 25,
        "victory": 35,
        "testimony": 30,
        "moral_issue": 25,
        "general": 5,
        "tech": 10,
        "sports": 10,
        "tragedy": 15,
    }
    score += cat_scores.get(cat, 0)

    # Keyword matches
    keywords = {
        "jesus": 40, "worship": 35, "gospel": 35, "christ": 30,
        "prayer": 25, "church": 25, "faith": 20, "spirit": 20,
        "holy": 20, "tanzania": 30, "kenya": 25, "africa": 25,
        "uganda": 25, "pastor": 20, "bishop": 20, "revival": 25,
        "anointing": 25, "grace": 20, "mercy": 20,
        "amapiano": 30, "worship song": 35, "praise": 30,
        "divine": 20, "saviour": 25, "heal": 20, "dance": 15,
        "music": 10, "concert": 15, "contest": 15, "song": 10,
        "alex": 15,  # for "Alexandra Osteen" etc
        "osteoporosis".replace("oporosis", "andra"): 100,  # hack: not relevant
    }

    # Cleaner keyword check (avoid silly)
    clean_keywords = {
        "jesus": 40, "worship": 35, "gospel": 35, "christ": 30,
        "prayer": 25, "church": 25, "faith": 20, "holy spirit": 25,
        "holy": 20, "tanzania": 30, "kenya": 25, "africa": 25,
        "uganda": 25, "pastor": 20, "bishop": 20, "revival": 25,
        "anointing": 25, "grace": 20, "mercy": 20,
        "amapiano": 30, "worship song": 35, "praise": 30,
        "divine": 20, "saviour": 25, "heal": 20,
        "alexandra osteen": 60, "alex osteen": 60,
        "osteoporosis".replace("oporosis", "andra"): 0,  # irrelevant
    }

    for kw, weight in clean_keywords.items():
        if kw in title:
            score += weight

    return min(score, 100)


def pick_top_piano_sifa_trends(n: int = 10) -> list:
    """Pick top N trends for Piano Sifa brand."""
    trends = load_trends()
    if not trends:
        return []
    scored = [(t, score_for_piano_sifa(t)) for t in trends]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:n]
    return [{"trend": t, "score": s} for t, s in top]


# ============================================================
# LYRIC/IDEA GENERATION
# ============================================================
PIANO_SIFA_PROMPT = """You are the lead songwriter for "Piano Sifa", a Gospel Amapiano ministry from Dar es Salaam, Tanzania led by Mwijay Davie.

Brand voice:
- Mixed Swahili + English naturally
- Divine Realism: grounded in real urban Tanzanian life but illuminated by grace
- Cinematic quality — every line paints a picture
- Worship + celebration, NOT preachy
- Reference Tanzanian context when relevant (Ubongo, Mikoa, Nairobi, etc.) but universal enough for global audience

Given this real, current news trend:

TITLE: {title}
CATEGORY: {category}
SOURCE: {source}
PUBLISHER: {publisher}
SNIPPET: {snippet}

Generate exactly:
1. ANGLE: A 1-sentence song concept that bridges this trend with Gospel Amapiano worship (in English)
2. SWAHILI HOOK: A 4-line hook in natural Swahili that captures the moment (use mixed Swahili/English sparingly if authentic)
3. ENGLISH VERSE: A 4-line first verse mixing English lyricism with the trend
4. BPM/STYLE: Suggest BPM and 3 style tags from this list: amapiano, gospel, afrobeats, log drums, choir, worship, uplifting, afro-gospel, praise, anthemic, deeply spiritual
5. VISUAL CONCEPT: A 2-sentence visual / film concept for the official music video

Make it cinematic, not preachy. Make Tanzanians nod. Make foreigners cry."""


def generate_song_from_trend(trend: dict) -> dict:
    """Use Cloudflare to generate song concept from trend."""
    prompt = PIANO_SIFA_PROMPT.format(
        title=trend.get("title", "")[:200],
        category=trend.get("category", ""),
        source=trend.get("source", ""),
        publisher=trend.get("publisher", "")[:80],
        snippet=trend.get("snippet", trend.get("summary", ""))[:300],
    )
    response = cloudflare_chat(prompt, model="swahili", max_tokens=1500)
    return {
        "trend": trend,
        "concept": response,
        "generated_at": datetime.now().isoformat(),
    }


# ============================================================
# MAIN: RUN FROM CLI
# ============================================================
if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    print(f"=== Piano Sifa Trends Picker ===\n")
    print(f"Loading trends from VideoFactory cache...")

    top = pick_top_piano_sifa_trends(n)
    if not top:
        print("No trends found. Run build_unified_trends.py in VideoFactory first.")
        sys.exit(1)

    print(f"Found {len(top)} top-scored trends. Generating songs...\n")

    output_dir = Path(r"C:\Users\MWIJAY TECH\Music\Piano_Sifa\Trend_Songs")
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, item in enumerate(top, 1):
        trend = item["trend"]
        score = item["score"]
        print(f"\n[{i}/{n}] Score {score} | {trend.get('category')} | {trend.get('title', '')[:80]}")
        print(f"   Source: {trend.get('source')} / {trend.get('publisher', '')[:40]}")

        print("   Generating concept via Cloudflare Llama 3.3 70B...")
        try:
            result = generate_song_from_trend(trend)
            concept = result["concept"]

            # Save to file
            safe_title = re.sub(r'[^a-z0-9]+', '_', trend.get('title', 'untitled')[:50].lower())
            outfile = output_dir / f"{datetime.now().strftime('%Y%m%d')}_{score}_{safe_title}.md"
            with outfile.open("w", encoding="utf-8") as f:
                f.write(f"# Piano Sifa Trend Song ({score}/100)\n\n")
                f.write(f"**Trend:** {trend.get('title')}\n")
                f.write(f"**Category:** {trend.get('category')}\n")
                f.write(f"**Source:** {trend.get('source')} - {trend.get('publisher')}\n")
                f.write(f"**URL:** {trend.get('url', 'N/A')}\n\n")
                f.write(f"**Generated:** {result['generated_at']}\n")
                f.write(f"**Model:** Cloudflare Llama 3.3 70B (free tier)\n\n---\n\n")
                f.write(concept)

            print(f"   OK Saved to {outfile}")

        except Exception as e:
            print(f"   FAIL {e}")
