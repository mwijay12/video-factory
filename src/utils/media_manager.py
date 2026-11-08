# ============================================================
# VIDEOFACTORY - MEDIA MANAGER
# Scans local stock folders for videos and images
# Works fully in DATA SAVER MODE - zero download needed
# Picks best media mix for reels: 7-15 items
# ============================================================

import os
import random
import json
from pathlib import Path

from config.settings import (
    STOCK_PATHS,
    VIDEO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    MIN_MEDIA_ITEMS,
    MAX_MEDIA_ITEMS,
    TARGET_MEDIA_ITEMS,
    USE_VIDEOS,
    USE_IMAGES,
    MODE,
    NICHE,
    NICHE_CONFIG,
)


# ============================================================
# MEDIA ITEM - Single piece of media
# ============================================================

class MediaItem:

    def __init__(self, path, media_type, folder_name):
        self.path = Path(path)
        self.media_type = media_type        # "video" or "image"
        self.folder_name = folder_name      # gospel, nature, etc
        self.filename = self.path.name
        self.size_mb = round(self.path.stat().st_size / (1024 * 1024), 2)

    def __repr__(self):
        clean_name = self.filename.encode("ascii", "replace").decode("ascii")
        return f"[{self.media_type.upper()}] {clean_name} ({self.size_mb}MB)"


# ============================================================
# MEDIA MANAGER CLASS
# ============================================================

