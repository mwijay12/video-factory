# -*- coding: utf-8 -*-
# ================================================================
# TRENDING TOPICS ENGINE - UNIFIED v3.0
# ================================================================
# FREE SOURCES (no API key needed):
#   ✅ Google News RSS (world, Christian, tech, sports, EA, Kenya)
#   ✅ Reddit JSON API (public endpoint, no auth)
#   ✅ Hacker News Firebase API
#   ✅ YouTube Trending RSS (by country/category)
#   ✅ BBC News RSS
#   ✅ Al Jazeera RSS
#   ✅ DW News RSS (Africa focus)
#   ✅ Christian Post RSS
#   ✅ Charisma News RSS
#   ✅ Bible Gateway Blog RSS
#   ✅ Premier Christian News RSS
#   ✅ Wikipedia Current Events (daily)
#
# OPTIONAL API SOURCES (set keys in .env):
#   🔑 NewsAPI.org (NEWSAPI_KEY) — free tier: 100 req/day
#   🔑 The Guardian API (GUARDIAN_KEY) — free tier: 12 calls/sec
#   🔑 GNews API (GNEWS_KEY) — free tier: 100 req/day
# ================================================================

import asyncio
import httpx
import json
import re
import random
import html
from pathlib import Path
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from src.utils.retry import retry_async


# ================================================================
# ENV LOADER
# ================================================================

def load_env():
    p = Path(".env")
    if not p.exists():
        return {}
    d = {}
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


ENV = load_env()
NEWSAPI_KEY   = ENV.get("NEWSAPI_KEY", "")
GUARDIAN_KEY  = ENV.get("GUARDIAN_KEY", "")
GNEWS_KEY     = ENV.get("GNEWS_KEY", "")

HTTP_TIMEOUT  = 4   # seconds per request
HTTP_HEADERS  = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ================================================================
# SOURCE REGISTRY
# ================================================================

# --- Google News RSS ---
GOOGLE_NEWS_FEEDS = {
    # General World
    "world":         "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "tech":          "https://news.google.com/rss/search?q=technology+AI&hl=en-US&gl=US&ceid=US:en",
    "sports":        "https://news.google.com/rss/search?q=sports&hl=en-US&gl=US&ceid=US:en",
    "business":      "https://news.google.com/rss/search?q=business&hl=en-US&gl=US&ceid=US:en",
    "health":        "https://news.google.com/rss/search?q=health+medicine&hl=en-US&gl=US&ceid=US:en",
    "east_africa":   "https://news.google.com/rss/search?q=east+africa+OR+kenya+OR+tanzania+OR+uganda&hl=en-KE&gl=KE&ceid=KE:en",
    "kenya":         "https://news.google.com/rss/search?q=kenya&hl=en-KE&gl=KE&ceid=KE:en",
    "tanzania":      "https://news.google.com/rss/search?q=tanzania&hl=en-TZ&gl=TZ&ceid=TZ:en",
    # Christian
    "christian":          "https://news.google.com/rss/search?q=christian+OR+church+OR+gospel&hl=en-US&gl=US&ceid=US:en",
    "church_news":        "https://news.google.com/rss/search?q=church+OR+pastor+OR+ministry&hl=en-US&gl=US&ceid=US:en",
    "gospel_music":       "https://news.google.com/rss/search?q=gospel+music+OR+christian+artist+OR+worship+song&hl=en-US&gl=US&ceid=US:en",
    "megachurch":         "https://news.google.com/rss/search?q=joel+osteen+OR+td+jakes+OR+steven+furtick+OR+hillsong&hl=en-US&gl=US&ceid=US:en",
    "persecution":        "https://news.google.com/rss/search?q=christian+persecution+OR+church+attacked&hl=en-US&gl=US&ceid=US:en",
    "revival":            "https://news.google.com/rss/search?q=revival+OR+crusade+OR+gospel+festival&hl=en-US&gl=US&ceid=US:en",
    "bible_news":         "https://news.google.com/rss/search?q=bible+discovery+OR+jesus+OR+biblical&hl=en-US&gl=US&ceid=US:en",
    "african_christian":  "https://news.google.com/rss/search?q=christian+africa+OR+pastor+kenya+OR+church+tanzania&hl=en-US&gl=US&ceid=US:en",
    "morality":           "https://news.google.com/rss/search?q=family+values+OR+marriage+OR+religious+freedom&hl=en-US&gl=US&ceid=US:en",
}

