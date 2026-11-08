# -*- coding: utf-8 -*-
"""
MWIJAY DAILY BRIEF
==================
Daily multi-interest trends report for Mzee.

Scrapes fresh trends across all of Mwijay's territories:
  1. 🎵 Gospel/Amapiano music (Piano Sifa)
  2. 💻 Tech / AI / dev
  3. 🇹🇿 Tanzania / East Africa news
  4. ✝️ Christian / faith news
  5. 💼 Business / African startups / creator economy
  6. � Design / UI-UX / shadcn / premium web
  7. 💎 Crypto / markets / African fintech
  8. 🎬 YouTube / TikTok content trends

FREE: All RSS sources, no API keys. Cloudflare Llama 3.3 70B for
the "what's rising" angle analysis (optional — falls back to scoring).

Usage:
    python mwijay_daily_brief.py            # all 8 territories
    python mwijay_daily_brief.py gospel     # one territory only
    python mwijay_daily_brief.py --top 5    # show top 5 per territory
"""

import asyncio
import httpx
import json
import re
import html
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree as ET

HTTP_TIMEOUT = 15
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# TERRITORY CONFIG
# ============================================================

TERRITORIES = {
    "gospel": {
        "icon": "🎵",
        "title": "GOSPEL AMAPIANO / PIANO SIFA",
        "feeds": [
            ("https://news.google.com/rss/search?q=gospel+amapiano&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://www.christianpost.com/rss/news.xml", "christian_post"),
            ("https://www.premierchristian.news/feed/", "premier"),
            ("https://news.google.com/rss/search?q=tanzania+gospel+music&hl=en-US&gl=US&ceid=US:en", "google"),
        ],
        "keywords": ["amapiano", "gospel", "worship", "praise", "jesus", "tanzania", "dar es salaam", "choir", "anthem", "piano sifa", "mwamba"],
    },
    "tech": {
        "icon": "💻",
        "title": "TECH / AI / DEV",
        "feeds": [
            ("https://news.google.com/rss/search?q=AI+agents+2026&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=nextjs+react+shadcn&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://hnrss.org/frontpage", "hackernews"),
            ("https://www.techcrunch.com/feed/", "techcrunch"),
            ("https://news.google.com/rss/search?q=openai+anthropic+claude&hl=en-US&gl=US&ceid=US:en", "google"),
        ],
        "keywords": ["ai", "agent", "llm", "claude", "gpt", "nextjs", "react", "shadcn", "vercel", "github", "copilot", "cursor", "typescript"],
    },
    "tanzania": {
        "icon": "🇹🇿",
        "title": "TANZANIA / EAST AFRICA",
        "feeds": [
            ("https://news.google.com/rss/search?q=tanzania+news&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=daily+news+Dar+es+Salaam&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=east+africa+startup+tech&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://www.thecitizen.co.tz/rss/", "thecitizen"),
        ],
        "keywords": ["tanzania", "dar es salaam", "dodoma", "zanzibar", "arusha", "kilimanjaro", "tbs", "bot", "ubongo", "tanzanite", "serengeti", "bagamoyo"],
    },
    "faith": {
        "icon": "✝️",
        "title": "CHRISTIAN / FAITH",
        "feeds": [
            ("https://www.christianpost.com/rss/news.xml", "christian_post"),
            ("https://www.charismamag.com/site/feed", "charisma"),
            ("https://www.biblegateway.com/blog/feed/", "biblegateway"),
            ("https://news.google.com/rss/search?q=revival+christian+africa&hl=en-US&gl=US&ceid=US:en", "google"),
        ],
        "keywords": ["christ", "jesus", "church", "revival", "pastor", "worship", "prayer", "bible", "holy spirit", "salvation", "gospel"],
    },
    "business": {
        "icon": "💼",
        "title": "BUSINESS / STARTUPS / CREATOR ECONOMY",
        "feeds": [
            ("https://news.google.com/rss/search?q=african+startup+funding&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=creator+economy+2026&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://techcrunch.com/category/startups/feed/", "techcrunch_startups"),
            ("https://news.google.com/rss/search?q=passive+income+online&hl=en-US&gl=US&ceid=US:en", "google"),
        ],
        "keywords": ["startup", "funding", "investment", "creator", "monetize", "saas", "mvp", "y combinator", "africa", "tanzania"],
    },
    "design": {
        "icon": "🎨",
        "title": "DESIGN / UI-UX / PREMIUM WEB",
        "feeds": [
            ("https://news.google.com/rss/search?q=shadcn+ui+design&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=react+bits+premium+ui&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://www.smashingmagazine.com/feed/", "smashing"),
        ],
        "keywords": ["shadcn", "tailwind", "framer motion", "reactbits", "design system", "ui", "ux", "premium", "figma", "landing page"],
    },
    "crypto": {
        "icon": "💎",
        "title": "CRYPTO / MARKETS / AFRICAN FINTECH",
        "feeds": [
            ("https://news.google.com/rss/search?q=bitcoin+ethereum+2026&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=african+fintech+mobile+money&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://www.coindesk.com/arc/outboundfeeds/rss/", "coindesk"),
        ],
        "keywords": ["bitcoin", "ethereum", "crypto", "stablecoin", "mpesa", "tigo pesa", "mobile money", "flutterwave", "fintech"],
    },
    "content": {
        "icon": "🎬",
        "title": "YOUTUBE / TIKTOK / CONTENT TRENDS",
        "feeds": [
            ("https://news.google.com/rss/search?q=youtube+trending+2026&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=tiktok+creator+algorithm&hl=en-US&gl=US&ceid=US:en", "google"),
            ("https://news.google.com/rss/search?q=short+form+video+strategy&hl=en-US&gl=US&ceid=US:en", "google"),
        ],
        "keywords": ["youtube", "tiktok", "shorts", "reels", "algorithm", "monetize", "viral", "creator fund"],
    },
}


