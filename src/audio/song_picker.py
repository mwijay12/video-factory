# -*- coding: utf-8 -*-
# ================================================================
# SMART SONG PROCESSOR
# - Auto picks random song or specific song
# - Finds the BEST 15-40s peak viral segment (chorus/drop/anthem)
# - Supports vocal songs (lyrics mode) & instrumental beats
# ================================================================

import random
import json
import subprocess
import numpy as np
from pathlib import Path


SONG_FOLDERS = {
    'swahili':  Path('assets/songs/swahili'),
    'english':  Path('assets/songs/english'),
    'mixed':    Path('assets/songs/mixed'),
    'beats':    Path('assets/songs/beats'),
}

AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']


def ensure_song_folders():
    for folder in SONG_FOLDERS.values():
        folder.mkdir(parents=True, exist_ok=True)


def scan_all_songs():
    ensure_song_folders()
    all_songs = {}
    for category, folder in SONG_FOLDERS.items():
        if not folder.exists():
            continue
        songs = []
        for f in folder.iterdir():
            if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS:
                songs.append(f)
        all_songs[category] = songs
    return all_songs


def list_songs_pretty():
    songs = scan_all_songs()
    print('')
    print('=' * 62)
    print('  AVAILABLE SONGS')
    print('=' * 62)
    total = 0
    for category, files in songs.items():
        if not files:
            continue
        print(f'')
        print(f'  [{category.upper()}] - {len(files)} songs')
        for i, f in enumerate(files, 1):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f'    {i}. {f.name} ({size_mb:.1f} MB)')
            total += 1
    print('')
    print(f'  Total: {total} songs')
    print('=' * 62)
    return songs


def pick_random_song(category=None):
    all_songs = scan_all_songs()
    
    if category and category in all_songs and all_songs[category]:
        return random.choice(all_songs[category])
    
    pool = []
    for cat, files in all_songs.items():
        if cat != 'beats':
            pool.extend(files)
    
    if not pool:
        return None
    return random.choice(pool)


def find_song_by_name(name):
    name_lower = name.lower().strip()
    all_songs = scan_all_songs()
    
    for category, files in all_songs.items():
        for f in files:
            if name_lower in f.name.lower() or name_lower == f.stem.lower():
                return f
    return None


def get_best_segment(audio_path, target_duration=30, min_dur=15, max_dur=45):
    """
    Finds the highest energy (chorus/drop/anthem peak) segment of the song.
    Skips silent intros & fades, locates the most impactful viral segment.
    """
    from src.audio.ffmpeg_ops import get_audio_duration
    
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return 0, target_duration

    try:
        total_duration = get_audio_duration(audio_path)
        print(f'  Song duration: {total_duration:.1f}s')

        if total_duration <= max_dur:
            print(f'  Song is short ({total_duration:.1f}s), using full song')
            return 0, total_duration

        # Use fast mono sub-sampling to compute RMS energy curve
        sr = 11025
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-f", "s16le",
            "-ac", "1",
            "-ar", str(sr),
            "pipe:1"
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            # Fallback: take middle section
            start = max(0, (total_duration - target_duration) / 2)
            return round(start, 2), round(min(start + target_duration, total_duration), 2)

        samples = np.frombuffer(res.stdout, dtype=np.int16)
        if len(samples) < sr * 5:
            return 0, min(total_duration, target_duration)

        win_samples = int(target_duration * sr)
        step_samples = int(1.0 * sr)  # Step every 1.0s

        # Evaluate windows between 12% and 88% of the song length (skips intro/outro)
        start_bound = int(total_duration * 0.12 * sr)
        end_bound = int(total_duration * 0.88 * sr) - win_samples
        if end_bound <= start_bound:
            start_bound = 0
            end_bound = len(samples) - win_samples

        best_start_s = start_bound / sr
        max_energy = -1.0

        for s_idx in range(start_bound, max(start_bound + 1, end_bound), step_samples):
            chunk = samples[s_idx:s_idx + win_samples].astype(np.float64)
            if len(chunk) == 0:
                continue
            rms = np.sqrt(np.mean(chunk ** 2))
            if rms > max_energy:
                max_energy = rms
                best_start_s = s_idx / sr

        best_end_s = min(total_duration, best_start_s + target_duration)
        actual_dur = best_end_s - best_start_s

        print(f'  🔥 Detected Peak Viral Segment: {best_start_s:.1f}s -> {best_end_s:.1f}s ({actual_dur:.1f}s)')
        return round(best_start_s, 2), round(best_end_s, 2)

    except Exception as e:
        print(f'  Peak segment detection failed: {e}')
        # Safe fallback: middle section
        start = max(0, (total_duration - target_duration) / 2) if 'total_duration' in locals() else 0
        return round(start, 2), round(start + target_duration, 2)


def extract_song_segment(audio_path, output_path, start_s, end_s, fade_in=1.0, fade_out=2.0):
    """Extract a section of song and save with smooth fade in/out."""
    from src.audio.ffmpeg_ops import extract_song_segment as ffmpeg_extract
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    return ffmpeg_extract(audio_path, output_path, start_s, end_s, fade_in=fade_in, fade_out=fade_out)
