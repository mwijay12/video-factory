# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY - MAIN ENTRY POINT
# ================================================================
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except:
        pass

import asyncio
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import NICHE, LANGUAGE, MODE, OUTPUT_DIR
from src.scripts.gospel_script import ScriptManager
from src.scripts.ai_generator import AIScriptGenerator
from src.audio.tts_engine import TTSEngine
from src.utils.media_manager import MediaManager, get_smart_music
from src.video.video_engine import ReelVideoEngine, load_json, now_stamp, ensure_output


# ================================================================
# BANNER
# ================================================================

def print_banner():
    print('')
    print('=' * 62)
    print('  V I D E O   F A C T O R Y')
    print('  Automated Reel Generator')
    print('  Gospel | Prayer | Praise | Swahili | Motivation')
    print('=' * 62)
    print('')


# ================================================================
# UNIVERSAL SCRIPT HELPER
# Works for BOTH AI and Local scripts
# ================================================================

def get_script_lines(script):
    if not script:
        return []
    lines = []
    if script.get('hook'):
        lines.append(script['hook'])
    body = script.get('body', [])
    if isinstance(body, list):
        lines.extend(body)
    if script.get('cta'):
        lines.append(script['cta'])
    return lines


# ================================================================
# NARRATION REEL PIPELINE
# ================================================================

async def generate_narration_reel(
    niche='gospel',
    language='english',
    script_index=0,
    mood=None,
    output_name=None,
    **kwargs,
):
    start_time = time.time()

    print(f'  Niche:      {niche}')
    print(f'  Language:   {language}')
    print(f'  Mode:       {MODE}')
    print('')

    # STEP 1: Load Script
    print('[1/5] Loading script...')

    use_ai = kwargs.get('use_ai', False)
    use_series = kwargs.get('use_series', None)
    use_viral = kwargs.get('use_viral', False)
    use_time_based = kwargs.get('use_time_based', False)

    if use_series or use_viral or use_time_based:
        use_ai = True

    if use_ai:
        print('  Generating fresh AI script...')
        ai_gen = AIScriptGenerator()
        script = await ai_gen.generate(
            niche=niche,
            language=language,
            use_viral_hook=use_viral,
            series=use_series,
            time_based=use_time_based,
        )
    else:
        safe_niche = niche if niche in ['gospel','prayer','motivational','swahili'] else 'gospel'
        script_mgr = ScriptManager(niche=safe_niche, language=language)
        script = script_mgr.get_script_by_index(script_index)
        if not script:
            script = script_mgr.get_random_script()

    if not script:
        print('ERROR: No script found!')
        return None

    lines = get_script_lines(script)

    print(f'  Title:  {script.get("title", "Untitled")}')
    print(f'  Hook:   {script.get("hook", "")}')
    print(f'  Lines:  {len(lines)}')
    print('')

    # STEP 2: Generate Voice
    print('[2/5] Generating voice narration...')

    voice_map = {
        'gospel':         'en-US-ChristopherNeural',
        'prayer':         'en-US-ChristopherNeural',
        'bedtime_prayer': 'en-US-AriaNeural',
        'praise':         'en-US-GuyNeural',
        'motivational':   'en-US-GuyNeural',
        'tech':           'en-US-DavisNeural',
        'swahili':        'puter:gemini:Puck',
    }
    rate_map = {
        'gospel':         '-15%',
        'prayer':         '-18%',
        'bedtime_prayer': '-22%',
        'praise':         '-8%',
        'motivational':   '-12%',
        'tech':           '-8%',
        'swahili':        '-10%',
    }

    import config.settings
    import importlib
    importlib.reload(config.settings)
    
    global_active_voice = getattr(config.settings, "ACTIVE_VOICE", "")
    global_provider = getattr(config.settings, "TTS_PROVIDER", "edge-tts")
    
    voice = script.get('voice')
    if global_provider in ["puter", "elevenlabs"] or (global_active_voice and (global_active_voice.startswith("puter:") or global_active_voice.startswith("elevenlabs:"))):
        voice = global_active_voice
    elif not voice:
        voice = voice_map.get(niche, 'en-US-ChristopherNeural')
        
    rate = script.get('rate') or rate_map.get(niche, '-5%')

    if language == 'swahili' and not script.get('voice'):
        voice = 'puter:gemini:Puck'

    engine = TTSEngine(voice=voice, rate=rate)
    prefix = f'{niche}_{script.get("id", "reel")}'
    tts_result = await engine.generate_per_line_synced(lines, prefix=prefix)

    if not tts_result or not tts_result.get('audio_path'):
        print('ERROR: Voice generation failed!')
        return None

    audio_path = tts_result['audio_path']
    subtitles = tts_result['subtitles']
    print(f'  Audio:  {Path(audio_path).name}')
    print(f'  Subs:   {len(subtitles)} lines')
    print('')

    # STEP 3: Get Media
    print('[3/5] Loading media...')
    safe_niche_for_media = niche if niche != 'bedtime_prayer' else 'prayer'
    manager = MediaManager(niche=safe_niche_for_media)
    manager.scan()

    media_items = []
    if manager.has_media():
        needed_clips = max(35, len(subtitles) * 3)
        media_items = manager.pick_media_for_reel(count=needed_clips, script=script)
        print(f'  Media:  {len(media_items)} 100% unique items (Anti-repetition active)')
    else:
        print('  Media:  No local files - using gradient backgrounds')
    print('')

    # STEP 4: Music
    print('[4/5] Selecting music...')
    music_path = get_smart_music(niche=safe_niche_for_media)
    if music_path:
        print(f'  Music:  {Path(music_path).name}')
    else:
        print('  Music:  None')
    print('')

    # STEP 5: Render
    print('[5/5] Rendering reel...')

    if not output_name:
        output_name = f'{script.get("id", "reel")}_{now_stamp()}.mp4'

    active_mood = mood or script.get('mood', 'peaceful')
    hook_text = script.get('hook', '')

    video_engine = ReelVideoEngine(mood=active_mood)
    output_path = video_engine.build_reel(
        media_items=media_items,
        audio_path=audio_path,
        subtitles=subtitles,
        output_name=output_name,
        hook_text=hook_text,
        music_path=music_path,
        show_progress_bar=True,
    )

    elapsed = time.time() - start_time
    print('')
    print('=' * 62)
    print('  DONE!')
    print(f'  Reel:    {output_path}')
    print(f'  Time:    {elapsed:.1f}s')
    print('=' * 62)
    print('')

    return output_path