# --- Specialty RSS Feeds (free, no auth) ---
SPECIALTY_FEEDS = {
    # World News
    "bbc_world":          "http://feeds.bbci.co.uk/news/world/rss.xml",
    "bbc_africa":         "http://feeds.bbci.co.uk/news/world/africa/rss.xml",
    "aljazeera":          "https://www.aljazeera.com/xml/rss/all.xml",
    "dw_africa":          "https://rss.dw.com/rdf/rss-en-africa",
    "reuters":            "https://feeds.reuters.com/reuters/topNews",
    "ap_news":            "https://rsshub.app/apnews/topics/ap-top-news",
    # Christian / Faith
    "christian_post":     "https://www.christianpost.com/rss",
    "charisma_news":      "https://www.charismanews.com/us/feed",
    "premier_christian":  "https://www.premierchristianradio.com/Shows/Saturday/Unbelievable/Podcast-Episodes.feed",
    "crosswalk":          "https://www.crosswalk.com/rss/site.rss",
    "relevant_mag":       "https://relevantmagazine.com/feed/",
    "christianity_today": "https://www.christianitytoday.com/ct/rss/new-content/",
    # Science / Hope
    "nasa":               "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    # Kenya / EAfrica
    "nation_ke":          "https://nation.africa/rss.xml",
    "standardmedia_ke":   "https://www.standardmedia.co.ke/rss/headlines.php",
    "thecitizen_tz":      "https://www.thecitizen.co.tz/feed",
}

# YouTube country trending RSS (no key needed, public)
YOUTUBE_TRENDING_RSS = {
    "KE": "https://www.youtube.com/feeds/videos.xml?chart=mostpopular&regionCode=KE",
    "TZ": "https://www.youtube.com/feeds/videos.xml?chart=mostpopular&regionCode=TZ",
    "NG": "https://www.youtube.com/feeds/videos.xml?chart=mostpopular&regionCode=NG",
    "US": "https://www.youtube.com/feeds/videos.xml?chart=mostpopular&regionCode=US",
}

# Reddit subreddits
REDDIT_GENERAL  = ["worldnews", "news", "todayilearned", "upliftingnews", "mildlyinteresting"]
REDDIT_CHRISTIAN = ["Christianity", "Christian", "TrueChristian", "PrayerRequests", "reformed", "MuslimConvert"]
REDDIT_EA        = ["Kenya", "Tanzania", "Uganda", "Africa"]
REDDIT_TRENDING  = ["popular", "all"]


# ================================================================
# RSS PARSER HELPER
# ================================================================

def parse_rss_items(xml_text: str, source_tag: str, limit: int = 12) -> list:
    """Parse a standard RSS 2.0 or Atom feed and return headline dicts."""
    items = []
    try:
        # Convert to bytes to properly support encoding declarations in ET
        xml_bytes = xml_text.encode('utf-8', errors='ignore')
        root = ET.fromstring(xml_bytes)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # Try RSS 2.0 items
        rss_items = root.findall(".//item")
        # Try Atom entries if no RSS items
        if not rss_items:
            # Avoid using boolean 'or' on element findings to prevent deprecation warning
            rss_items = root.findall(".//atom:entry", ns)
            if not rss_items:
                rss_items = root.findall(".//entry")

        for el in rss_items[:limit]:
            # Title
            t = el.find("title")
            if t is None:
                t = el.find("atom:title", ns)
            
            if t is not None:
                title = "".join(t.itertext()).strip()
            else:
                title = ""

            title = html.unescape(re.sub(r"<[^>]+>", "", title))
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()

            if not title or len(title) < 8:
                continue

            # Link
            lk = el.find("link")
            if lk is None:
                lk = el.find("atom:link", ns)
                
            url = ""
            if lk is not None:
                url = "".join(lk.itertext()).strip() or lk.get("href", "") or ""

            # Source/publisher
            src = el.find("source")
            publisher = ""
            if src is not None:
                publisher = "".join(src.itertext()).strip()
            if not publisher:
                publisher = source_tag

            items.append({
                "source": source_tag,
                "title": title,
                "publisher": publisher,
                "url": url.strip(),
            })

    except Exception as e:
        print(f"  RSS parse error [{source_tag}]: {e}")
    return items


# ================================================================
# FREE FETCHERS
# ================================================================

@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_google_news(topic: str, limit: int = 12) -> list:
    url = GOOGLE_NEWS_FEEDS.get(topic)
    if not url:
        return []
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS, follow_redirects=True) as c:
        r = await c.get(url)
        if r.status_code == 200:
            items = parse_rss_items(r.text, f"google_{topic}", limit)
            print(f"  Google News [{topic}]: {len(items)} items")
            return items
        else:
            raise Exception(f"Google News [{topic}] status {r.status_code}")


