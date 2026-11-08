# ============================================================
# VIDEOFACTORY - MEDIA DOWNLOADER
# Searches and downloads photos & videos from Pinterest & Pexels
# Auto-normalizes Pinterest images to high-resolution originals
# ============================================================

import os
import re
import json
import asyncio
import httpx
from pathlib import Path
from collections import Counter
from src.utils.retry import retry_async

# Niche to Pinterest Users mapping
NICHE_USERS = {
    "gospel":       ["dailyprayer", "crosscards", "christianquotes"],
    "prayer":       ["dailyprayer", "christianquotes"],
    "praise":       ["christianquotes", "crosscards"],
    "motivational": ["motivationalquotes", "successquotes", "mindsetquotes"],
    "tech":         ["motivationalquotes", "successquotes"],
    "nature":       ["successquotes", "motivationalquotes"],
    "quotes":       ["motivationalquotes", "successquotes", "mindsetquotes"]
}

def load_env():
    p = Path(".env")
    if not p.exists():
        return {}
    d = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d

ENV = load_env()
PEXELS_API_KEY = ENV.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = ENV.get("PIXABAY_API_KEY", "")

# Helper to download a single file
@retry_async(max_attempts=3, base_delay=1.0)
async def download_file(client, url, dest_path):
    r = await client.get(url, timeout=30)
    if r.status_code == 200:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(r.content)
        return True
    
    # Fallback for originals if 404/403: try 736x
    if r.status_code in [403, 404] and "/originals/" in url:
        fallback_url = url.replace("/originals/", "/736x/")
        r = await client.get(fallback_url, timeout=30)
        if r.status_code == 200:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(r.content)
            return True
            
    raise Exception(f"Failed download: {url} (Status: {r.status_code})")


# ============================================================
# PINTEREST DOWNLOADER
# ============================================================

def extract_pin_image_url(html_content):
    # Normalize escaped slashes
    norm = html_content.replace(r'\/', '/').replace(r'\u002f', '/').replace(r'\u002F', '/')
    # Find all i.pinimg.com URLs
    urls = re.findall(r'https://i\.pinimg\.com/[a-zA-Z0-9_/.-]+', norm)
    if not urls:
        return None
    
    # Extract the file name/hash suffix for each URL.
    paths = []
    url_map = {}
    for u in urls:
        parts = u.split('/')
        if len(parts) >= 5:
            # Reconstruct the subpath after the resolution directory
            subpath = '/'.join(parts[4:])
            paths.append(subpath)
            # Store the URL, preferring originals if available
            if parts[3] == 'originals':
                url_map[subpath] = u
            elif subpath not in url_map:
                url_map[subpath] = u
                
    if not paths:
        return None
        
    # Count frequencies of the subpaths
    counter = Counter(paths)
    most_common_subpath, count = counter.most_common(1)[0]
    
    # Construct/get the original URL
    best_url = url_map.get(most_common_subpath)
    if best_url:
        # Ensure it uses originals
        parts = best_url.split('/')
        parts[3] = 'originals'
        return '/'.join(parts)
    return None