class MediaManager:

    def __init__(self, niche=None, mode=None):
        self.niche = niche or NICHE
        self.mode = mode or MODE
        self.all_media = []
        self.videos = []
        self.images = []
        self._scanned = False

    def scan(self):
        self.all_media = []
        self.videos = []
        self.images = []
        seen_paths = set()

        active_folders = []
        if "," in str(self.niche):
            for part in str(self.niche).split(","):
                part = part.strip()
                niche_conf = NICHE_CONFIG.get(part, {})
                f_list = niche_conf.get("folders", [part])
                for f in f_list:
                    if f not in active_folders:
                        active_folders.append(f)
                if part not in active_folders:
                    active_folders.append(part)
        else:
            niche_conf = NICHE_CONFIG.get(self.niche, {})
            active_folders = list(niche_conf.get("folders", [self.niche, "nature"]))
            if self.niche not in active_folders:
                active_folders.append(self.niche)

        # Always include fallback rich folders to ensure vast clip variety
        for fallback_folder in ["nature", "dance", "pinterest", "gospel", "uploaded_queue", "vibe"]:
            if fallback_folder not in active_folders:
                active_folders.append(fallback_folder)

        print("")
        print("=" * 55)
        print("MEDIA MANAGER - Scanning local stock folders (Recursive)")
        print(f"Niche:   {self.niche}")
        print(f"Mode:    {self.mode}")
        print(f"Folders: {active_folders}")
        print("=" * 55)

        for folder_name in active_folders:
            folder_path = STOCK_PATHS.get(folder_name)
            if not folder_path:
                folder_path = Path("assets/stock") / folder_name

            folder_path = Path(folder_path)
            if not folder_path.exists():
                folder_path.mkdir(parents=True, exist_ok=True)
                continue

            found = 0
            # Recursively scan all files in folder and its subdirectories
            try:
                all_files = [p for p in folder_path.rglob("*") if p.is_file()]
            except Exception:
                all_files = [p for p in folder_path.iterdir() if p.is_file()]

            for f in all_files:
                if f.name.startswith(".") or f.name.startswith("~"):
                    continue

                abs_path_str = str(f.resolve())
                if abs_path_str in seen_paths:
                    continue

                ext = f.suffix.lower()

                if USE_VIDEOS and ext in VIDEO_EXTENSIONS:
                    seen_paths.add(abs_path_str)
                    item = MediaItem(f, "video", folder_name)
                    self.videos.append(item)
                    self.all_media.append(item)
                    found += 1

                elif USE_IMAGES and ext in IMAGE_EXTENSIONS:
                    seen_paths.add(abs_path_str)
                    item = MediaItem(f, "image", folder_name)
                    self.images.append(item)
                    self.all_media.append(item)
                    found += 1

            if found > 0:
                print(f"  {folder_name:15} -> {found} files found (recursive)")

        self._scanned = True

        print("=" * 55)
        print(f"  Total Unique Videos:  {len(self.videos)}")
        print(f"  Total Unique Images:  {len(self.images)}")
        print(f"  Total Unique Media:   {len(self.all_media)}")
        print("=" * 55)
        print("")

    def has_media(self):
        if not self._scanned:
            self.scan()
        return len(self.all_media) > 0

    def _detect_character_folders(self, script):
        """Scans the script title and text to find if a biblical character is referenced.
        Returns a list of matching subfolder Paths if they exist."""
        if not script:
            return []

        # List of common biblical figures to scan for
        characters = [
            "david", "goliath", "moses", "mary", "jesus", "peter", "samson",
            "noah", "joseph", "daniel", "esther", "abraham", "isaac", "jacob",
            "job", "paul", "solomon", "elijah", "gideon", "jonah", "ruth",
            "adam", "eve", "samuel", "gabriel", "john"
        ]

        text_to_scan = ""
        # script can be a dict or a string or a list of lines
        if isinstance(script, dict):
            text_to_scan += script.get("title", "") + " "
            text_to_scan += script.get("hook", "") + " "
            body = script.get("body", [])
            if isinstance(body, list):
                text_to_scan += " ".join(body)
            elif isinstance(body, str):
                text_to_scan += body
            text_to_scan += " " + script.get("cta", "")
        elif isinstance(script, list):
            text_to_scan = " ".join(script)
        elif isinstance(script, str):
            text_to_scan = script

        text_to_scan = text_to_scan.lower()
        import re

        matched = []
        for char in characters:
            if re.search(rf"\b{char}\b", text_to_scan):
                matched.append(char)

        if not matched:
            return []

        # Find folders matching these characters
        # Check folders like:
        # assets/stock/pinterest/characters/{char}
        # assets/stock/pinterest/{char}
        # assets/stock/characters/{char}
        # assets/stock/{char}
        found_folders = []
        base_paths = [
            Path("assets/stock/pinterest/characters"),
            Path("assets/stock/pinterest"),
            Path("assets/stock/characters"),
            Path("assets/stock")
        ]

        for char in matched:
            for base in base_paths:
                char_dir = base / char
                if char_dir.exists() and char_dir.is_dir():
                    found_folders.append((char, char_dir))
                    break

        return found_folders

    def get_unique_videos(self, count=None, shuffle=True):
        """Returns a deduplicated list of unique video items."""
        if not self._scanned:
            self.scan()
        pool = list(self.videos)
        if shuffle:
            random.shuffle(pool)
        if count is not None:
            return pool[:count]
        return pool

    def pick_media_for_reel(self, count=None, shuffle=True, script=None):
        if not self._scanned:
            self.scan()

        if not self.all_media:
            print("WARNING: No local media found.")
            print("Add videos/images to your stock folders:")
            for name, path in STOCK_PATHS.items():
                print(f"  {path}")
            return []

        # Target enough unique clips for high-density 1.5s-2.5s timeline cuts
        # For a standard 30-60s reel, 35-50 distinct clips ensure 100% zero-repeat timeline cuts
        base_count = count or TARGET_MEDIA_ITEMS
        target = max(35, base_count * 3)
        target = min(len(self.all_media), target)

        # 1. Try SEMANTIC B-ROLL matching first
        semantic_media = []
        if script and isinstance(script, dict) and "broll_keywords" in script:
            bk = script["broll_keywords"]
            hook_kws = bk.get("hook", [])
            body_kws = bk.get("body", [])
            cta_kws = bk.get("cta", [])
            
            line_kws = []
            if hook_kws:
                line_kws.append(hook_kws)
            else:
                line_kws.append([])
                
            if isinstance(body_kws, list):
                for bk_item in body_kws:
                    if isinstance(bk_item, list):
                        line_kws.append(bk_item)
                    elif isinstance(bk_item, str):
                        line_kws.append([bk_item])
                    else:
                        line_kws.append([])
            else:
                line_kws.append([])
                
            if cta_kws:
                line_kws.append(cta_kws)
            else:
                line_kws.append([])
                
            print("")
            print("=" * 60)
            print(f"SEMANTIC B-ROLL MATCHING - Found {len(line_kws)} line keyword queries")
            print("=" * 60)
            
            for idx, kws in enumerate(line_kws):
                query = " ".join(kws).strip()
                if not query:
                    semantic_media.append(None)
                    continue
                    
                broll_dir = self._download_semantic_broll(query)
                item = None
                if broll_dir and broll_dir.exists():
                    files = [f for f in broll_dir.iterdir() if f.is_file()]
                    if files:
                        chosen_file = random.choice(files)
                        ext = chosen_file.suffix.lower()
                        media_type = "video" if ext in VIDEO_EXTENSIONS else "image"
                        item = MediaItem(chosen_file, media_type, f"autobroll/{broll_dir.name}")
                        print(f"  Line {idx+1} query '{query}' -> matched: {chosen_file.name}")
                semantic_media.append(item)
            print("=" * 60)
            print("")

        # 2. Try BIBLICAL CHARACTER prioritizing second
        detected_chars = []
        if script:
            characters = [
                "david", "goliath", "moses", "mary", "jesus", "peter", "samson",
                "noah", "joseph", "daniel", "esther", "abraham", "isaac", "jacob",
                "job", "paul", "solomon", "elijah", "gideon", "jonah", "ruth",
                "adam", "eve", "samuel", "gabriel", "john"
            ]
            text_to_scan = ""
            if isinstance(script, dict):
                text_to_scan += script.get("title", "") + " "
                text_to_scan += script.get("hook", "") + " "
                body = script.get("body", [])
                if isinstance(body, list):
                    text_to_scan += " ".join(body)
                elif isinstance(body, str):
                    text_to_scan += body
                text_to_scan += " " + script.get("cta", "")
            elif isinstance(script, list):
                text_to_scan = " ".join(script)
            elif isinstance(script, str):
                text_to_scan = script
                
            text_to_scan = text_to_scan.lower()
            import re
            for char in characters:
                if re.search(rf"\b{char}\b", text_to_scan):
                    detected_chars.append(char)

        char_media = []
        if detected_chars:
            print("")
            print("=" * 60)
            print("CHARACTER DETECTED - Prioritizing character-specific media")
            for char in detected_chars:
                char_dir = Path("assets/stock/pinterest/characters") / char
                char_dir.mkdir(parents=True, exist_ok=True)
                
                # Check files count
                files = [f for f in char_dir.iterdir() if f.is_file()]
                if len(files) == 0:
                    self._download_character_assets_fallback(char)
                    files = [f for f in char_dir.iterdir() if f.is_file()]
                    
                if files:
                    print(f"  Character: {char.upper()} -> Folder: {char_dir}")
                    found_char_files = 0
                    for f in files:
                        ext = f.suffix.lower()
                        if ext in VIDEO_EXTENSIONS:
                            char_media.append(MediaItem(f, "video", char))
                            found_char_files += 1
                        elif ext in IMAGE_EXTENSIONS:
                            char_media.append(MediaItem(f, "image", char))
                            found_char_files += 1
                    print(f"    Loaded {found_char_files} files for {char}")
            print(f"  Total character-specific files loaded: {len(char_media)}")
            print("=" * 60)
            print("")

        selected = []
        sel_paths = set()

        # 3. Assemble full selection mapping to each line (100% strictly UNIQUE files)
        for idx in range(target):
            # A. Try semantic B-Roll
            item = None
            if idx < len(semantic_media):
                cand = semantic_media[idx]
                if cand and cand.path not in sel_paths:
                    item = cand
                
            if item is not None:
                selected.append(item)
                sel_paths.add(item.path)
                continue
                
            # B. Try Character priorities
            if char_media:
                avail_char = [x for x in char_media if x.path not in sel_paths]
                if avail_char:
                    chosen = random.choice(avail_char)
                    selected.append(chosen)
                    sel_paths.add(chosen.path)
                    continue
                    
            # C. Try general pool balance (strictly unique items)
            pool = list(self.all_media)
            avail = [x for x in pool if x.path not in sel_paths]
            if avail:
                chosen = random.choice(avail)
                selected.append(chosen)
                sel_paths.add(chosen.path)
            else:
                # Ultimate fallback if entire inventory is exhausted
                selected.append(random.choice(self.all_media))

        print(f"Selected {len(selected)} 100% UNIQUE media items for reel (Anti-repetition active):")
        for i, item in enumerate(selected[:10], 1):
            print(f"  {i:02d}. {item}")
        if len(selected) > 10:
            print(f"  ... and {len(selected) - 10} more unique items (ZERO clip reuse on timeline)")

        return selected

    def _balance_selection(self, target):
        min_images = max(2, int(target * 0.30))
        min_videos = max(2, int(target * 0.50))

        images_pool = list(self.images)
        videos_pool = list(self.videos)
        random.shuffle(images_pool)
        random.shuffle(videos_pool)

        selected = []

        # Add minimum images
        while len([x for x in selected if x.media_type == "image"]) < min_images:
            if not images_pool:
                images_pool = list(self.images)
                random.shuffle(images_pool)
            selected.append(images_pool.pop())

        # Add minimum videos
        while len([x for x in selected if x.media_type == "video"]) < min_videos:
            if not videos_pool:
                videos_pool = list(self.videos)
                random.shuffle(videos_pool)
            selected.append(videos_pool.pop())

        # Fill remaining from full pool
        full_pool = list(self.all_media)
        random.shuffle(full_pool)
        while len(selected) < target:
            item = random.choice(full_pool)
            selected.append(item)

        random.shuffle(selected)
        return selected[:target]

    def get_random_music(self):
        from config.settings import MUSIC_PATH
        music_dir = Path(MUSIC_PATH)

        if not music_dir.exists():
            music_dir.mkdir(parents=True, exist_ok=True)
            print(f"Music folder created: {music_dir}")
            print("Add .mp3 files to assets/music for background music")
            return None

        music_files = [
            f for f in music_dir.iterdir()
            if f.is_file() and f.suffix.lower() in [".mp3", ".wav", ".m4a"]
        ]

        if not music_files:
            print("No music files found in assets/music")
            print("Add royalty-free .mp3 files there for background music")
            return None

        chosen = random.choice(music_files)
        print(f"Music selected: {chosen.name}")
        return str(chosen)

    def _download_character_assets_fallback(self, char):
        char_dir = Path("assets/stock/pinterest/characters") / char
        char_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if it already has files (REUSE CACHED ASSETS)
        has_files = any(f.is_file() for f in char_dir.iterdir())
        if has_files:
            return True
            
        from config.settings import PEXELS_API_KEY, MODE
        if not PEXELS_API_KEY or MODE == "data_saver":
            print(f"  Skipping auto-download for {char}: PEXELS_API_KEY not set or data_saver mode active.")
            return False
            
        print(f"  [Auto-Downloader] No local assets found for character '{char}'.")
        print(f"  Attempting to download stock media from Pexels...")
        
        try:
            import asyncio
            from src.utils.media_downloader import run_pexels_download
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            print(f"  Downloading videos for '{char}'...")
            loop.run_until_complete(
                run_pexels_download(
                    query=f"{char} history" if char in ["jesus", "mary", "paul"] else f"{char}",
                    limit=3,
                    media_type="video",
                    folder=f"pinterest/characters/{char}"
                )
            )
            print(f"  Downloading photos for '{char}'...")
            loop.run_until_complete(
                run_pexels_download(
                    query=f"{char}",
                    limit=3,
                    media_type="photo",
                    folder=f"pinterest/characters/{char}"
                )
            )
            return True
        except Exception as e:
            print(f"  Auto-download for {char} failed: {e}")
            return False

    def _download_semantic_broll(self, query):
        import re
        # Sanitize query to make a safe folder name
        query_slug = re.sub(r'[^a-zA-Z0-9 ]+', '', query.lower()).strip().replace(' ', '_')
        if not query_slug:
            return None
            
        broll_dir = Path("assets/stock/pinterest/autobroll") / query_slug
        broll_dir.mkdir(parents=True, exist_ok=True)
        
        # If folder already has files, return the path
        files = [f for f in broll_dir.iterdir() if f.is_file()]
        if files:
            return broll_dir
            
        from config.settings import PEXELS_API_KEY, MODE
        if not PEXELS_API_KEY or MODE == "data_saver":
            return None
            
        print(f"  [Semantic B-Roll] Downloading assets for query: '{query}'...")
        try:
            import asyncio
            from src.utils.media_downloader import run_pexels_download
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Download 1 video and 1 photo for semantic relevance
            loop.run_until_complete(
                run_pexels_download(
                    query=query,
                    limit=1,
                    media_type="video",
                    folder=f"pinterest/autobroll/{query_slug}"
                )
            )
            loop.run_until_complete(
                run_pexels_download(
                    query=query,
                    limit=1,
                    media_type="photo",
                    folder=f"pinterest/autobroll/{query_slug}"
                )
            )
            return broll_dir
        except Exception as e:
            print(f"  Semantic download for '{query}' failed: {e}")
            return None

    def print_summary(self):
        if not self._scanned:
            self.scan()

        print("")
        print("=" * 55)
        print("MEDIA MANAGER - Summary")
        print("=" * 55)
        print(f"Niche:          {self.niche}")
        print(f"Total Videos:   {len(self.videos)}")
        print(f"Total Images:   {len(self.images)}")
        print(f"Total Media:    {len(self.all_media)}")
        print(f"Target Items:   {TARGET_MEDIA_ITEMS}")

        if self.all_media:
            total_size = sum(m.size_mb for m in self.all_media)
            print(f"Total Size:     {total_size:.1f} MB")

        print("")
        print("Stock Folders:")
        niche_conf = NICHE_CONFIG.get(self.niche, {})
        for folder_name in niche_conf.get("folders", []):
            path = STOCK_PATHS.get(folder_name, "")
            count_v = len([x for x in self.videos if x.folder_name == folder_name])
            count_i = len([x for x in self.images if x.folder_name == folder_name])
            print(f"  {folder_name:15} -> {count_v} videos | {count_i} images")

        print("=" * 55)
        print("")


