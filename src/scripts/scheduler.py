# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except:
        pass

import time
import json
from pathlib import Path
import asyncio

# Set PYTHONPATH
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import NICHE, LANGUAGE, ACTIVE_VOICE, OUTPUT_DIR
from src.scripts.ai_generator import AIScriptGenerator
from src.utils.media_manager import MediaManager
from src.video.video_engine import ReelVideoEngine
from src.utils.uploader import SocialUploader

PUBLISH_LOG = BASE_DIR / "output" / "publication_log.json"

def get_today_date():
    return time.strftime("%Y-%m-%d")

def check_already_published():
    if not PUBLISH_LOG.exists():
        return False
    try:
        data = json.loads(PUBLISH_LOG.read_text(encoding="utf-8"))
        today = get_today_date()
        return today in data
    except:
        return False

def mark_published(video_name, platforms):
    data = {}
    if PUBLISH_LOG.exists():
        try: data = json.loads(PUBLISH_LOG.read_text(encoding="utf-8"))
        except: pass
    today = get_today_date()
    data[today] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "video": video_name,
        "platforms": platforms
    }
    PUBLISH_LOG.parent.mkdir(parents=True, exist_ok=True)
    PUBLISH_LOG.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

async def run_daily_pipeline(force=False, log_callback=None):
    def log(msg):
        print(msg)
        if log_callback:
            try:
                log_callback(msg)
            except:
                pass

    if check_already_published() and not force:
        log(f"[Scheduler] Already published a video today. Skipping daily run. Use --force to override.")
        return
        
    log(f"\n[Scheduler] Starting Daily Video Factory Pipeline: {get_today_date()} ...")
    
    # 1. Generate Script
    log("\n[Scheduler] Step 1: Generating script via AI...")
    generator = AIScriptGenerator()
    script = await generator.generate(niche=NICHE, language=LANGUAGE, use_viral_hook=True)
    if not script:
        log("  Error: Script generation failed.")
        return
        
    log(f"  Script Title: {script['title']}")
    
    # 2. Narration Sound + Sync Subtitles
    log("\n[Scheduler] Step 2: Rendering voice narration & sync timings...")
    from src.audio.tts_engine import TTSEngine
    lines = [script["hook"]] + script["body"] + [script["cta"]]
    tts_engine = TTSEngine(voice=script["voice"], rate=script["rate"])
    tts_result = await tts_engine.generate_per_line_synced(lines, prefix=f"auto_{NICHE}")
    if not tts_result:
        log("  Error: Narration generation failed.")
        return
        
    # 3. Load & Match B-Roll (Semantic Auto-matching active!)
    log("\n[Scheduler] Step 3: Loading stock media items...")
    subs_len = len(tts_result["subtitles"]) if tts_result and "subtitles" in tts_result else 10
    needed_clips = max(35, subs_len * 3)
    media_items = manager.pick_media_for_reel(count=needed_clips, script=script)
    if not media_items:
        log("  Error: No stock media items retrieved.")
        return
        
    # 4. Pick Smart Niche Music Beat
    from src.utils.media_manager import get_smart_music
    music_path = get_smart_music(niche=NICHE)
    
    # 5. Compile Video
    log("\n[Scheduler] Step 4: Compiling cinematic reels...")
    video_engine = ReelVideoEngine(mood=script["mood"])
    output_name = f"auto_{NICHE}_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    
    out_path = video_engine.build_reel(
        media_items=media_items,
        audio_path=tts_result["audio_path"],
        subtitles=tts_result["subtitles"],
        output_name=output_name,
        hook_text=script["hook"],
        music_path=music_path,
        show_progress_bar=True,
        log_callback=log
    )
    log(f"  Compiled reel saved to: {out_path}")
    
    # 6. Publish to active platforms
    from config.settings import ENV
    platforms_str = ENV.get("PUBLISH_PLATFORMS", "youtube")
    active_platforms = [p.strip().lower() for p in platforms_str.split(",") if p.strip()]
    
    published_platforms = []
    
    for platform in active_platforms:
        log(f"\n[Scheduler] Step 5: Publishing to {platform.upper()}...")
        uploader = SocialUploader(platform=platform)
        
        success = False
        title = script["title"]
        
        log(f"  Generating viral AI caption with trending hashtags...")
        try:
            caption = await generator.generate_caption(script, niche=NICHE)
        except Exception as e:
            log(f"  [Warning] AI caption generation failed ({e}). Using fallback caption.")
            caption = f"{title}\n\n#dailydevotion #bibletruth #gospelreels #{NICHE} #faith"
            
        import random
        delay_mins = random.randint(1, 5)
        log(f"  [Organic Delay] Waiting {delay_mins} min(s) before posting to {platform.upper()} (natural timing)...")
        await asyncio.sleep(delay_mins * 60)
        
        if platform == "youtube":
            success = await asyncio.to_thread(uploader.upload_youtube_shorts, out_path, title=title, description=caption)
        elif platform == "tiktok":
            success = await asyncio.to_thread(uploader.upload_tiktok, out_path, caption=caption)
        elif platform == "instagram":
            success = await asyncio.to_thread(uploader.upload_instagram_reels, out_path, caption=caption)
            
        if success:
            published_platforms.append(platform)
            
    if published_platforms:
        mark_published(Path(out_path).name, published_platforms)
        log(f"\n[Scheduler] Daily pipeline completed successfully! Posted to: {published_platforms}")
    else:
        log("\n[Scheduler] Pipeline completed, but uploader was skipped or failed on all platforms.")

if __name__ == "__main__":
    force_run = "--force" in sys.argv or "-f" in sys.argv
    asyncio.run(run_daily_pipeline(force=force_run))