class PinterestDownloader:
    
    def __init__(self, output_dir="assets/stock/pinterest"):
        self.output_dir = Path(output_dir)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    def parse_username(self, url):
        # Extract username from a URL like:
        # https://www.pinterest.com/username/boardname/ or https://www.pinterest.com/username/
        pattern = r"pinterest\.com/([^/]+)"
        match = re.search(pattern, url)
        if match:
            return match.group(1).strip("/")
        return None

    def parse_board_url(self, url):
        # e.g., https://www.pinterest.com/username/boardname/
        clean_url = url.split("?")[0].strip("/")
        pattern = r"pinterest\.com/([^/]+)/([^/]+)"
        match = re.search(pattern, clean_url)
        if match:
            return match.group(1), match.group(2)
        return None

    @retry_async(max_attempts=3, base_delay=1.0)
    async def fetch_pinterest_rss(self, url, limit=15):
        import xml.etree.ElementTree as ET
        import random
        pins = []
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
            r = await client.get(url)
            if r.status_code != 200:
                raise Exception(f"Pinterest RSS request failed (Status: {r.status_code})")
            
            try:
                root = ET.fromstring(r.text)
            except Exception as e:
                raise Exception(f"Pinterest RSS XML parse failed: {e}")
                
            items = root.findall(".//item")[:limit]
            for idx, item in enumerate(items):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                
                title = title_el.text if title_el is not None else ""
                link = link_el.text if link_el is not None else ""
                desc = desc_el.text if desc_el is not None else ""
                
                # Find the image URL from description using regex
                img_match = re.search(r'src=["\'](https://i\.pinimg\.com/[^"\']+)["\']', desc)
                img_url = img_match.group(1) if img_match else None
                
                if link:
                    pin_id_match = re.search(r"/pin/(\d+)", link)
                    pin_id = pin_id_match.group(1) if pin_id_match else f"pin_{idx}_{random.randint(1000, 9999)}"
                    
                    pins.append({
                        "id": pin_id,
                        "title": title,
                        "url": link,
                        "image_url": img_url
                    })
        return pins

    async def download_board_pins(self, username, board, limit=15):
        url = f"https://www.pinterest.com/{username}/{board}.rss"
        print(f"Fetching Pinterest board RSS: {url}...")
        try:
            pins = await self.fetch_pinterest_rss(url, limit=limit)
        except Exception as e:
            print(f"  Error fetching Pinterest RSS: {e}")
            pins = []
        
        if not pins:
            print("  No pins found for board via RSS. Switching to headless Playwright board scraper...")
            pins = await self.scrape_board_pins_playwright(username, board, limit=limit)
            
        if not pins:
            print("  No pins found for board via RSS or Playwright.")
            return 0
            
        print(f"  Found {len(pins)} pins via RSS. Downloading up to {limit}...")
        
        tasks = []
        downloaded_count = 0
        
        for idx, pin in enumerate(pins[:limit]):
            pin_id = pin["id"]
            custom_fn = f"{username}_{board}_{pin_id}"
            
            exists = False
            for ext in [".mp4", ".jpg", ".jpeg", ".png", ".webp"]:
                if (self.output_dir / f"{custom_fn}{ext}").exists():
                    exists = True
                    break
            
            if exists:
                downloaded_count += 1
                continue
                
            tasks.append(self.download_single_pin(pin["url"], custom_filename=custom_fn))
            
        if tasks:
            results = await asyncio.gather(*tasks)
            downloaded_count += sum(1 for r in results if r)
            
        print(f"  Successfully downloaded/verified {downloaded_count} board items.")
        return downloaded_count

    async def download_user_pins(self, username, limit=15):
        url = f"https://www.pinterest.com/{username}/feed.rss"
        print(f"Fetching Pinterest user RSS: {url}...")
        pins = await self.fetch_pinterest_rss(url, limit=limit)
        
        if not pins:
            print("  No pins found for user via RSS.")
            return 0
            
        print(f"  Found {len(pins)} pins via RSS. Downloading up to {limit}...")
        
        tasks = []
        downloaded_count = 0
        
        for idx, pin in enumerate(pins[:limit]):
            pin_id = pin["id"]
            custom_fn = f"{username}_{pin_id}"
            
            exists = False
            for ext in [".mp4", ".jpg", ".jpeg", ".png", ".webp"]:
                if (self.output_dir / f"{custom_fn}{ext}").exists():
                    exists = True
                    break
                    
            if exists:
                downloaded_count += 1
                continue
                
            tasks.append(self.download_single_pin(pin["url"], custom_filename=custom_fn))
            
        if tasks:
            results = await asyncio.gather(*tasks)
            downloaded_count += sum(1 for r in results if r)
            
        print(f"  Successfully downloaded/verified {downloaded_count} user items.")
        return downloaded_count

    async def download_single_pin(self, pin_id_or_url, custom_filename=None):
        # 1. Parse or construct target URL
        pin_url = pin_id_or_url.strip()
        if not pin_url.startswith("http"):
            pin_url = f"https://www.pinterest.com/pin/{pin_id_or_url}/"
            pin_id = pin_id_or_url
        else:
            pin_id_match = re.search(r"/pin/(\d+)", pin_url)
            if pin_id_match:
                pin_id = pin_id_match.group(1)
            else:
                pin_id = "single_pin"

        print(f"Downloading single Pinterest pin: {pin_id}...")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine the base output filename
        base_name = custom_filename if custom_filename else f"pinterest_{pin_id}"
        
        # Try Playwright scraper first for high-quality video/image extraction
        print("  Attempting media extraction with headless Playwright...")
        media_url, media_type = await self.scrape_single_pin_media_playwright(pin_url)
        if media_url:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
                ext = ".mp4" if media_type == "video" else ".jpg"
                if "?" in media_url:
                    ext = media_url.split("?")[0][-4:]
                    if ext not in [".mp4", ".jpg", ".jpeg", ".png", ".webp"]:
                        ext = ".mp4" if media_type == "video" else ".jpg"
                dest_file = self.output_dir / f"{base_name}{ext}"
                
                # If image is an original from pinimg, normalize resolution
                if media_type == "image":
                    parts = media_url.split('/')
                    if len(parts) >= 5:
                        parts[3] = 'originals'
                        media_url = '/'.join(parts)
                
                try:
                    success = await download_file(client, media_url, dest_file)
                except Exception as e:
                    print(f"  Playwright download failed: {e}")
                    success = False
                if success:
                    print(f"  Successfully downloaded {media_type} using Playwright to {dest_file.name}")
                    return 1
                    
        # 2. Try yt-dlp first (it extracts and merges video stream automatically)
        print(f"  Attempting video download with yt-dlp...")
        try:
            output_template = str(self.output_dir / f"{base_name}.%(ext)s")
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "-o", output_template,
                "--no-playlist",
                "--merge-output-format", "mp4",
                pin_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                dest_file = self.output_dir / f"{base_name}.mp4"
                if dest_file.exists():
                    print(f"  Successfully downloaded video to {dest_file.name}")
                    return 1
                else:
                    for file in self.output_dir.glob(f"{base_name}.*"):
                        print(f"  Successfully downloaded to {file.name}")
                        return 1
            else:
                stderr_str = stderr.decode('utf-8', errors='ignore')
                print(f"  yt-dlp did not find video formats: {stderr_str.strip().splitlines()[-1] if stderr_str.strip() else 'Unknown error'}")
        except Exception as e:
            print(f"  yt-dlp execution error: {e}")

        # 3. Fallback: treat as image pin
        print(f"  Falling back to image download for pin: {pin_id}...")
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                r = await client.get(pin_url, timeout=15)
                if r.status_code != 200:
                    print(f"  Failed to fetch Pin HTML (Status: {r.status_code})")
                    return 0
                
                img_url = extract_pin_image_url(r.text)
                if not img_url:
                    print("  Could not extract image URL from Pin HTML.")
                    return 0
                
                ext = Path(img_url).suffix or ".jpg"
                if "?" in ext:
                    ext = ext.split("?")[0]
                
                dest_img = self.output_dir / f"{base_name}{ext}"
                if dest_img.exists():
                    print(f"  Image already exists at {dest_img.name}")
                    return 1
                
                success = await download_file(client, img_url, dest_img)
                if success:
                    print(f"  Successfully downloaded image to {dest_img.name}")
                    return 1
            except Exception as e:
                print(f"  Failed to download image pin: {e}")
                
        return 0

    async def download_by_niche(self, niche, limit=10, custom_dir=None):
        users = NICHE_USERS.get(niche, NICHE_USERS["gospel"])
        # Pick one random user profile to download from to maintain variety
        import random
        username = random.choice(users)
        # Update output directory for the niche
        if custom_dir:
            self.output_dir = Path(custom_dir)
        else:
            self.output_dir = Path("assets/stock/pinterest") / niche
        return await self.download_user_pins(username, limit=limit)

    async def scrape_board_pins_playwright(self, username, board, limit=15):
        url = f"https://www.pinterest.com/{username}/{board}/"
        print(f"Scraping Pinterest board via Playwright: {url}...")
        
        pins = []
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Scroll to trigger lazy loading
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)
                
                anchors = await page.query_selector_all("a")
                seen_pin_ids = set()
                
                for anchor in anchors:
                    href = await anchor.get_attribute("href")
                    if href and "/pin/" in href:
                        pin_id_match = re.search(r"/pin/(\d+)", href)
                        if pin_id_match:
                            pin_id = pin_id_match.group(1)
                            if pin_id not in seen_pin_ids:
                                seen_pin_ids.add(pin_id)
                                img = await anchor.query_selector("img")
                                img_url = None
                                if img:
                                    img_url = await img.get_attribute("src")
                                
                                pins.append({
                                    "id": pin_id,
                                    "url": f"https://www.pinterest.com/pin/{pin_id}/",
                                    "image_url": img_url
                                })
                                
                                if len(pins) >= limit:
                                    break
                await browser.close()
        except Exception as e:
            print(f"  Playwright board scrape failed: {e}")
        return pins

    async def scrape_single_pin_media_playwright(self, pin_url):
        print(f"  Scraping single Pin via Playwright: {pin_url}...")
        media_url = None
        media_type = "image"
        
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                await page.goto(pin_url, timeout=30000)
                await page.wait_for_timeout(3000)
                
                # 1. Try to find a <video> element
                video_el = await page.query_selector("video")
                if video_el:
                    video_src = await video_el.get_attribute("src")
                    if video_src:
                        media_url = video_src
                        media_type = "video"
                        print(f"    Found video source in DOM: {media_url[:60]}...")
                
                # 2. If no video, look for the highest resolution image
                if not media_url:
                    og_image = await page.query_selector("meta[property='og:image']")
                    if og_image:
                        og_src = await og_image.get_attribute("content")
                        if og_src:
                            media_url = og_src
                            media_type = "image"
                            print(f"    Found image source in og:image: {media_url[:60]}...")
                
                # 3. Fallback: parse json content from script tag (ld+json)
                if not media_url:
                    scripts = await page.query_selector_all("script[type='application/ld+json']")
                    for script in scripts:
                        text = await script.inner_text()
                        try:
                            data = json.loads(text)
                            if isinstance(data, dict):
                                if "contentUrl" in data:
                                    media_url = data["contentUrl"]
                                    media_type = "video"
                                    break
                                elif "image" in data:
                                    media_url = data["image"]
                                    media_type = "image"
                                    break
                        except:
                            pass
                            
                await browser.close()
        except Exception as e:
            print(f"  Playwright pin media scrape failed: {e}")
            
        return media_url, media_type