# ============================================================
# SIMPLE HELPER
# ============================================================

def get_media_for_reel(niche=None, count=None):
    manager = MediaManager(niche=niche)
    manager.scan()
    return manager.pick_media_for_reel(count=count)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\nTesting MediaManager...")

    manager = MediaManager(niche="gospel")
    manager.scan()
    manager.print_summary()

    print("\nPicking media for reel...")
    selected = manager.pick_media_for_reel()

    print(f"\nMusic track:")
    music = manager.get_random_music()
    print(f"  {music if music else 'No music files yet - add mp3 to assets/music'}")

    print("\nDone.")
    print("")
    print("NOTE: If you see 0 files, add videos/images to:")
    for name, path in STOCK_PATHS.items():
        print(f"  {path}")


# ============================================
# SMART MUSIC SELECTOR (with subfolder support)
# ============================================

def get_smart_music(niche="gospel"):
    import random
    from pathlib import Path as P
    import subprocess
    from config.settings import MODE

    MUSIC_BASE = P("assets/music")
    extensions = [".mp3", ".wav", ".m4a", ".ogg"]

    # Niche to music folder mapping
    niche_music = {
        "gospel":       ["worship", "prayer"],
        "prayer":       ["prayer", "ambient", "worship"],
        "praise":       ["praise", "worship", "cheerful"],
        "motivational": ["motivational", "cinematic"],
        "tech":         ["cinematic", "ambient"],
        "swahili":      ["swahili", "worship", "prayer"],
        "stories":      ["cinematic", "ambient"],
    }

    folders_to_check = niche_music.get(niche, ["worship", "prayer"])

    # Try each preferred folder
    for folder_name in folders_to_check:
        folder = MUSIC_BASE / folder_name
        if folder.exists():
            files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in extensions]
            if files:
                chosen = random.choice(files)
                print(f"Music selected: [{folder_name}] {chosen.name}")
                return str(chosen)

    # Fallback 1: check root music folder
    if MUSIC_BASE.exists():
        all_music = []
        for f in MUSIC_BASE.rglob("*"):
            if f.is_file() and f.suffix.lower() in extensions:
                all_music.append(f)
        if all_music:
            chosen = random.choice(all_music)
            rel = chosen.relative_to(MUSIC_BASE)
            print(f"Music selected: [general] {rel}")
            return str(chosen)

    # Fallback 2: Auto-download one background music track online if empty and not in data saver mode
    if MODE != "data_saver":
        target_subfolder = folders_to_check[0]
        target_dir = MUSIC_BASE / target_subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare search query
        queries = {
            "worship":      "calm instrumental worship background music royalty free",
            "prayer":       "calm ambient prayer background music instrumental royalty free",
            "praise":       "uplifting praise worship instrumental beat royalty free",
            "motivational": "cinematic motivational background music instrumental royalty free",
            "cinematic":    "ambient cinematic corporate electronic background music royalty free",
            "swahili":      "african acoustic guitar instrumental background music royalty free",
            "ambient":      "calm ambient background music drone royalty free",
        }
        search_query = queries.get(target_subfolder, f"calm instrumental {target_subfolder} music background beat royalty free")
        
        print(f"  No local music found for niche '{niche}'. Auto-downloading one online background track...")
        print(f"  Query: {search_query}")
        
        output_template = str(target_dir / "%(title)s.%(ext)s")
        try:
            res = subprocess.run([
                "yt-dlp",
                "-o", output_template,
                "--no-playlist",
                "--extract-audio",
                "--audio-format", "mp3",
                f"ytsearch1:{search_query}"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
            
            if res.returncode == 0:
                files = [f for f in target_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions]
                if files:
                    chosen = random.choice(files)
                    print(f"Auto-downloaded music selected: [{target_subfolder}] {chosen.name}")
                    return str(chosen)
        except Exception as e:
            print(f"  Auto-download music failed: {e}")

    print(f"No music found for niche: {niche}")
    print(f"Add .mp3 files to one of these folders:")
    for folder_name in folders_to_check:
        print(f"  assets/music/{folder_name}/")
    return None
