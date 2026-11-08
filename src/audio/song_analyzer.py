# -*- coding: utf-8 -*-
# ================================================================
# SONG ANALYZER - Detects instrumental vs vocal songs
# Also finds beat drops for cinematic cuts using direct ffmpeg stream
# ================================================================

import subprocess
import numpy as np
from pathlib import Path


def detect_song_type(audio_path):
    """
    Detect if song has vocals or is instrumental.
    Returns: 'vocal', 'instrumental', or 'mixed'
    """
    audio_path = Path(audio_path)

    try:
        # Convert to mono for analysis via ffmpeg stdout
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-f", "s16le",
            "-ac", "1",
            "-ar", "22050",
            "pipe:1"
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            return 'vocal'
            
        samples = np.frombuffer(res.stdout, dtype=np.int16)
        if len(samples) == 0:
            return 'vocal'

        # Method 1: Check filename hints
        name_lower = audio_path.stem.lower()
        instrumental_hints = ['beat', 'instrumental', 'karaoke', 'background',
                              'bgm', 'amapiano', 'afro beat', 'lofi', 'piano']

        for hint in instrumental_hints:
            if hint in name_lower:
                print(f'  Filename suggests INSTRUMENTAL ({hint})')
                return 'instrumental'

        # Method 2: Frequency analysis - vocals are 80Hz-1000Hz
        # If energy is concentrated outside this range, likely instrumental
        sample_rate = 22050

        # Quick FFT
        fft = np.abs(np.fft.rfft(samples[:min(len(samples), sample_rate * 5)]))
        freqs = np.fft.rfftfreq(min(len(samples), sample_rate * 5), 1/sample_rate)

        vocal_range = (freqs >= 80) & (freqs <= 1000)
        total_energy = np.sum(fft)
        vocal_energy = np.sum(fft[vocal_range])

        vocal_ratio = vocal_energy / total_energy if total_energy > 0 else 0
        print(f'  Vocal frequency energy: {vocal_ratio*100:.1f}%')

        if vocal_ratio < 0.35:
            return 'instrumental'
        elif vocal_ratio > 0.55:
            return 'vocal'
        else:
            return 'mixed'

    except Exception as e:
        print(f'  Detection failed: {e}, assuming vocal')
        return 'vocal'


def detect_beat_drops(audio_path, segment_start=0.0, segment_duration=30.0):
    """
    Find moments of high energy (beat drops, choruses).
    Returns list of timestamps where exciting moments happen.
    """
    audio_path = Path(audio_path)

    try:
        # Load specific segment via ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{segment_start:.3f}",
            "-t", f"{segment_duration:.3f}",
            "-i", str(audio_path),
            "-f", "s16le",
            "-ac", "1",
            "-ar", "22050",
            "pipe:1"
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            return []
            
        samples = np.frombuffer(res.stdout, dtype=np.int16)
        if len(samples) == 0:
            return []

        # Analyze in 0.5s chunks (0.5 * 22050 = 11025 samples)
        chunk_size = 11025
        energy_levels = []

        for i in range(0, len(samples), chunk_size):
            chunk = samples[i:i+chunk_size]
            if len(chunk) > 0:
                # Calculate RMS as energy level
                rms = np.sqrt(np.mean(chunk.astype(np.float64) ** 2))
                energy_levels.append((i / 22050.0, rms))

        if not energy_levels:
            return []

        # Find peaks (moments louder than average)
        avg_energy = np.mean([e for _, e in energy_levels])
        threshold = avg_energy * 1.15

        drops = []
        last_drop = -2.0
        for time_s, energy in energy_levels:
            if energy > threshold and (time_s - last_drop) > 2.0:
                drops.append(round(time_s, 2))
                last_drop = time_s

        print(f'  Found {len(drops)} beat drops in segment')
        return drops

    except Exception as e:
        print(f'  Beat detection failed: {e}')
        return []


def create_beat_cuts(song_duration, beat_drops, min_clip=2.0, max_clip=4.0, audio_path=None):
    """
    Create video cut timing based on beat drops.
    
    If audio_path is provided, uses the advanced beat_sync engine for
    proper BPM-driven, energy-adaptive cut points.
    Falls back to simple beat-drop-based cutting otherwise.
    
    Returns subtitle-like list with timing for clip changes.
    """
    # Try advanced beat-synced cut points if audio path is available
    if audio_path:
        try:
            from src.audio.beat_sync import generate_beat_cut_points
            cuts = generate_beat_cut_points(audio_path, min_clip=min_clip, max_clip=max_clip)
            if cuts:
                # Convert to the expected format (add empty 'text' field)
                return [{'text': '', 'start': c['start'], 'end': c['end']} for c in cuts]
        except Exception as e:
            print(f"  Beat sync engine unavailable ({e}), using fallback")

    # Fallback: original simple approach
    cuts = []

    if not beat_drops:
        # No beats detected - create rhythmic cuts every 2.5s
        num_cuts = max(8, int(song_duration / 2.5))
        cut_dur = song_duration / num_cuts
        for i in range(num_cuts):
            cuts.append({
                'text': '',
                'start': round(i * cut_dur, 3),
                'end': round((i + 1) * cut_dur, 3),
            })
        return cuts

    # Use beat drops as cut points
    current = 0.0
    for drop in beat_drops:
        if drop - current >= min_clip:
            cuts.append({
                'text': '',
                'start': round(current, 3),
                'end': round(drop, 3),
            })
            current = drop

    # Add final segment
    if song_duration - current > 0.5:
        cuts.append({
            'text': '',
            'start': round(current, 3),
            'end': round(song_duration, 3),
        })

    # Ensure cuts aren't too long
    final_cuts = []
    for cut in cuts:
        dur = cut['end'] - cut['start']
        if dur > max_clip:
            # Split this segment
            num_sub = max(1, int(dur / max_clip))
            sub_dur = dur / num_sub
            for j in range(num_sub):
                final_cuts.append({
                    'text': '',
                    'start': round(cut['start'] + j * sub_dur, 3),
                    'end': round(cut['start'] + (j + 1) * sub_dur, 3),
                })
        else:
            final_cuts.append(cut)

    return final_cuts


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        song = sys.argv[1]
        print(f'Analyzing: {song}')
        song_type = detect_song_type(song)
        print(f'Song type: {song_type}')
        if song_type != 'instrumental':
            drops = detect_beat_drops(song, 0, 30)
            print(f'Beat drops: {drops}')