@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_specialty_feed(name: str, url: str, limit: int = 10) -> list:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS, follow_redirects=True) as c:
        r = await c.get(url)
        if r.status_code == 200:
            items = parse_rss_items(r.text, name, limit)
            print(f"  [{name}]: {len(items)} items")
            return items
        else:
            raise Exception(f"[{name}] status {r.status_code}")


@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_youtube_trending(region: str = "KE", limit: int = 10) -> list:
    url = YOUTUBE_TRENDING_RSS.get(region, YOUTUBE_TRENDING_RSS["US"])
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS, follow_redirects=True) as c:
        r = await c.get(url)
        if r.status_code == 200:
            items = parse_rss_items(r.text, f"youtube_trending_{region}", limit)
            for item in items:
                item["source_type"] = "video"
            print(f"  YouTube Trending [{region}]: {len(items)} videos")
            return items
        else:
            raise Exception(f"YouTube Trending [{region}] status {r.status_code}")


@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_single_reddit_sub(sub: str, limit: int, headers: dict) -> list:
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
    posts = []
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=headers, follow_redirects=True) as c:
        r = await c.get(url)
        if r.status_code == 200:
            data = r.json()
            for post in data.get("data", {}).get("children", []):
                d = post.get("data", {})
                title = d.get("title", "").strip()
                if title and len(title) > 12 and not d.get("stickied"):
                    posts.append({
                        "source": f"reddit/{sub}",
                        "title": title,
                        "score": d.get("score", 0),
                        "url": f"https://reddit.com{d.get('permalink', '')}",
                        "upvotes": d.get("ups", 0),
                    })
            print(f"  Reddit r/{sub}: {len(posts)} posts")
            return posts
        else:
            raise Exception(f"Reddit r/{sub} status {r.status_code}")


async def fetch_reddit(subreddits: list, limit: int = 8) -> list:
    all_posts = []
    headers = {**HTTP_HEADERS, "User-Agent": "VideoFactory/3.0 TrendResearcher (by /u/videofactory_bot)"}
    
    tasks = [fetch_single_reddit_sub(sub, limit, headers) for sub in subreddits]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for res in results:
        if isinstance(res, list):
            all_posts.extend(res)
            
    return sorted(all_posts, key=lambda x: x.get("score", 0), reverse=True)


@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_hackernews(limit: int = 6) -> list:
    headlines = []
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as c:
        r = await c.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        if r.status_code == 200:
            ids = r.json()[:limit]
            tasks = [c.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json") for sid in ids]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for resp in responses:
                if isinstance(resp, Exception):
                    continue
                if resp.status_code == 200:
                    story = resp.json()
                    if story and story.get("title"):
                        headlines.append({
                            "source": "hackernews",
                            "title": story["title"],
                            "score": story.get("score", 0),
                            "url": story.get("url", f"https://news.ycombinator.com/item?id={story.get('id', '')}"),
                        })
            print(f"  HackerNews: {len(headlines)} stories")
            return headlines
        else:
            raise Exception(f"HackerNews status {r.status_code}")


@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_wikipedia_current_events(limit: int = 10) -> list:
    """Scrape Wikipedia's Today's Current Events page (no auth, public)."""
    from datetime import datetime as dt
    today = dt.now()
    # Try today and yesterday (in case today's not updated yet)
    dates = []
    # Windows doesn't support %-d — use %#d on Windows, %-d on Unix
    for fmt in ["%Y_%B_%#d", "%Y_%B_%-d", "%Y_%B_%d"]:
        try:
            dates = [today.strftime(fmt), (today - timedelta(days=1)).strftime(fmt)]
            break
        except Exception:
            continue
    if not dates:
        dates = [today.strftime("%Y_%B_%d"), (today - timedelta(days=1)).strftime("%Y_%B_%d")]

    headers = []
    last_err = None
    for date_str in dates:
        url = f"https://en.m.wikipedia.org/wiki/Portal:Current_events/{date_str}"
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS, follow_redirects=True) as c:
                r = await c.get(url)
                if r.status_code == 200:
                    # Extract bullet points (li items) from the page text
                    text = r.text
                    # Simple regex to find list items — strip HTML tags
                    raw_items = re.findall(r"<li[^>]*>(.*?)</li>", text, re.DOTALL)
                    for raw in raw_items[:limit * 2]:
                        clean = re.sub(r"<[^>]+>", "", raw).strip()
                        clean = html.unescape(clean).strip()
                        if len(clean) > 20 and len(clean) < 250:
                            headers.append({
                                "source": "wikipedia_events",
                                "title": clean[:200],
                                "url": url,
                            })
                    if headers:
                        print(f"  Wikipedia Current Events: {len(headers[:limit])} items")
                        return headers[:limit]
                else:
                    last_err = Exception(f"Wikipedia events status {r.status_code}")
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err
    return []


