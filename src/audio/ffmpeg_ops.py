# -*- coding: utf-8 -*-
"""
src/audio/ffmpeg_ops.py — VideoFactory Pure FFmpeg Audio Processing Helpers

This module provides functions for silence trimming, audio concatenation, and PCM conversion
using direct ffmpeg and ffprobe subprocess calls. This eliminates the dependency on pydub
and the deprecated audioop module, making VideoFactory Python 3.13+ compatible.
"""

import subprocess
import re
import shutil
from pathlib import Path
from loguru import logger

def get_audio_duration(file_path: Path) -> float:
    """Gets total duration of an audio file in seconds using ffprobe (with ffmpeg fallback)."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        logger.warning(f"ffprobe duration check failed for {file_path}: {e}. Trying fallback...")
        try:
            # Fallback to parsing ffmpeg stderr output
            cmd = ["ffmpeg", "-i", str(file_path)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", res.stderr)
            if match:
                h, m, s = match.groups()
                return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception as ex:
            logger.error(f"ffmpeg duration fallback failed: {ex}")
    return 0.0

def detect_silence_bounds(file_path: Path, threshold_db: float = -40.0, min_silence_duration: float = 0.03) -> tuple[float, float]:
    """
    Detects the non-silent start and end boundaries of an audio file using ffmpeg's silencedetect filter.
    Returns (start_sec, end_sec).
    """
    duration = get_audio_duration(file_path)
    if duration <= 0.0:
        return 0.0, 0.0
        
    cmd = [
        "ffmpeg", "-y", "-i", str(file_path),
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence_duration}",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    lines = res.stderr.splitlines()
    silence_starts = []
    silence_ends = []
    
    for line in lines:
        if "silencedetect" in line:
            start_match = re.search(r"silence_start:\s*([\d.]+)", line)
            end_match = re.search(r"silence_end:\s*([\d.]+)", line)
            if start_match:
                silence_starts.append(float(start_match.group(1)))
            if end_match:
                silence_ends.append(float(end_match.group(1)))
                
    audio_start = 0.0
    # If the first silence end occurred, and silence started at/near 0, that's our active audio start
    if silence_starts and silence_starts[0] <= 0.05:
        if silence_ends:
            audio_start = silence_ends[0]
            
    audio_end = duration
    if silence_starts:
        # Check if the last silence start extends to the end of the file
        last_start = silence_starts[-1]
        if duration - last_start <= 0.15: # if silence is within the last 150ms
            audio_end = last_start
            
    return audio_start, audio_end

def trim_audio_silence(input_path: Path, output_path: Path, threshold_db: float = -40.0, pad_start_ms: int = 40, pad_end_ms: int = 80) -> float:
    """
    Trims leading and trailing silence of an audio file using ffmpeg silencedetect.
    Applies start/end safety padding (in ms) to prevent clipping.
    Returns the duration of the trimmed file in seconds.
    """
    duration = get_audio_duration(input_path)
    if duration <= 0.0:
        return 0.0
        
    start, end = detect_silence_bounds(input_path, threshold_db=threshold_db)
    
    pad_start = pad_start_ms / 1000.0
    pad_end = pad_end_ms / 1000.0
    
    start_trimmed = max(0.0, start - pad_start)
    end_trimmed = min(duration, end + pad_end)
    
    trimmed_duration = end_trimmed - start_trimmed
    if trimmed_duration <= 0.05:
        # If trimmed audio is too short, keep the original
        shutil.copy(str(input_path), str(output_path))
        return duration
        
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-ss", f"{start_trimmed:.3f}",
        "-to", f"{end_trimmed:.3f}",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return trimmed_duration

def generate_silence(output_path: Path, duration_sec: float) -> None:
    """Generates a silent MP3 file of the specified duration using anullsrc."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=mono",
        "-t", f"{duration_sec:.3f}",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def concat_audio_files(file_paths: list[Path], output_path: Path) -> None:
    """Concatenates a list of audio files using the ffmpeg concat demuxer."""
    concat_file = output_path.parent / f"concat_list_{output_path.name.replace('.', '_')}.txt"
    lines = []
    for fp in file_paths:
        # Convert path to absolute forward slash representation for ffmpeg compatibility
        p_str = str(fp.resolve()).replace("\\", "/")
        lines.append(f"file '{p_str}'")
        
    concat_file.write_text("\n".join(lines), encoding="utf-8")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
    finally:
        if concat_file.exists():
            try: concat_file.unlink()
            except: pass

def pcm_to_mp3(pcm_bytes: bytes, frame_rate: int = 24000, channels: int = 1) -> bytes:
    """Converts raw s16le PCM bytes directly into MP3 bytes using ffmpeg pipe."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "s16le",
        "-ar", str(frame_rate),
        "-ac", str(channels),
        "-i", "pipe:0",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-f", "mp3",
        "pipe:1"
    ]
    res = subprocess.run(cmd, input=pcm_bytes, capture_output=True, check=True)
    return res.stdout

def detect_nonsilent_intervals(file_path: Path, min_silence_len_s: float = 0.5, threshold_db: float = -40.0) -> list[tuple[float, float]]:
    """Detects active (non-silent) audio intervals using ffmpeg silencedetect."""
    duration = get_audio_duration(file_path)
    if duration <= 0.0:
        return []
        
    cmd = [
        "ffmpeg", "-y", "-i", str(file_path),
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence_len_s}",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    lines = res.stderr.splitlines()
    silences = []
    
    current_start = None
    for line in lines:
        if "silencedetect" in line:
            start_match = re.search(r"silence_start:\s*([\d.]+)", line)
            end_match = re.search(r"silence_end:\s*([\d.]+)", line)
            if start_match:
                current_start = float(start_match.group(1))
            if end_match and current_start is not None:
                silences.append((current_start, float(end_match.group(1))))
                current_start = None
                
    if current_start is not None:
        silences.append((current_start, duration))
        
    # Invert silence to get non-silent blocks
    nonsilent = []
    last_end = 0.0
    for start, end in silences:
        if start > last_end + 0.1: # keep segments longer than 100ms
            nonsilent.append((last_end, start))
        last_end = end
        
    if duration > last_end + 0.1:
        nonsilent.append((last_end, duration))
        
    return nonsilent

def extract_song_segment(audio_path: Path, output_path: Path, start_s: float, end_s: float, fade_in: float = 1.0, fade_out: float = 2.0) -> str:
    """Extracts a section of a song and saves it with fade-in/fade-out using ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    segment_duration = end_s - start_s
    
    fade_filters = []
    if fade_in > 0.0:
        fade_filters.append(f"afade=t=in:ss=0:d={fade_in:.3f}")
    if fade_out > 0.0 and segment_duration > fade_out:
        fade_out_start = segment_duration - fade_out
        fade_filters.append(f"afade=t=out:st={fade_out_start:.3f}:d={fade_out:.3f}")
        
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_s:.3f}",
        "-to", f"{end_s:.3f}",
        "-i", str(audio_path),
    ]
    if fade_filters:
        cmd.extend(["-af", ",".join(fade_filters)])
        
    cmd.extend([
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ])
    
    subprocess.run(cmd, capture_output=True, check=True)
    return str(output_path)