# ================================================================
# SONG LYRICS PIPELINE
# ================================================================

async def generate_song_reel(song_path, language=None, niche='gospel', mood=None, output_name=None, words_per_line=4):
    song_path = Path(song_path)

    if not song_path.exists():
        for subfolder in ['swahili', 'english', 'mixed', 'custom', '']:
            check = Path('assets/songs') / subfolder / song_path.name
            if check.exists():
                song_path = check
                break

    if not song_path.exists():
        print(f'Song not found: {song_path}')
        return None

    print(f'Song: {song_path.name}')
    print(f'Extracting lyrics & generating social kit...')

    from src.audio.lyrics_mode import generate_lyric_reel
    result = await generate_lyric_reel(
        song_path=str(song_path),
        language=language,
        niche=niche,
        mood=mood or 'peaceful',
        words_per_line=words_per_line,
    )
    return result





# ================================================================
# TRENDING TOPICS REEL PIPELINE
# ================================================================

async def generate_trending_reel(
    niche='gospel',
    language='english',
    category=None,
    mood=None,
    output_name=None,
):
    start_time = time.time()
    
    from src.scripts.trending_topics import TrendCollector, trend_to_spiritual_script
    
    print('=' * 62)
    print('  TRENDING REEL GENERATOR')
    print('=' * 62)
    print(f'  Niche: {niche}')
    print(f'  Language: {language}')
    print('')
    
    # Step 1: Collect or load trends
    print('[1/6] Loading trends...')
    collector = TrendCollector()
    trends = collector.get_cached_trends()
    
    # If cache empty or older than 6 hours, fetch fresh
    needs_fresh = True
    if trends:
        try:
            import json as _j
            cache = _j.loads(Path('output/.trends_cache.json').read_text(encoding='utf-8'))
            from datetime import datetime as _dt, timedelta as _td
            collected_at = _dt.fromisoformat(cache.get('collected_at', '2000-01-01'))
            if (_dt.now() - collected_at) < _td(hours=6):
                needs_fresh = False
                print(f'  Using cached trends ({len(trends)} items)')
        except Exception:
            pass
    
    if needs_fresh:
        print('  Fetching fresh trends...')
        regions = None  # Fetch all regions by default to populate a rich cache
        if niche == 'swahili':
            regions = ['east_africa', 'kenya', 'tanzania']
        trends = await collector.collect_all_trends(regions=regions)
    
    # Step 2: Pick best trend
    print('')
    print('[2/6] Selecting best trend...')
    categories_filter = [category] if category else None
    best_trends = collector.pick_best_trends(trends, categories=categories_filter, count=5)
    
    if not best_trends:
        print('  No suitable trends found')
        return None
    
    selected = best_trends[0]
    print(f'  Selected: {selected["title"][:80]}')
    print(f'  Category: {selected["category"]}')
    
    # Step 3: Convert to spiritual script
    print('')
    print('[3/6] Converting to spiritual script...')
    script = await trend_to_spiritual_script(selected, niche=niche, language=language)
    
    if not script:
        print('  AI failed to generate script')
        return None
    
    print(f'  Title: {script["title"]}')
    print(f'  Hook:  {script["hook"]}')
    print(f'  Lines: {len(script.get("body", []))}')
    
    # Step 4: Generate voice
    print('')
    print('[4/6] Generating voice...')
    voice = script.get('voice', 'en-US-ChristopherNeural')
    rate = script.get('rate', '-5%')
    
    if language == 'swahili' and not script.get('voice'):
        voice = 'puter:gemini:Puck'
    
    engine = TTSEngine(voice=voice, rate=rate)
    lines = get_script_lines(script)
    prefix = f'trend_{script.get("id", "reel")}'
    tts_result = await engine.generate_per_line_synced(lines, prefix=prefix)
    
    if not tts_result:
        print('  TTS failed')
        return None
    
    audio_path = tts_result['audio_path']
    subtitles = tts_result['subtitles']
    
    # Step 5: Get media
    print('')
    print('[5/6] Loading media...')
    manager = MediaManager(niche=niche)
    manager.scan()
    media_items = manager.pick_media_for_reel(count=len(subtitles), script=script) if manager.has_media() else []
    music_path = get_smart_music(niche=niche)
    
    # Step 6: Render
    print('')
    print('[6/6] Rendering reel...')
    if not output_name:
        output_name = f'trending_{script["id"]}_{now_stamp()}.mp4'
    
    active_mood = mood or script.get('mood', 'powerful')
    video_engine = ReelVideoEngine(mood=active_mood)
    
    output_path = video_engine.build_reel(
        media_items=media_items,
        audio_path=audio_path,
        subtitles=subtitles,
        output_name=output_name,
        hook_text=script['hook'],
        music_path=music_path,
        show_progress_bar=True,
    )
    
    elapsed = time.time() - start_time
    print('')
    print('=' * 62)
    print(f'  TRENDING REEL DONE in {elapsed:.1f}s')
    print(f'  Topic: {selected["title"][:60]}')
    print(f'  File: {output_path}')
    print('=' * 62)
    
    return output_path