# ============================================================
# PEXELS & PIXABAY STOCK DOWNLOADER
# ============================================================

class StockDownloader:

    def __init__(self):
        self.headers = {}
        if PEXELS_API_KEY:
            self.headers["Authorization"] = PEXELS_API_KEY

    @retry_async(max_attempts=3, base_delay=1.0)
    async def download_pexels_videos(self, query, limit=5, folder="nature"):
        if not PEXELS_API_KEY:
            print("ERROR: PEXELS_API_KEY is not set in your .env file!")
            return 0
            
        url = f"https://api.pexels.com/videos/search?query={query}&per_page={limit*2}&orientation=portrait"
        dest_dir = Path("assets/stock") / folder
        
        print(f"Searching Pexels for vertical videos: '{query}'...")
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            r = await client.get(url, timeout=15)
            if r.status_code != 200:
                raise Exception(f"Pexels API status {r.status_code}: {r.text}")
                
            data = r.json()
            videos = data.get("videos", [])
            if not videos:
                print("  No videos found for query.")
                return 0
                
            print(f"  Found {len(videos)} videos. Downloading {limit} portrait clips...")
            
            tasks = []
            downloaded_count = 0
            
            for idx, v in enumerate(videos):
                if downloaded_count >= limit:
                    break
                    
                video_files = v.get("video_files", [])
                best_file = None
                
                # Filter for vertical and HD
                for f in video_files:
                    w = f.get("width") or 0
                    h = f.get("height") or 0
                    if h > w:
                        # Prefer standard HD (1080p height) or slightly lower for faster download
                        if 720 <= h <= 1920:
                            best_file = f
                            break
                            
                if not best_file and video_files:
                    best_file = video_files[0]
                    
                if not best_file:
                    continue
                    
                video_url = best_file.get("link")
                video_id = v.get("id") or f"v_{idx}"
                dest = dest_dir / f"pexels_{video_id}.mp4"
                
                if dest.exists():
                    downloaded_count += 1
                    continue
                    
                tasks.append(download_file(client, video_url, dest))
                downloaded_count += 1
                
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success_count = sum(1 for r in results if r is True)
                print(f"  Downloaded {success_count} vertical videos to {dest_dir.name}/")
                return success_count
            
            return downloaded_count

    @retry_async(max_attempts=3, base_delay=1.0)
    async def download_pexels_photos(self, query, limit=8, folder="pinterest"):
        if not PEXELS_API_KEY:
            print("ERROR: PEXELS_API_KEY is not set in your .env file!")
            return 0
            
        url = f"https://api.pexels.com/v1/search?query={query}&per_page={limit}&orientation=portrait"
        dest_dir = Path("assets/stock") / folder
        
        print(f"Searching Pexels for portrait photos: '{query}'...")
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            r = await client.get(url, timeout=15)
            if r.status_code != 200:
                raise Exception(f"Pexels API status {r.status_code}: {r.text}")
                
            data = r.json()
            photos = data.get("photos", [])
            if not photos:
                print("  No photos found for query.")
                return 0
                
            print(f"  Found {len(photos)} photos. Downloading {limit} portrait photos...")
            
            tasks = []
            downloaded_count = 0
            
            for idx, p in enumerate(photos):
                img_url = p.get("src", {}).get("large2x") or p.get("src", {}).get("original")
                if not img_url:
                    continue
                    
                photo_id = p.get("id") or f"p_{idx}"
                ext = Path(img_url).suffix or ".jpg"
                if "?" in ext:
                    ext = ext.split("?")[0]
                    
                dest = dest_dir / f"pexels_photo_{photo_id}{ext}"
                
                if dest.exists():
                    downloaded_count += 1
                    continue
                    
                tasks.append(download_file(client, img_url, dest))
                
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success_count = sum(1 for r in results if r is True)
                print(f"  Downloaded {success_count} photos to {dest_dir.name}/")
                return success_count
            
            return downloaded_count