# ================================================================
# OPTIONAL API FETCHERS (need keys in .env)
# ================================================================

@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_newsapi(query: str = "trending", limit: int = 15) -> list:
    """NewsAPI.org — Free: 100 req/day. Get at: https://newsapi.org/register"""
    if not NEWSAPI_KEY:
        return []
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWSAPI_KEY,
        "pageSize": limit,
        "language": "en",
    }
    if query != "trending":
        params["q"] = query
    else:
        params["category"] = "general"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as c:
        r = await c.get(url, params=params)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            items = []
            for a in articles:
                title = a.get("title", "").strip()
                if title and "[Removed]" not in title:
                    items.append({
                        "source": "newsapi",
                        "title": title,
                        "publisher": a.get("source", {}).get("name", "NewsAPI"),
                        "url": a.get("url", ""),
                    })
            print(f"  NewsAPI [{query}]: {len(items)} articles")
            return items
        else:
            raise Exception(f"NewsAPI status {r.status_code}: {r.text}")


@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_guardian(query: str = "world", limit: int = 12) -> list:
    """The Guardian API — Free: unlimited (fair use). Get at: https://bonobo.capi.guim.co.uk/register/developer"""
    if not GUARDIAN_KEY:
        return []
    url = "https://content.guardianapis.com/search"
    params = {
        "api-key": GUARDIAN_KEY,
        "q": query,
        "order-by": "newest",
        "page-size": limit,
        "show-fields": "headline",
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as c:
        r = await c.get(url, params=params)
        if r.status_code == 200:
            results = r.json().get("response", {}).get("results", [])
            items = []
            for a in results:
                title = a.get("webTitle", "").strip()
                if title:
                    items.append({
                        "source": "guardian",
                        "title": title,
                        "publisher": "The Guardian",
                        "url": a.get("webUrl", ""),
                    })
            print(f"  Guardian [{query}]: {len(items)} articles")
            return items
        else:
            raise Exception(f"Guardian API status {r.status_code}: {r.text}")


@retry_async(max_attempts=3, base_delay=1.0)
async def fetch_gnews(query: str = "trending", limit: int = 10) -> list:
    """GNews API — Free: 100 req/day, 10 results/req. Get at: https://gnews.io"""
    if not GNEWS_KEY:
        return []
    url = "https://gnews.io/api/v4/search"
    params = {
        "token": GNEWS_KEY,
        "q": query,
        "lang": "en",
        "max": limit,
        "sortby": "publishedAt",
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as c:
        r = await c.get(url, params=params)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            items = []
            for a in articles:
                title = a.get("title", "").strip()
                if title:
                    items.append({
                        "source": "gnews",
                        "title": title,
                        "publisher": a.get("source", {}).get("name", "GNews"),
                        "url": a.get("url", ""),
                    })
            print(f"  GNews [{query}]: {len(items)} articles")
            return items
        else:
            raise Exception(f"GNews API status {r.status_code}: {r.text}")


# ================================================================
# CATEGORIZER
# ================================================================

CATEGORIES = {
    # CHRISTIAN (priority)
    "church_news":     ["church", "pastor", "ministry", "bishop", "minister", "reverend", "congregation", "sermon", "diocese", "archbishop"],
    "gospel_music":    ["gospel music", "gospel singer", "worship artist", "christian rapper", "hillsong", "elevation", "cece winans", "kirk franklin", "maverick city", "lecrae", "tasha cobbs", "travis greene", "sinach", "don moen"],
    "christian_celeb": ["baptized", "gave life to christ", "kanye gospel", "justin bieber faith", "denzel faith", "tyler perry faith", "christian celebrity", "gave his life", "born again"],
    "megachurch":      ["joel osteen", "td jakes", "t.d. jakes", "steven furtick", "judah smith", "rick warren", "lakewood", "elevation church", "hillsong church", "bethel church", "willow creek", "saddleback"],
    "persecution":     ["christian persecution", "church attacked", "pastor arrested", "church burned", "christian killed", "martyr", "persecuted christians", "christians flee"],
    "revival":         ["revival", "crusade", "gospel festival", "asbury", "awakening", "mass baptism", "mass conversion", "outpouring", "pentecost"],
    "bible_news":      ["bible discovery", "biblical", "dead sea scrolls", "jerusalem find", "israel archaeology", "ancient scroll", "old testament"],
    "african_church":  ["kenya pastor", "tanzania church", "nigeria pastor", "ghana pastor", "bishop kiuna", "apostle ng", "pastor muriithi", "stl church", "nairobi chapel"],
    "moral_issue":     ["abortion", "gender", "lgbtq", "transgender", "same-sex", "religious freedom", "family values", "marriage definition"],
    "prophecy":        ["prophecy", "end times", "rapture", "revelation", "antichrist", "second coming", "armageddon"],

    # GENERAL (good for spiritual angle)
    "tragedy":         ["death", "died", "killed", "dead", "tragedy", "crash", "earthquake", "disaster", "flood", "fire", "shooting", "attack", "war", "crisis", "massacre", "bombing", "explosion", "accident", "drowned", "stabbed", "violence", "victims", "casualties", "wounded", "injured", "famine", "drought", "epidemic", "outbreak"],
    "victory":         ["won", "wins", "victory", "champion", "success", "achieve", "record", "trophy", "gold medal", "breakthrough", "overcame", "triumph"],
    "unity":           ["together", "united", "peace", "agreement", "help", "rescue", "save", "reconciled", "solidarity", "community"],
    "struggle":        ["protest", "losing", "failure", "collapse", "recession", "unemployment", "poverty", "homeless", "strike", "riot"],
    "hope":            ["cure", "discovery", "innovation", "recovery", "rebuild", "healed", "miracle", "rescued", "survived", "breakthrough treatment"],
    "celebrity_death": ["died at", "passed away", "celebrity dies", "star dies", "actor dies", "singer dies", "found dead"],
    "celebrity":       ["celebrity", "star", "actor", "actress", "singer", "famous", "rapper", "taylor swift", "beyonce", "drake", "kanye", "rihanna", "ariana", "billie eilish", "selena gomez", "harry styles", "ed sheeran", "premiere", "red carpet", "grammy", "oscar", "emmy", "concert", "viral"],
    "youth_crisis":    ["teen suicide", "youth depression", "school shooting", "mental health crisis", "bullying", "fentanyl"],
    "sports":          ["football", "soccer", "basketball", "tennis", "cricket", "rugby", "boxing", "mma", "ufc", "fifa", "olympics", "champions league", "world cup", "premier league", "la liga", "psg", "real madrid", "barcelona", "manchester", "arsenal", "chelsea", "liverpool", "messi", "ronaldo", "mbappe", "haaland", "neymar", "nba", "nfl", "mlb", "nhl", "ipl", "afcon", "match", "game", "goal", "score", "final", "semifinal", "quarterfinal", "stadium", "coach", "manager", "transfer", "signed", "athlete", "player", "team", "league", "trophy", "title", "kenya rugby", "harambee stars", "taifa stars", "simba", "yanga"],
    "tech":            ["ai", "artificial intelligence", "technology", "tech", "apple", "google", "microsoft", "chatgpt", "openai", "robot", "startup", "gadget", "software", "app", "cybersecurity", "hack", "elon musk", "spacex"],
    "business":        ["stock", "market", "economy", "inflation", "banks", "investment", "crypto", "bitcoin", "dollar", "shilling", "gdp"],
    "health":          ["cancer", "vaccine", "mental health", "hospital", "disease", "outbreak", "healing", "medical", "therapy"],
    "politics":        ["president", "election", "parliament", "government", "vote", "senator", "minister", "policy", "law", "court", "supreme court"],
}

CHRISTIAN_CATEGORIES = {
    "church_news", "gospel_music", "christian_celeb", "megachurch",
    "persecution", "revival", "bible_news", "african_church", "moral_issue", "prophecy"
}


def has_keyword(text_lower: str, kw: str) -> bool:
    if len(kw) <= 3:
        return re.search(r'' + re.escape(kw) + r'', text_lower) is not None
    return kw in text_lower


def categorize_trend(title: str) -> str:
    title_lower = title.lower()

    # Priority 1: Christian categories
    christian_priority = [
        "megachurch", "gospel_music", "christian_celeb", "persecution",
        "revival", "bible_news", "african_church", "prophecy", "moral_issue", "church_news"
    ]
    for cat in christian_priority:
        if cat in CATEGORIES:
            for kw in CATEGORIES[cat]:
                if has_keyword(title_lower, kw):
                    return cat

    # Priority 2: High-signal general topics
    general_priority = ["celebrity_death", "youth_crisis", "sports", "tech", "business", "politics", "health"]
    for cat in general_priority:
        if cat in CATEGORIES:
            for kw in CATEGORIES[cat]:
                if has_keyword(title_lower, kw):
                    return cat

    # Priority 3: Emotional / narrative categories
    for cat, kws in CATEGORIES.items():
        if cat in CHRISTIAN_CATEGORIES or cat in general_priority:
            continue
        for kw in kws:
            if has_keyword(title_lower, kw):
                return cat

    return "general"


# ================================================================
# MAIN COLLECTOR CLASS
# ================================================================

class TrendCollector:

    def __init__(self):
        self.cache_file = Path("output/.trends_cache.json")

    async def collect_all_trends(self, regions=None, sources=None):
        """Collect from ALL enabled sources concurrently."""
        print("")
        print("=" * 66)
        print("  COLLECTING TRENDING TOPICS — VideoFactory v3.0")
        print("=" * 66)

        tasks = []

        # 1. Google News RSS
        google_regions = regions or [
            "world", "east_africa", "kenya", "tanzania",
            "sports", "tech", "business", "health",
            "christian", "church_news", "gospel_music",
            "megachurch", "persecution", "revival",
            "bible_news", "african_christian", "morality",
        ]
        for region in google_regions:
            tasks.append(fetch_google_news(region, limit=15))

        # 2. Specialty RSS Feeds
        specialty_to_use = sources or [
            "bbc_world", "bbc_africa", "aljazeera", "dw_africa",
            "christian_post", "charisma_news", "crosswalk",
            "relevant_mag", "christianity_today",
            "nation_ke", "standardmedia_ke", "thecitizen_tz",
        ]
        for name in specialty_to_use:
            if name in SPECIALTY_FEEDS:
                tasks.append(fetch_specialty_feed(name, SPECIALTY_FEEDS[name], limit=10))

        # 3. YouTube Trending (Kenya, Tanzania, Nigeria, US)
        for region in ["KE", "TZ", "NG"]:
            tasks.append(fetch_youtube_trending(region, limit=8))

        # 4. Reddit
        tasks.append(fetch_reddit(REDDIT_GENERAL, limit=10))
        tasks.append(fetch_reddit(REDDIT_CHRISTIAN, limit=10))
        tasks.append(fetch_reddit(REDDIT_EA, limit=8))

        # 5. HackerNews
        tasks.append(fetch_hackernews(limit=6))

        # 6. Wikipedia Current Events
        tasks.append(fetch_wikipedia_current_events(limit=8))

        # 7. Optional API sources (only if keys set)
        if NEWSAPI_KEY:
            tasks.append(fetch_newsapi("world news", limit=15))
            tasks.append(fetch_newsapi("christian church gospel", limit=10))
        if GUARDIAN_KEY:
            tasks.append(fetch_guardian("world", limit=12))
            tasks.append(fetch_guardian("religion faith church", limit=10))
        if GNEWS_KEY:
            tasks.append(fetch_gnews("trending world news", limit=10))

        print(f"  Running {len(tasks)} concurrent fetch tasks...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_trends = []
        for res in results:
            if isinstance(res, list):
                all_trends.extend(res)
            elif isinstance(res, Exception):
                print(f"  Subtask error: {res}")

        # Categorize
        for trend in all_trends:
            if "category" not in trend:
                trend["category"] = categorize_trend(trend["title"])

        # Deduplicate by title (first 55 chars)
        seen = set()
        unique = []
        for t in all_trends:
            key = re.sub(r"\s+", " ", t["title"].lower()[:55]).strip()
            if key not in seen:
                seen.add(key)
                unique.append(t)

        print(f"")
        print(f"  [SUCCESS] Total unique trends collected: {len(unique)}")
        print("")

        # Save cache
        self.cache_file.parent.mkdir(exist_ok=True, parents=True)
        self.cache_file.write_text(json.dumps({
            "collected_at": datetime.now().isoformat(),
            "count": len(unique),
            "trends": unique,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

        return unique

    def get_cached_trends(self):
        if not self.cache_file.exists():
            return []
        try:
            data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            return data.get("trends", [])
        except Exception:
            return []

    def get_cache_age_minutes(self) -> float:
        if not self.cache_file.exists():
            return 9999
        try:
            data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            collected = datetime.fromisoformat(data.get("collected_at", "2000-01-01"))
            return (datetime.now() - collected).total_seconds() / 60
        except Exception:
            return 9999

    def pick_best_trends(self, trends=None, categories=None, count=5, christian_ratio=0.6):
        if trends is None:
            trends = self.get_cached_trends()

        if categories:
            filtered = [t for t in trends if t.get("category") in categories]
            if not filtered:
                # Fuzzy keyword search fallback
                kw_map = {
                    "sports": ["football", "soccer", "basketball", "tennis", "cricket", "match", "goal", "athlete"],
                    "tragedy": ["death", "died", "killed", "dead", "crash", "disaster", "attack", "accident"],
                    "celebrity": ["star", "actor", "actress", "singer", "celebrity", "rapper"],
                    "tech": ["ai", "technology", "google", "apple", "chatgpt", "microsoft"],
                    "church_news": ["church", "pastor", "ministry", "congregation", "sermon", "bishop"],
                    "gospel_music": ["gospel", "worship", "song", "singer", "artist", "choir"],
                    "revival": ["revival", "crusade", "awakening", "baptism"],
                    "bible_news": ["bible", "biblical", "discovery", "jerusalem", "israel"],
                    "african_church": ["pastor kenya", "church tanzania", "nigeria", "africa", "bishop"],
                }
                for cat in categories:
                    if cat in kw_map:
                        for trend in trends:
                            tl = trend["title"].lower()
                            for kw in kw_map[cat]:
                                if kw in tl:
                                    filtered.append(trend)
                                    break
            random.shuffle(filtered)
            return filtered[:count]

        # Balanced default mix
        christian_trends = [t for t in trends if t.get("category") in CHRISTIAN_CATEGORIES]
        general_trends   = [t for t in trends if t.get("category") not in CHRISTIAN_CATEGORIES and t.get("category") != "general"]

        random.shuffle(christian_trends)
        random.shuffle(general_trends)

        c_n = max(1, int(count * christian_ratio))
        g_n = count - c_n
        result = christian_trends[:c_n] + general_trends[:g_n]
        random.shuffle(result)
        return result[:count]

    def show_summary(self, trends=None):
        if trends is None:
            trends = self.get_cached_trends()
        if not trends:
            print("No trends cached. Run collect_all_trends() first.")
            return

        by_cat = {}
        for t in trends:
            cat = t.get("category", "general")
            by_cat.setdefault(cat, []).append(t)

        print("")
        print("=" * 66)
        print(f"  TRENDING TOPICS ({len(trends)} total)")
        print("=" * 66)

        print("\n  *** CHRISTIAN TRENDS ***")
        for cat in sorted(by_cat.keys()):
            if cat not in CHRISTIAN_CATEGORIES:
                continue
            items = by_cat[cat]
            print(f"\n  [{cat.upper()}] {len(items)} items")
            for t in items[:3]:
                print(f"    - {t['title'][:80]}")

        print("\n\n\n  *** WORLD TRENDS ***")
        for cat in sorted(by_cat.keys()):
            if cat in CHRISTIAN_CATEGORIES or cat == "general":
                continue
            items = by_cat[cat]
            print(f"\n  [{cat.upper()}] {len(items)} items")
            for t in items[:3]:
                print(f"    - {t['title'][:80]}")
        print("")


# ================================================================
# AI: TREND → SPIRITUAL REEL SCRIPT
# ================================================================

async def trend_to_spiritual_script(trend, niche="gospel", language="english"):
    from src.scripts.ai_generator import (
        generate_with_groq,
        generate_with_gemini,
        generate_with_openrouter,
        clean_ai_output,
        MOOD_VARIANTS,
        CTA_TEMPLATES,
        SWAHILI_CTA_TEMPLATES,
    )

    trend_title = trend.get("title", "")
    category    = trend.get("category", "general")

    if not trend_title:
        return None

    if language == "swahili":
        variant = random.choice(MOOD_VARIANTS["swahili"])
    else:
        variant = random.choice(MOOD_VARIANTS.get(niche, MOOD_VARIANTS["gospel"]))
    mood    = variant["mood"]
    cta     = random.choice(SWAHILI_CTA_TEMPLATES if language == "swahili" else CTA_TEMPLATES)
    is_christian = category in CHRISTIAN_CATEGORIES

    if language == "swahili":
        prompt = f"""Wewe ni mtengenezaji wa video za kiroho zinazoshtua na kufundisha.

LAZIMA UANDIKE KILA KITU KWA KISWAHILI TUPU, KISWAHILI FASHA NA CHA ASILI.
HAKUNA KIINGEREZA KABISA kwenye maneno yatakayosomwa. Hata mstari wa mwisho LAZIMA uwe Kiswahili.

HABARI YA LEO:
"{trend_title}"
Aina: {category}

Tengeneza script ya reel ya sekunde 25-30 inayohusisha habari hii na mafundisho ya kiroho au ujumbe wa Biblia.

MUUNDO (Mistari 8-9):
1. Mstari 1 HOOK: Taja habari hii kwa msisitizo
2. Mistari 2-7 MWILI: Unganisha na mstari wa Biblia au ujumbe wa kiroho
3. Mstari wa MWISHO: "{cta}"

SHERIA MUHIMU ZA LUGHA NA MPANGILIO:
- KILA mstari LAZIMA uwe Kiswahili fasaha cha asili ya Afrika Mashariki (Tanzania/Kenya).
- Epuka tafsiri ya moja kwa moja ya maneno kutoka Kiingereza (avoid literal translations). Sentensi ziwe za asili na zinazotumiwa na wasemaji wazawa (native sounding).
- Hakikisha sarufi (grammar) na tahajia (spelling) ni sahihi 100%.
- Mistari mifupi ya maneno 5-9
- Tone: {mood}
- LAZIMA: Weka emoji 1-2 zinazofaa (mfano: 🙏, ✨, 😢, ❤️) mwanzoni au katikati ya kila mstari.

Rudisha MISTARI tu, moja kila line. Hakuna namba. KISWAHILI TU."""
    else:
        if is_christian:
            examples = """EXAMPLES FOR CHRISTIAN NEWS:
- Megachurch news → authentic faith vs platform
- Gospel artist news → ministry of music, David's worship
- Persecution → Acts 5:41 rejoicing in suffering
- Revival → Acts 2 Pentecost outpouring
- Christian celebrity faith → bold testimony"""
        else:
            examples = """EXAMPLES FOR WORLD NEWS:
- Sports victory → running your spiritual race (1 Cor 9:24-25)
- Tragedy → God close to brokenhearted (Psalm 34:18)
- Tech/AI news → wisdom that surpasses understanding
- Celebrity death → life is a vapor (James 4:14)
- War/Crisis → Peace beyond understanding (Phil 4:7)"""

        prompt = f"""You are a gospel reel creator who connects current events to spiritual truth.

REAL HEADLINE TODAY:
"{trend_title}"
Category: {category}

Create a 25-30 second reel script that REFERENCES this headline and pivots to a powerful spiritual message.

STRUCTURE (8-9 lines):
1. Line 1 HOOK: Reference the headline naturally
2. Lines 2-7 BODY: Spiritual angle with specific verse or biblical character
3. Final line: "{cta}"

{examples}

RULES:
- Each line 5-9 words MAX
- Reference the actual news event in hook
- Include specific Bible verse or character
- Tone: {mood}
- Make people think and share

Return ONLY the script lines. No labels. No numbers."""

    print(f"  Generating spiritual angle for: {trend_title[:50]}...")

    raw = await generate_with_groq(prompt)
    if not raw:
        raw = await generate_with_gemini(prompt)
    if not raw:
        raw = await generate_with_openrouter(prompt)

    if not raw:
        return None

    lines = clean_ai_output(raw)

    if len(lines) < 4:
        return None
    if len(lines) > 10:
        lines = lines[:10]

    ts = datetime.now().strftime("%H%M%S")
    return {
        "id":               f"trend_{ts}",
        "title":            f"TRENDING: {trend_title[:60]}",
        "thumb":            trend_title.upper()[:40],
        "hook":             lines[0],
        "body":             lines[1:-1] if len(lines) > 2 else lines[1:],
        "cta":              lines[-1] if len(lines) > 1 else cta,
        "tags":             [niche, "trending", category],
        "mood":             mood,
        "voice":            variant["voice"],
        "rate":             variant["rate"],
        "pitch":            variant["pitch"],
        "style":            variant["style"],
        "duration_estimate": len(lines) * 3.0,
        "ai_generated":     True,
        "is_trending":      True,
        "trend_source":     trend.get("source", "unknown"),
        "trend_url":        trend.get("url", ""),
        "trend_category":   category,
        "is_christian":     is_christian,
        "cta_used":         cta,
    }


# ================================================================
# QUICK TEST
# ================================================================

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        
    async def test():
        collector = TrendCollector()
        trends = await collector.collect_all_trends()
        collector.show_summary()
        best = collector.pick_best_trends(count=3)
        print("\n=== TOP 3 -> SPIRITUAL REELS ===")
        for i, t in enumerate(best, 1):
            print(f"\n[{i}] {t['title'][:80]}")
            script = await trend_to_spiritual_script(t, niche="gospel")
            if script:
                print(f"    HOOK: {script['hook']}")
                print(f"    CTA : {script['cta']}")

    asyncio.run(test())