# ================================================================
# LIST SCRIPTS
# ================================================================

def list_all_scripts():
    print('')
    print('=' * 62)
    print('  AVAILABLE SCRIPTS')
    print('=' * 62)
    for niche in ['gospel', 'prayer', 'praise', 'motivational', 'swahili']:
        try:
            mgr = ScriptManager(niche=niche, language='english')
            scripts = mgr.get_all_scripts()
            print(f'\n  [{niche.upper()}] - {len(scripts)} scripts')
            for i, s in enumerate(scripts, 1):
                print(f'    {i}. {s.get("title", "")}')
        except Exception as e:
            print(f'  [{niche.upper()}] error: {e}')
    print('=' * 62)
    print('')


# ================================================================
# CLI
# ================================================================

def parse_args():
    p = argparse.ArgumentParser(
        description='VideoFactory - Automated Reel Generator',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''
Examples:
  python main.py                              Generate default reel
  python main.py --ai                         AI-generated script
  python main.py --ai --niche prayer          Prayer reel
  python main.py --ai --viral                 With viral hook
  python main.py --series armor_of_god        Series part
  python main.py --batch 5                    Generate 5 reels
  python main.py --time-based                 Auto pick niche by time
  python main.py --niche bedtime_prayer       Whisper bedtime mode
  python main.py --list                       List all scripts
  python main.py --clip-list                  List longform sermon/podcast sources
  python main.py --clip-longform              Clip newest longform video → 3 shorts
  python main.py --clip-longform sermon.mp4 --clips 5 --clip-crop top
        '''
    )
    p.add_argument('--niche', '-n', type=str, default=NICHE,
                   choices=['gospel','prayer','bedtime_prayer','praise','motivational','tech','swahili'])
    p.add_argument('--lang', '-l', type=str, default=LANGUAGE, 
                  choices=['english','swahili','en','sw'])
    p.add_argument('--script', '-s', type=int, default=1)
    p.add_argument('--mood', '-m', type=str, default=None,
                   choices=['peaceful','powerful','hopeful','emotional','holy','cinematic','whisper'])
    p.add_argument('--song', type=str, default=None)
    p.add_argument('--batch', type=int, default=1)
    p.add_argument('--series', type=str, default=None,
                   choices=['armor_of_god','fruits_of_spirit','names_of_god','powerful_prayers'])
    p.add_argument('--viral', action='store_true')
    p.add_argument('--time-based', action='store_true')
    p.add_argument('--trending', action='store_true',
                   help='Generate reel from real trending news topic')
    p.add_argument('--trend-category', type=str, default=None,
                   choices=[
                       # Christian
                       'church_news', 'gospel_music', 'christian_celeb',
                       'megachurch', 'persecution', 'revival', 'bible_news',
                       'african_church', 'prophecy', 'moral_issue',
                       # General
                       'tragedy', 'victory', 'unity', 'struggle', 'hope',
                       'celebrity', 'celebrity_death', 'youth_crisis',
                       'sports', 'tech', 'business',
                   ],
                   help='Filter trending by category')
    p.add_argument('--ai', action='store_true')
    p.add_argument('--list', action='store_true')
    p.add_argument('--list-songs', action='store_true', help='List all available songs and tracks')
    p.add_argument('--duration', '-d', type=int, default=25, help='Target reel duration in seconds')
    p.add_argument('--words-per-line', type=int, default=4, help='Words per subtitle line for kinetic captions')
    p.add_argument('--output', '-o', type=str, default=None)
    p.add_argument('--download-pinterest', type=str, default=None,
                   help='Download pins from a Pinterest board URL or niche name')
    p.add_argument('--download-stock', type=str, default=None,
                   help='Download vertical stock videos or photos from Pexels by query')
    p.add_argument('--download-limit', type=int, default=10,
                   help='Number of files to download')
    p.add_argument('--download-folder', type=str, default=None,
                   help='Subfolder in assets/stock/ to save files')
    p.add_argument('--download-type', type=str, default='video',
                   choices=['video', 'photo'],
                   help='Type of media to download from stock API')
    p.add_argument('--download-music', type=str, default=None,
                   help='Download copyright-free background music/beats from YouTube by niche or query')
    # ── Longform Clipper (sermons/podcasts → vertical shorts) ──
    p.add_argument('--clip-longform', type=str, nargs='?', const='auto',
                   default=None, metavar='SOURCE',
                   help='Clip a longform video into captioned vertical shorts\n'
                        '(omit SOURCE to use the newest file in assets/longform)')
    p.add_argument('--clip-list', action='store_true',
                   help='List longform source videos available for clipping')
    p.add_argument('--clips', type=int, default=3,
                   help='Number of top clips to render (default: 3)')
    p.add_argument('--clip-min', type=float, default=20,
                   help='Minimum clip length in seconds (default: 20)')
    p.add_argument('--clip-max', type=float, default=50,
                   help='Maximum clip length in seconds (default: 50)')
    p.add_argument('--clip-model', type=str, default='base',
                   choices=['tiny', 'base', 'small', 'medium', 'large-v3'],
                   help='faster-whisper model size (default: base)')
    p.add_argument('--clip-crop', type=str, default='center',
                   choices=['center', 'top', 'bottom', 'left', 'right'],
                   help='9:16 crop focus when reframing (default: center)')
    return p.parse_args()


# ================================================================
# RUN
# ================================================================

async def run():
    print_banner()
    args = parse_args()
    # Normalize short language codes
    if args.lang == 'en':
        args.lang = 'english'
    elif args.lang == 'sw':
        args.lang = 'swahili'

    ensure_output()

    if args.list_songs:
        from src.audio.song_picker import list_songs_pretty
        list_songs_pretty()
        return

    if args.download_pinterest:
        from src.utils.media_downloader import run_pinterest_download
        await run_pinterest_download(
            args.download_pinterest,
            limit=args.download_limit,
            folder=args.download_folder
        )
        return

    if args.download_stock:
        from src.utils.media_downloader import run_pexels_download
        await run_pexels_download(
            args.download_stock,
            limit=args.download_limit,
            media_type=args.download_type,
            folder=args.download_folder or 'nature'
        )
        return

    if args.download_music:
        from src.utils.media_downloader import run_music_download
        await run_music_download(
            args.download_music,
            limit=args.download_limit,
            folder=args.download_folder
        )
        return

    if args.list:
        list_all_scripts()
        return

    # ── Longform Clipper modes ──
    if args.clip_list:
        from src.video.longform_clipper import print_source_list
        print_source_list()
        return

    if args.clip_longform is not None:
        from src.video.longform_clipper import run_clipper_pipeline
        run_clipper_pipeline(
            source=args.clip_longform,
            language=args.lang,
            model=args.clip_model,
            min_dur=args.clip_min,
            max_dur=args.clip_max,
            count=args.clips,
            crop=args.clip_crop,
            niche=args.niche,
            mood=args.mood or 'peaceful',
            words_per_line=args.words_per_line,
        )
        return

    if args.song:
        from src.audio.lyrics_mode import generate_lyric_reel_smart
        # song can be a name or empty for random
        song_name = args.song if args.song.lower() not in ['random', 'auto', ''] else None
        await generate_lyric_reel_smart(
            song_name=song_name,
            language=args.lang,
            niche=args.niche,
            mood=args.mood or 'peaceful',
            words_per_line=args.words_per_line,
            target_duration=args.duration,
            use_best_segment=True,
        )
        return

    if args.trending:
        await generate_trending_reel(
            niche=args.niche,
            language=args.lang,
            category=args.trend_category,
            mood=args.mood,
            output_name=args.output,
        )
        return
    
    if args.batch > 1:
        print(f'\nBATCH MODE: Generating {args.batch} reels...\n')
        for i in range(args.batch):
            print(f'\n{"="*62}\n  REEL {i+1}/{args.batch}\n{"="*62}')
            await generate_narration_reel(
                niche=args.niche,
                language=args.lang,
                script_index=args.script - 1,
                mood=args.mood,
                output_name=None,
                use_ai=True,
                use_series=args.series,
                use_viral=args.viral,
                use_time_based=args.time_based,
            )
    else:
        await generate_narration_reel(
            niche=args.niche,
            language=args.lang,
            script_index=args.script - 1,
            mood=args.mood,
            output_name=args.output,
            use_ai=args.ai,
            use_series=args.series,
            use_viral=args.viral,
            use_time_based=args.time_based,
        )


if __name__ == '__main__':
    asyncio.run(run())