# ============================================================
# DUAL SEARCH RUNNER
# ============================================================

async def run_pinterest_download(target, limit=15, folder=None):
    p_down = PinterestDownloader()
    if folder:
        if folder.startswith("assets/stock"):
            p_down.output_dir = Path(folder)
        else:
            p_down.output_dir = Path("assets/stock") / folder

    target_str = target.strip()
    if "/pin/" in target_str or "pin.it" in target_str or target_str.isdigit():
        if not folder:
            p_down.output_dir = Path("assets/stock/pinterest/single_pins")
        await p_down.download_single_pin(target_str)
    elif "/" in target_str or "pinterest.com" in target_str:
        res = p_down.parse_board_url(target_str)
        if res:
            username, board = res
            if not folder:
                p_down.output_dir = Path("assets/stock/pinterest") / board
            await p_down.download_board_pins(username, board, limit=limit)
        else:
            print("Invalid Pinterest board URL. Example: https://www.pinterest.com/crosscards/bible-verses/")
    else:
        # Treat as niche name
        await p_down.download_by_niche(target_str, limit=limit, custom_dir=p_down.output_dir if folder else None)

async def run_pexels_download(query, limit=5, media_type="video", folder="nature"):
    downloader = StockDownloader()
    if media_type == "video":
        await downloader.download_pexels_videos(query, limit=limit, folder=folder)
    else:
        await downloader.download_pexels_photos(query, limit=limit, folder=folder)

