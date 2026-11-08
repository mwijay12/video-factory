# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except:
        pass

import json
import asyncio
import time
from pathlib import Path

# Set PYTHONPATH to project root
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import OUTPUT_DIR
from src.audio.lyrics_mode import LyricsExtractor
from src.utils.media_manager import MediaManager
from src.video.video_engine import ReelVideoEngine

def log(msg, log_file=None):
    print(msg, flush=True)
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except:
            pass

def progress(pct: int, step: str = "", log_file=None):
    step_suffix = f" STEP:{step}" if step else ""
    log(f"PROGRESS:{pct}%{step_suffix}", log_file)

def get_audio_duration_via_moviepy(audio_path):
    from moviepy import AudioFileClip
    try:
        clip = AudioFileClip(str(audio_path))
        dur = clip.duration
        clip.close()
        return dur
    except Exception as e:
        print(f"Warning getting duration: {e}")
        return 30.0

def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--payload":
        print("Usage: python lyrics_worker.py --payload <json_path> [log_file_path]")
        sys.exit(1)

    payload_path = Path(sys.argv[2])
    log_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Clear log file
    if log_file:
        try:
            Path(log_file).write_text("Starting Lyric Reel Compilation...\n", encoding="utf-8")
        except:
            pass

    progress(5, "Reading payload parameters...", log_file)
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"ERROR: Failed to load payload: {e}", log_file)
        sys.exit(1)

    song_path = payload.get("song_path")
    mode = payload.get("mode", "whisper") # "whisper" or "custom"
    custom_lyrics = payload.get("custom_lyrics", "")
    niche = payload.get("niche", "gospel")
    mood = payload.get("mood", "peaceful")
    words_per_line = int(payload.get("words_per_line", 4))
    language = payload.get("language", "english")
    output_name = payload.get("output_name", "lyric_reel.mp4")
    
    # New customization parameters
    audio_mode = payload.get("audio_mode", "clip") # "clip" or "full"
    start_time = float(payload.get("start_time", 0.0))
    clip_duration = payload.get("clip_duration", 30.0)
    end_time = payload.get("end_time", None)
    aspect_ratio = payload.get("aspect_ratio", "9:16")

    song_file = Path(song_path)
    if not song_file.exists():
        # Search in subdirectories
        found = False
        for sub in ['swahili', 'english', 'mixed', 'custom', '']:
            check = Path('assets/songs') / sub / song_file.name
            if check.exists():
                song_file = check
                found = True
                break
            check_m = Path('assets/music') / sub / song_file.name
            if check_m.exists():
                song_file = check_m
                found = True
                break
        if not found:
            log(f"ERROR: Song file not found: {song_path}", log_file)
            progress(100, "Failed: File not found", log_file)
            sys.exit(1)

    log(f"Audio file: {song_file.name}", log_file)

    # -------------------------------------------------------------
    # AUDIO TRIMMING & SLICING (Full Song vs Clip)
    # -------------------------------------------------------------
    target_audio_file = song_file
    if audio_mode == "clip":
        full_dur = get_audio_duration_via_moviepy(song_file)
        start_sec = max(0.0, float(start_time or 0.0))
        if end_time is not None and float(end_time) > start_sec:
            end_sec = min(full_dur, float(end_time))
        elif clip_duration is not None and float(clip_duration) > 0:
            end_sec = min(full_dur, start_sec + float(clip_duration))
        else:
            end_sec = min(full_dur, start_sec + 30.0)

        clip_len = max(3.0, end_sec - start_sec)
        log(f"✂️ Clipping audio: {start_sec:.1f}s to {end_sec:.1f}s (Reel length: {clip_len:.1f}s)", log_file)
        
        temp_dir = Path("output/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        clipped_file = temp_dir / f"clip_{song_file.stem}_{int(start_sec)}_{int(end_sec)}.mp3"

        if not clipped_file.exists():
            try:
                from moviepy import AudioFileClip
                ac = AudioFileClip(str(song_file)).subclipped(start_sec, end_sec)
                ac.write_audiofile(str(clipped_file), logger=None)
                ac.close()
                target_audio_file = clipped_file
            except Exception as e:
                log(f"Warning: Audio clipping failed ({e}), using full audio.", log_file)
        else:
            target_audio_file = clipped_file

    subtitles = []

    if mode == "none":
        log("🚫 Clean Reel Mode selected: No subtitles will be burned. Generating video + audio for CapCut editing.", log_file)
    elif mode == "whisper":
        progress(20, "Extracting and transcribing lyrics with Whisper AI...", log_file)
        extractor = LyricsExtractor(model_size='base')
        try:
            lyrics_result = extractor.extract_lyrics(str(target_audio_file), language=language)
            if lyrics_result:
                extractor.save_lyrics(str(target_audio_file), lyrics_result)
                subtitles = extractor.lyrics_to_subtitles(lyrics_result, group_words_per_line=words_per_line)
                log(f"Whisper successfully generated {len(subtitles)} subtitle chunks.", log_file)
            else:
                log("WARNING: Whisper transcription returned empty text.", log_file)
        except Exception as e:
            log(f"WARNING: Whisper extraction failed: {e}", log_file)

    raw_custom = str(custom_lyrics or "").strip()
    if mode == "custom" and raw_custom:
        progress(25, "Processing custom lyrics and aligning to song clip...", log_file)
        lines = [line.strip() for line in raw_custom.splitlines() if line.strip()]
        if lines:
            from moviepy import AudioFileClip
            try:
                ac = AudioFileClip(str(target_audio_file))
                clip_dur = ac.duration
                ac.close()
            except:
                clip_dur = 30.0
            
            line_dur = max(1.5, clip_dur / len(lines))
            subtitles = []
            for i, line in enumerate(lines):
                subtitles.append({
                    "start": round(i * line_dur, 2),
                    "end": round(min(clip_dur, (i + 1) * line_dur), 2),
                    "text": line
                })
            log(f"Created {len(subtitles)} custom lyric segments ({line_dur:.1f}s each).", log_file)

    caption_style = payload.get("caption_style", "typing")
    transition_style = payload.get("transition_style", "whip_zoom")
    caption_position = payload.get("caption_position", "center")
    include_dance = payload.get("include_dance", False)
    custom_title = payload.get("song_title", "").strip()

    # ---------------------------------------------------------------
    # BEAT DETECTION — Analyze song rhythm for beat-synced clip cuts
    # ---------------------------------------------------------------
    beat_cuts = None
    progress(50, "🎵 Analyzing song rhythm for studio beat-synced clip transitions...", log_file)
    try:
        from src.audio.beat_sync import generate_beat_cut_points
        beat_cuts = generate_beat_cut_points(str(target_audio_file), min_clip=1.2, max_clip=3.5)
        if beat_cuts:
            durations = [c["end"] - c["start"] for c in beat_cuts]
            energy_high = sum(1 for c in beat_cuts if c["energy"] == "high")
            energy_med = sum(1 for c in beat_cuts if c["energy"] == "medium")
            energy_low = sum(1 for c in beat_cuts if c["energy"] == "low")
            log(f"🎵 Studio Beat Sync: {len(beat_cuts)} cuts | Range: {min(durations):.2f}s-{max(durations):.2f}s | Energy: {energy_high}H/{energy_med}M/{energy_low}L", log_file)
        else:
            log("🎵 Beat Sync: No beats detected, using standard clip timing.", log_file)
    except Exception as e:
        log(f"🎵 Beat Sync: Analysis note ({e}), using standard clip timing.", log_file)
        beat_cuts = None

    # Pick stock video media (strictly 100% UNIQUE video clips with ZERO repeats)
    progress(58, "Loading unique stock video background media...", log_file)
    niche_folders = niche
    if include_dance:
        niche_folders = f"{niche},dance"

    manager = MediaManager(niche=niche_folders)
    manager.scan()
    media_items = []
    if manager.has_media() and manager.videos:
        seen_paths = set()
        unique_videos = []
        for item in manager.videos:
            if str(item.path) not in seen_paths:
                seen_paths.add(str(item.path))
                unique_videos.append(item)
        
        import random
        random.shuffle(unique_videos)
        
        # Determine exact count of unique clips needed (at least cuts + 5 buffer)
        needed_count = max(35, len(beat_cuts) + 5 if beat_cuts else 30)
        media_items = unique_videos[:needed_count] if len(unique_videos) >= needed_count else unique_videos
        log(f"🎬 Loaded {len(media_items)} 100% UNIQUE stock video clips for {len(beat_cuts) if beat_cuts else 'timeline'} cuts (ZERO clip repetition).", log_file)
    else:
        log("No stock video b-roll found. Falling back to dynamic gradients.", log_file)

    progress(60, "Stock media assets ready.", log_file)
    progress(70, f"Compiling video layers (Aspect Ratio: {aspect_ratio}, Style: {caption_style}, Pos: {caption_position})...", log_file)

    video_engine = ReelVideoEngine(
        mood=mood,
        aspect_ratio=aspect_ratio,
        caption_style=caption_style,
        transition_style=transition_style,
        caption_position=caption_position
    )
    
    # Pick hook text (None if mode == "none" for 100% clean video)
    if mode == "none":
        hook = None
    else:
        hook = custom_title if custom_title else song_file.stem.replace("_", " ").title()
        if not custom_title and subtitles and not subtitles[0]["text"].startswith("🎵"):
            hook = subtitles[0]["text"]

    try:
        out_path = video_engine.build_reel(
            media_items=media_items,
            audio_path=str(target_audio_file),
            subtitles=subtitles,
            output_name=output_name,
            hook_text=hook,
            music_path=None,
            show_progress_bar=(mode != "none"),
            beat_cuts=beat_cuts,
            log_callback=lambda m: log(m, log_file),
        )

        # Generate Viral Social Media Package
        try:
            from src.utils.social_strategy import generate_social_package, save_social_kit
            social_data = generate_social_package(
                song_name=custom_title if custom_title else song_file.stem,
                subtitles=subtitles,
                niche=niche,
                language=language or "swahili",
                mood=mood
            )
            saved_kit = save_social_kit(out_path, social_data)
            log(f"🚀 Viral Social Kit created: {Path(saved_kit['txt_path']).name}", log_file)
        except Exception as se:
            log(f"Warning generating social kit: {se}", log_file)

        progress(100, f"✅ Lyric Reel Ready! -> {Path(out_path).name}", log_file)
        log(f"SUCCESS: Rendered reel: {Path(out_path).name}", log_file)
    except Exception as e:
        log(f"ERROR: Lyric reel compilation failed: {e}", log_file)
        sys.exit(1)

    # Clean up temp payload
    try:
        payload_path.unlink()
    except:
        pass

if __name__ == "__main__":
    main()
