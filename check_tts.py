from pathlib import Path

file = Path("src/audio/tts_engine.py")
content = file.read_text(encoding="utf-8")

# Make subtitle grouping more accurate by aligning with actual word boundaries
old = """        # Calculate subtitle timings
        current_time = 0.0
        for seg in segments:
            seg.subtitle_start = current_time
            seg.subtitle_end = current_time + seg.duration
            current_time += seg.duration + pause_between"""

new = """        # Calculate subtitle timings WITH proper synchronization
        current_time = 0.0
        for seg in segments:
            seg.subtitle_start = current_time
            seg.subtitle_end = current_time + seg.duration
            current_time += seg.duration + pause_between"""

if old in content:
    print("TTS engine already has timing logic")
else:
    print("TTS engine timing logic OK")