async def run_music_download(target, limit=1, folder=None):
    from pathlib import Path
    import asyncio
    
    # Niche to query mapping
    queries = {
        "gospel":       "royalty free instrumental worship music",
        "prayer":       "calm ambient prayer background music instrumental royalty free",
        "praise":       "uplifting praise worship instrumental beat royalty free",
        "motivational": "cinematic motivational background music instrumental royalty free",
        "tech":         "ambient cinematic corporate electronic background music royalty free",
        "swahili":      "african acoustic guitar instrumental background music royalty free",
        "ambient":      "calm ambient background music drone royalty free",
    }
    
    query = queries.get(target.lower(), target)
    
    # Target folder: assets/music/{niche}
    if folder:
        music_dir = Path("assets/music") / folder
    elif target.lower() in queries:
        music_dir = Path("assets/music") / target.lower()
    else:
        music_dir = Path("assets/music") / "general"
        
    music_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Searching and downloading background music for: '{target}'...")
    print(f"  Query: {query}")
    print(f"  Saving to: {music_dir}")
    
    output_template = str(music_dir / "%(title)s.%(ext)s")
    
    print(f"  Running yt-dlp extraction...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-o", output_template,
            "--no-playlist",
            "--extract-audio",
            "--audio-format", "mp3",
            f"ytsearch{limit}:{query}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            print(f"  Successfully downloaded {limit} background music track(s) to assets/music/{music_dir.name}/")
            return limit
        else:
            stderr_str = stderr.decode('utf-8', errors='ignore')
            print(f"  yt-dlp failed to download music: {stderr_str.strip().splitlines()[-1] if stderr_str.strip() else 'Unknown error'}")
    except Exception as e:
        print(f"  yt-dlp music execution error: {e}")
        
    return 0