# ============================================================
# RSS SCRAPER
# ============================================================

def clean_text(t: str) -> str:
    if not t:
        return ""
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def parse_rss(xml_text: str, source: str, limit: int = 30) -> list[dict]:
    """Parse RSS XML → list of {title, url, source, published}."""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out

    channel = root.find("channel")
    if channel is None:
        return out

    items = channel.findall("item")
    for item in items[:limit]:
        title = clean_text(item.findtext("title", ""))
        link = clean_text(item.findtext("link", ""))
        pub = clean_text(item.findtext("pubDate", ""))
        if title and link:
            out.append({
                "title": title,
                "url": link,
                "source": source,
                "published": pub,
            })
    return out


async def fetch_feed(client: httpx.AsyncClient, url: str, source: str) -> list[dict]:
    try:
        r = await client.get(url, timeout=HTTP_TIMEOUT, follow_redirects=True)
        if r.status_code == 200:
            return parse_rss(r.text, source)
    except Exception as e:
        # Silently skip — we want the report even if some feeds fail
        pass
    return []


# ============================================================
# TREND COLLECTOR + SCORER
# ============================================================

class MzeeDailyBrief:
    def __init__(self):
        self.territory_data: dict[str, list[dict]] = {}
        self.timestamp = datetime.now()

    async def collect_all(self, territories: list[str] | None = None):
        """Scrape trends for all (or specific) territories in parallel."""
        targets = territories or list(TERRITORIES.keys())
        async with httpx.AsyncClient(headers=HTTP_HEADERS) as client:
            tasks = []
            for t_name in targets:
                cfg = TERRITORIES[t_name]
                for url, source in cfg["feeds"]:
                    tasks.append((t_name, fetch_feed(client, url, source)))

            results = await asyncio.gather(*[t[1] for t in tasks])
            for (t_name, _), items in zip(tasks, results):
                self.territory_data.setdefault(t_name, []).extend(items)

    def dedupe(self):
        """Remove duplicate titles within each territory."""
        for t_name, items in self.territory_data.items():
            seen = set()
            unique = []
            for item in items:
                key = item["title"].lower()[:80]
                if key not in seen:
                    seen.add(key)
                    unique.append(item)
            self.territory_data[t_name] = unique

    def score_and_rank(self, top_n: int = 7):
        """Score by keyword relevance, return top N per territory."""
        for t_name, items in self.territory_data.items():
            cfg = TERRITORIES[t_name]
            kws = [k.lower() for k in cfg["keywords"]]
            for item in items:
                text = (item["title"] + " " + item.get("source", "")).lower()
                score = sum(2 for k in kws if k in text)
                # Boost recent items
                item["score"] = score
            items.sort(key=lambda x: x["score"], reverse=True)
            self.territory_data[t_name] = items[:top_n]

    def format_report(self, top_n: int = 7) -> str:
        """Build a WhatsApp/Telegram-friendly daily brief."""
        lines = []
        date_str = self.timestamp.strftime("%a, %d %b %Y · %H:%M")
        lines.append("=" * 60)
        lines.append(f"🌍 MWIJAY DAILY BRIEF — {date_str}")
        lines.append("=" * 60)
        lines.append("")

        # Top movers across all territories (global hot)
        all_items = []
        for t_name, items in self.territory_data.items():
            cfg = TERRITORIES[t_name]
            for item in items[:3]:  # top 3 per territory
                all_items.append({**item, "_territory": cfg["title"], "_icon": cfg["icon"]})
        all_items.sort(key=lambda x: x.get("score", 0), reverse=True)

        lines.append("🔥 TOP MOVERS (across all interests)")
        lines.append("-" * 60)
        for i, item in enumerate(all_items[:5], 1):
            lines.append(f"{i}. [{item['_icon']}] {item['title'][:90]}")
            lines.append(f"   ↳ {item['_territory']} · {item['source']}")
        lines.append("")

        # Per-territory breakdown
        for t_name, items in self.territory_data.items():
            cfg = TERRITORIES[t_name]
            if not items:
                continue
            lines.append(f"{cfg['icon']} {cfg['title']}")
            lines.append("-" * 60)
            for i, item in enumerate(items[:top_n], 1):
                title = item["title"][:100]
                lines.append(f"{i}. {title}")
                lines.append(f"   📰 {item['source']}")
            lines.append("")

        lines.append("=" * 60)
        total = sum(len(v) for v in self.territory_data.values())
        lines.append(f"📊 Total trends scraped: {total}")
        lines.append(f"⏰ Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def save_report(self, content: str):
        """Save to Mwijay's daily briefs folder."""
        out_dir = Path(r"C:\Users\MWIJAY TECH\Music\Piano_Sifa\Daily_Briefs")
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{self.timestamp.strftime('%Y%m%d_%H%M')}_daily_brief.md"
        out_path = out_dir / fname
        out_path.write_text(content, encoding="utf-8")

        # Also save JSON for programmatic access
        json_path = out_dir / f"{self.timestamp.strftime('%Y%m%d_%H%M')}_daily_brief.json"
        json_path.write_text(json.dumps({
            "generated_at": self.timestamp.isoformat(),
            "territories": self.territory_data,
        }, indent=2), encoding="utf-8")

        return out_path, json_path


# ============================================================
# MAIN
# ============================================================

async def main():
    import sys

    # Parse args
    only_territory = None
    top_n = 7
    args = sys.argv[1:]
    if args:
        if args[0] in TERRITORIES:
            only_territory = [args[0]]
        elif args[0] == "--top" and len(args) > 1:
            try:
                top_n = int(args[1])
            except ValueError:
                pass

    brief = MzeeDailyBrief()
    print(f"⏳ Scraping trends for {'ALL' if not only_territory else only_territory[0]}...\n")
    await brief.collect_all(only_territory)
    brief.dedupe()
    brief.score_and_rank(top_n=top_n)

    report = brief.format_report(top_n=top_n)
    print(report)

    md_path, json_path = brief.save_report(report)
    print(f"\n💾 Saved: {md_path}")
    print(f"💾 Saved: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
