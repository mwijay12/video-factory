# ================================================================
# VIDEOFACTORY - CINEMATIC REEL ENGINE
# Professional vertical reel compositor
#
# Features:
#   - Cinematic Ken Burns zoom on images
#   - Smooth crossfade transitions between clips
#   - Dynamic subtitle animations (fade + slide)
#   - Hook text with cinematic entrance
#   - Color grading overlay per mood
#   - Vignette border effect
#   - Background music ducking under voice
#   - Fallback cinematic gradient if no media
#   - Full data saver mode support
#   - Handles videos + images mixed
#   - Auto crop to vertical 1080x1920
#   - Per-clip random start point for variety
# ================================================================

import json
import random
import time
from pathlib import Path

import numpy as np
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
    ImageEnhance,
)

from moviepy import (
    VideoFileClip,
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    ColorClip,
    concatenate_videoclips,
    concatenate_audioclips,
)
from proglog import ProgressBarLogger

import config.settings
from config.settings import (
    OUTPUT_DIR,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    VIDEO_CODEC,
    AUDIO_CODEC,
    BITRATE,
    PRESET,
    VIDEO_CRF,
    AUDIO_BITRATE,
    VIDEO_SHARPEN,
    ENCODE_THREADS,
    VIDEO_QUALITY_PRESET,
    SUBTITLES_ENABLED,
    SUBTITLE_STYLE,
    BACKGROUND_MUSIC_ENABLED,
    BACKGROUND_MUSIC_VOLUME,
    TARGET_DURATION,
    HOOK_CONFIG,
    NICHE,
    NICHE_CONFIG,
)


# ================================================================
# MOOD COLOR GRADING PRESETS
# Each mood adds a subtle color tint overlay
# ================================================================

MOOD_GRADES = {
    "peaceful": {
        "tint": (180, 210, 255),
        "tint_opacity": 18,
        "brightness": 1.05,
        "contrast": 1.08,
        "saturation": 1.10,
    },
    "powerful": {
        "tint": (255, 200, 160),
        "tint_opacity": 20,
        "brightness": 1.00,
        "contrast": 1.18,
        "saturation": 1.20,
    },
    "hopeful": {
        "tint": (255, 240, 180),
        "tint_opacity": 16,
        "brightness": 1.08,
        "contrast": 1.10,
        "saturation": 1.15,
    },
    "emotional": {
        "tint": (200, 180, 255),
        "tint_opacity": 22,
        "brightness": 0.98,
        "contrast": 1.15,
        "saturation": 0.95,
    },
    "cinematic": {
        "tint": (255, 220, 180),
        "tint_opacity": 24,
        "brightness": 0.95,
        "contrast": 1.22,
        "saturation": 0.90,
    },
    "teal_orange": {
        "tint": (0, 180, 220),
        "tint_opacity": 25,
        "brightness": 0.96,
        "contrast": 1.25,
        "saturation": 1.25,
    },
    "cyberpunk": {
        "tint": (255, 0, 200),
        "tint_opacity": 22,
        "brightness": 0.95,
        "contrast": 1.28,
        "saturation": 1.30,
    },
    "gospel_gold": {
        "tint": (255, 215, 100),
        "tint_opacity": 22,
        "brightness": 1.08,
        "contrast": 1.12,
        "saturation": 1.18,
    },
    "vintage": {
        "tint": (240, 210, 170),
        "tint_opacity": 24,
        "brightness": 0.94,
        "contrast": 1.15,
        "saturation": 0.85,
    },
    "holy": {
        "tint": (255, 255, 220),
        "tint_opacity": 20,
        "brightness": 1.10,
        "contrast": 1.05,
        "saturation": 0.85,
    },
    "default": {
        "tint": (200, 200, 200),
        "tint_opacity": 10,
        "brightness": 1.00,
        "contrast": 1.05,
        "saturation": 1.00,
    },
}


class MoviePyLiveProgressLogger(ProgressBarLogger):
    """Custom proglog progress logger that outputs real-time frame progress
    (e.g., 53/945) and emits PROGRESS:N% markers with FPS and ETA for the web dashboard."""

    def __init__(self, log_callback=None):
        super().__init__()
        self.log_callback = log_callback
        self.last_frame = 0
        self.last_log_time = 0
        self.start_encode_time = None
        self.total_frames = 0

    def bars_callback(self, bar, attr, value, old_value=None):
        if bar == "t":
            if attr == "total":
                self.total_frames = int(value or 0)
                self.start_encode_time = time.time()
            elif attr == "index" and self.total_frames > 0:
                current_frame = int(value or 0)
                total = self.total_frames
                pct = int((current_frame / total) * 100)
                now = time.time()

                if not self.start_encode_time:
                    self.start_encode_time = now

                # Emit updates every 10 frames, every 0.8 seconds, or on completion
                if (current_frame - self.last_frame >= 10) or (now - self.last_log_time >= 0.8) or (current_frame >= total):
                    self.last_frame = current_frame
                    self.last_log_time = now

                    # Calculate FPS and ETA
                    elapsed = max(0.001, now - self.start_encode_time)
                    fps = current_frame / elapsed
                    remaining_frames = max(0, total - current_frame)
                    eta_sec = int(remaining_frames / max(0.1, fps)) if fps > 0 else 0

                    # Map frame progress cleanly from 80% -> 98% in the overall pipeline
                    overall_pct = min(98, int(80 + (current_frame / total) * 18))
                    
                    # Format human-readable ETA
                    if eta_sec > 60:
                        eta_str = f"~{eta_sec // 60}m {eta_sec % 60}s left"
                    else:
                        eta_str = f"~{eta_sec}s left"

                    step_msg = f"🎞️ Encoding frame {current_frame}/{total} ({pct}%) • {fps:.1f} fps • {eta_str}"
                    terminal_line = f"  [MoviePy] Frame {current_frame}/{total} ({pct}%) | {fps:.1f} fps | {eta_str} | Active encoder..."

                    if self.log_callback:
                        self.log_callback(f"PROGRESS:{overall_pct}% STEP:{step_msg}")
                        self.log_callback(terminal_line)
                    else:
                        print(f"PROGRESS:{overall_pct}% STEP:{step_msg}", flush=True)
                        print(terminal_line, flush=True)


# ================================================================
# CINEMATIC GRADIENT FALLBACK BACKGROUNDS
# Used when no stock media is available
# ================================================================

CINEMATIC_GRADIENTS = [
    {"name": "deep_night",    "top": (5, 5, 20),      "bottom": (20, 30, 60)},
    {"name": "golden_hour",   "top": (80, 30, 10),    "bottom": (220, 120, 30)},
    {"name": "holy_dawn",     "top": (60, 40, 10),    "bottom": (240, 200, 100)},
    {"name": "dark_forest",   "top": (5, 20, 5),      "bottom": (20, 60, 20)},
    {"name": "storm",         "top": (10, 10, 10),    "bottom": (40, 40, 60)},
    {"name": "ocean_deep",    "top": (5, 10, 40),     "bottom": (10, 60, 120)},
    {"name": "sunset_fire",   "top": (80, 10, 5),     "bottom": (220, 80, 20)},
    {"name": "purple_glory",  "top": (20, 5, 40),     "bottom": (80, 20, 120)},
]


# ================================================================
# HELPERS
# ================================================================

def download_sfx_online(query, dest_path):
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_template = str(dest_path.with_name(f"temp_{dest_path.stem}.%(ext)s"))
    
    import subprocess
    print(f"  Attempting to download premium sound effect online for '{query}'...")
    try:
        res = subprocess.run([
            "yt-dlp",
            "-o", temp_template,
            "--no-playlist",
            "--extract-audio",
            "--audio-format", "wav",
            f"ytsearch1:{query}"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        
        if res.returncode == 0:
            temp_wav = dest_path.with_name(f"temp_{dest_path.stem}.wav")
            if temp_wav.exists():
                temp_wav.rename(dest_path)
                print(f"  Successfully downloaded premium sfx: {dest_path.name}")
                return True
    except Exception as e:
        print(f"  Failed downloading premium sfx: {e}")
    return False

def ensure_hook_assets():
    hooks_dir = Path("assets/hooks")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    default_whoosh = hooks_dir / "whoosh.wav"
    # Re-generate if missing or if old harsh noise generator was used (<140KB or missing)
    if not default_whoosh.exists() or default_whoosh.stat().st_size == 132344:
        try:
            print("  Synthesizing smooth cinematic whoosh sound effect...")
            import wave
            import math
            import struct
            import random
            
            sample_rate = 44100
            duration = 1.2
            num_samples = int(duration * sample_rate)
            
            # Simple lowpass state for filtered pink noise
            prev_noise = 0.0
            
            with wave.open(str(default_whoosh), 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                
                for i in range(num_samples):
                    t = i / sample_rate
                    # Gentle frequency sweep rising from 80Hz to 280Hz, settling back to 110Hz
                    freq = 80 + 200 * math.sin(math.pi * t / duration)
                    sine_val = math.sin(2 * math.pi * freq * t)
                    sub_val = math.sin(math.pi * freq * t)
                    
                    # Lowpass filtered noise (prevents harsh ear screeching)
                    raw_noise = random.uniform(-1.0, 1.0)
                    prev_noise = prev_noise * 0.88 + raw_noise * 0.12
                    
                    # Smooth parabolic bell envelope
                    envelope = math.sin(math.pi * t / duration) ** 3
                    
                    # Blended warm cinematic swoosh
                    val = (0.50 * sine_val + 0.25 * sub_val + 0.25 * prev_noise) * envelope
                    sample = int(val * 7500)
                    
                    # Clamp sample to safe 16-bit limits
                    sample = max(-32768, min(32767, sample))
                    wf.writeframesraw(struct.pack('<h', sample))
            print("  Default cinematic whoosh sound generated successfully.")
        except Exception as e:
            print(f"  Warning: Failed to generate default whoosh sound: {e}")

def ensure_output():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    ensure_hook_assets()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_file(folder, pattern):
    files = sorted(
        Path(folder).glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return files[0] if files else None


def now_stamp():
    return time.strftime("%Y%m%d_%H%M%S")


def get_active_mood():
    niche_conf = NICHE_CONFIG.get(NICHE, {})
    moods = niche_conf.get("moods", ["default"])
    return random.choice(moods)


def get_font(size=60, bold=True):
    # 1. Check if a custom font path is set in SUBTITLE_STYLE
    font_path = SUBTITLE_STYLE.get("font_path")
    if font_path and Path(font_path).exists():
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except Exception as e:
            print(f"Failed to load custom font from config {font_path}: {e}")
            
    # 2. Auto-scan assets directory for any .ttf font file as fallback
    fonts_dir = Path("assets/fonts")
    if fonts_dir.exists():
        ttf_files = list(fonts_dir.glob("*.ttf"))
        if ttf_files:
            try:
                # Prefer bold or first available font
                bold_fonts = [f for f in ttf_files if "bold" in f.name.lower() or "bd" in f.name.lower()]
                selected_font = bold_fonts[0] if (bold and bold_fonts) else ttf_files[0]
                return ImageFont.truetype(str(selected_font), size=size)
            except Exception as e:
                print(f"Failed to load custom font from assets/fonts: {e}")
                
    # 3. Check root assets directory
    root_assets = Path("assets")
    if root_assets.exists():
        ttf_files = list(root_assets.glob("*.ttf"))
        if ttf_files:
            try:
                return ImageFont.truetype(str(ttf_files[0]), size=size)
            except:
                pass

    candidates = []
    if bold:
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
            "C:/Windows/Fonts/georgiab.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/verdana.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def get_emoji_font(size):
    path = "C:/Windows/Fonts/seguiemj.ttf"
    try:
        return ImageFont.truetype(path, size=size)
    except:
        return None


def is_emoji(char):
    o = ord(char)
    return (
        0x1F300 <= o <= 0x1F9FF or  # Emoticons, symbols, pictographs
        0x2600 <= o <= 0x27BF or    # Dingbats, misc symbols
        0xfe00 <= o <= 0xfe0f or    # Variation selector
        o > 0xffff                  # Supplementary planes (most emojis are here)
    )


def get_text_width_with_emoji(draw, text, font, emoji_font, stroke_width=3):
    if not emoji_font:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        return bbox[2] - bbox[0]
    w = 0
    for char in text:
        current_font = emoji_font if is_emoji(char) else font
        bbox = draw.textbbox((0, 0), char, font=current_font, stroke_width=stroke_width)
        w += (bbox[2] - bbox[0])
    return w


def draw_text_with_emoji(draw, position, text, font, emoji_font, fill, stroke_width, stroke_fill):
    x, y = position
    if not emoji_font:
        draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        return
    for char in text:
        current_font = emoji_font if is_emoji(char) else font
        draw.text((x, y), char, font=current_font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        bbox = draw.textbbox((0, 0), char, font=current_font, stroke_width=stroke_width)
        x += (bbox[2] - bbox[0])


def wrap_text(draw, text, font, max_width, stroke_width=3, emoji_font=None):
    from config.settings import SUBTITLE_STYLE
    max_words = SUBTITLE_STYLE.get("max_words_per_line", 4)
    
    words = text.split()
    lines = []
    current_words = []
    for word in words:
        if len(current_words) >= max_words:
            if current_words:
                lines.append(" ".join(current_words))
            current_words = [word]
            continue
            
        test_words = current_words + [word]
        test_text = " ".join(test_words)
        w = get_text_width_with_emoji(draw, test_text, font, emoji_font, stroke_width)
        if w <= max_width:
            current_words = test_words
        else:
            if current_words:
                lines.append(" ".join(current_words))
            current_words = [word]
    if current_words:
        lines.append(" ".join(current_words))

    # Enforce strictly MAX 2 ROWS per caption card!
    if len(lines) > 2 and len(words) >= 2:
        mid = (len(words) + 1) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        lines = [line1, line2]

    return lines


# ================================================================
# IMAGE COLOR GRADING
# ================================================================

def apply_color_grade(pil_image, mood="default"):
    grade = MOOD_GRADES.get(mood, MOOD_GRADES["default"])

    enhancer = ImageEnhance.Brightness(pil_image)
    img = enhancer.enhance(grade["brightness"])

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(grade["contrast"])

    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(grade["saturation"])

    tint_r, tint_g, tint_b = grade["tint"]
    opacity = grade["tint_opacity"]

    tint_layer = Image.new("RGB", img.size, (tint_r, tint_g, tint_b))
    tint_alpha = Image.new("L", img.size, opacity)

    img = img.convert("RGB")
    img.paste(tint_layer, mask=tint_alpha)

    return img


# ================================================================
# VIGNETTE EFFECT
# Makes edges darker - very cinematic
# ================================================================

def create_vignette(width, height, intensity=0.55):
    vignette = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(vignette)

    steps = 120
    for i in range(steps, 0, -1):
        ratio = i / steps
        alpha = int((1 - ratio ** 1.8) * 255 * intensity)
        margin_x = int((width // 2) * (1 - ratio))
        margin_y = int((height // 2) * (1 - ratio))
        draw.rectangle(
            [(margin_x, margin_y), (width - margin_x, height - margin_y)],
            fill=alpha
        )

    dark = Image.new("RGB", (width, height), (0, 0, 0))
    base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    base.paste(dark, mask=vignette)
    return np.array(base, dtype=np.uint8)


# Precompute vignette once - faster rendering
VIGNETTE_ARRAY = create_vignette(1080, 1920, intensity=0.50)
VIGNETTE_CLIP = ImageClip(VIGNETTE_ARRAY, transparent=True)


# ================================================================
# CINEMATIC GRADIENT BACKGROUND
# Used as fallback when no local media is available
# ================================================================

def make_gradient_frame(width, height, top_color, bottom_color):
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    r1, g1, b1 = top_color
    r2, g2, b2 = bottom_color
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return np.array(img, dtype=np.uint8)


def make_cinematic_gradient_clip(duration, index=0):
    grad = CINEMATIC_GRADIENTS[index % len(CINEMATIC_GRADIENTS)]
    frame = make_gradient_frame(1080, 1920, grad["top"], grad["bottom"])
    clip = ImageClip(frame).with_duration(duration)
    return clip


# ================================================================
# SUBTITLE IMAGE BUILDER
# ================================================================

def build_subtitle_image(
    text,
    width=980,
    font_size=56,
    text_color="white",
    stroke_color="black",
    stroke_width=3,
    bg_opacity=145,
    mood="peaceful"
):
    canvas_height = 380
    img = Image.new("RGBA", (width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(font_size, bold=True)
    emoji_font = get_emoji_font(font_size)

    max_text_width = width - 80
    lines = wrap_text(draw, text, font, max_text_width, stroke_width, emoji_font)

    metrics = []
    for line in lines:
        line_w = get_text_width_with_emoji(draw, line, font, emoji_font, stroke_width)
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        metrics.append({
            "width": line_w,
            "height": bbox[3] - bbox[1],
        })

    if not metrics:
        return np.array(img, dtype=np.uint8)

    line_spacing = 14
    total_h = sum(m["height"] for m in metrics) + line_spacing * (len(lines) - 1)
    max_w = max(m["width"] for m in metrics)

    pad_x, pad_y = 36, 26
    box_w = min(width - 40, max_w + pad_x * 2)
    box_h = total_h + pad_y * 2
    box_x = (width - box_w) // 2
    box_y = (canvas_height - box_h) // 2

    # Mood-colored subtle bottom border on subtitle box
    mood_tints = {
        "peaceful": (100, 160, 255),
        "powerful": (255, 140, 60),
        "hopeful":  (255, 220, 80),
        "emotional":(160, 100, 255),
        "holy":     (255, 255, 180),
        "default":  (200, 200, 200),
    }
    accent = mood_tints.get(mood, (200, 200, 200))

    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_w, box_y + box_h)],
        radius=30,
        fill=(0, 0, 0, bg_opacity)
    )

    draw.rounded_rectangle(
        [(box_x, box_y + box_h - 6), (box_x + box_w, box_y + box_h)],
        radius=6,
        fill=(*accent, 200)
    )

    cur_y = box_y + pad_y
    for i, line in enumerate(lines):
        lw = metrics[i]["width"]
        lh = metrics[i]["height"]
        lx = (width - lw) // 2

        draw_text_with_emoji(
            draw,
            (lx, cur_y),
            line,
            font,
            emoji_font,
            text_color,
            stroke_width,
            stroke_color
        )
        cur_y += lh + line_spacing

    return np.array(img, dtype=np.uint8)


def build_subtitle_image_karaoke(
    text,
    active_word_index=-1,
    width=980,
    font_size=56,
    text_color="white",
    stroke_color="black",
    stroke_width=3,
    bg_opacity=145,
    mood="peaceful"
):
    canvas_height = 380
    img = Image.new("RGBA", (width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(font_size, bold=True)
    emoji_font = get_emoji_font(font_size)

    max_text_width = width - 80
    lines = wrap_text(draw, text, font, max_text_width, stroke_width, emoji_font)

    metrics = []
    for line in lines:
        line_w = get_text_width_with_emoji(draw, line, font, emoji_font, stroke_width)
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        metrics.append({
            "width": line_w,
            "height": bbox[3] - bbox[1],
        })

    if not metrics:
        return np.array(img, dtype=np.uint8)

    line_spacing = 14
    total_h = sum(m["height"] for m in metrics) + line_spacing * (len(lines) - 1)
    max_w = max(m["width"] for m in metrics)

    pad_x, pad_y = 36, 26
    box_w = min(width - 40, max_w + pad_x * 2)
    box_h = total_h + pad_y * 2
    box_x = (width - box_w) // 2
    box_y = (canvas_height - box_h) // 2

    # Mood-colored subtle bottom border on subtitle box
    mood_tints = {
        "peaceful": (100, 160, 255),
        "powerful": (255, 140, 60),
        "hopeful":  (255, 220, 80),
        "emotional":(160, 100, 255),
        "holy":     (255, 255, 180),
        "default":  (200, 200, 200),
    }
    accent = mood_tints.get(mood, (200, 200, 200))

    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_w, box_y + box_h)],
        radius=30,
        fill=(0, 0, 0, bg_opacity)
    )

    draw.rounded_rectangle(
        [(box_x, box_y + box_h - 6), (box_x + box_w, box_y + box_h)],
        radius=6,
        fill=(*accent, 200)
    )

    # Highlight color definition
    karaoke_colors = {
        "peaceful": (255, 225, 0),   # Bright yellow
        "powerful": (255, 136, 0),   # Orange
        "hopeful":  (0, 240, 255),   # Cyan
        "emotional":(255, 0, 180),   # Pink/Magenta
        "holy":     (255, 215, 0),   # Gold
        "default":  (255, 225, 0),   # Bright yellow
    }
    highlight_color = karaoke_colors.get(mood, karaoke_colors["default"])

    # Space width measurement
    space_bbox = draw.textbbox((0, 0), " ", font=font, stroke_width=stroke_width)
    space_w = space_bbox[2] - space_bbox[0]

    cur_y = box_y + pad_y
    word_counter = 0

    for i, line in enumerate(lines):
        lw = metrics[i]["width"]
        lh = metrics[i]["height"]
        lx = (width - lw) // 2

        words_in_line = line.split()
        cur_x = lx

        for word in words_in_line:
            is_active = (word_counter == active_word_index)
            word_w = get_text_width_with_emoji(draw, word, font, emoji_font, stroke_width)

            draw_text_with_emoji(
                draw,
                (cur_x, cur_y),
                word,
                font,
                emoji_font,
                highlight_color if is_active else text_color,
                stroke_width,
                stroke_color
            )
            cur_x += word_w + space_w
            word_counter += 1

        cur_y += lh + line_spacing

    return np.array(img, dtype=np.uint8)


# ================================================================
# SUBTITLE TYPING EFFECT IMAGE BUILDER
# ================================================================

def build_subtitle_image_typing(
    visible_text,
    width=980,
    font_size=56,
    text_color="white",
    stroke_color="black",
    stroke_width=3,
    bg_opacity=155,
    mood="peaceful"
):
    """Renders a typing effect frame with a dynamic cursor indicator."""
    canvas_height = 380
    img = Image.new("RGBA", (width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(font_size, bold=True)
    emoji_font = get_emoji_font(font_size)

    text_with_cursor = visible_text + "▌"
    max_text_width = width - 80
    lines = wrap_text(draw, text_with_cursor, font, max_text_width, stroke_width, emoji_font)

    metrics = []
    for line in lines:
        line_w = get_text_width_with_emoji(draw, line, font, emoji_font, stroke_width)
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        metrics.append({
            "width": line_w,
            "height": bbox[3] - bbox[1],
        })

    if not metrics:
        return np.array(img, dtype=np.uint8)

    line_spacing = 14
    total_h = sum(m["height"] for m in metrics) + line_spacing * (len(lines) - 1)
    max_w = max(m["width"] for m in metrics)

    pad_x, pad_y = 36, 26
    box_w = min(width - 40, max_w + pad_x * 2)
    box_h = total_h + pad_y * 2
    box_x = (width - box_w) // 2
    box_y = (canvas_height - box_h) // 2

    mood_tints = {
        "peaceful": (100, 160, 255),
        "powerful": (255, 140, 60),
        "hopeful":  (255, 220, 80),
        "emotional":(160, 100, 255),
        "holy":     (255, 255, 180),
        "default":  (200, 200, 200),
    }
    accent = mood_tints.get(mood, (200, 200, 200))

    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_w, box_y + box_h)],
        radius=30,
        fill=(0, 0, 0, bg_opacity)
    )

    draw.rounded_rectangle(
        [(box_x, box_y + box_h - 6), (box_x + box_w, box_y + box_h)],
        radius=6,
        fill=(*accent, 220)
    )

    cur_y = box_y + pad_y
    for i, line in enumerate(lines):
        lw = metrics[i]["width"]
        lh = metrics[i]["height"]
        lx = (width - lw) // 2

        draw_text_with_emoji(
            draw,
            (lx, cur_y),
            line,
            font,
            emoji_font,
            text_color,
            stroke_width,
            stroke_color
        )
        cur_y += lh + line_spacing

    return np.array(img, dtype=np.uint8)


# ================================================================
# HOOK TEXT IMAGE BUILDER
# ================================================================

def build_hook_image(text, width=1020, mood="peaceful"):
    canvas_height = 500
    img = Image.new("RGBA", (width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(82, bold=True)
    emoji_font = get_emoji_font(82)

    max_text_width = width - 100
    lines = wrap_text(draw, text, font, max_text_width, stroke_width=5, emoji_font=emoji_font)

    metrics = []
    for line in lines:
        line_w = get_text_width_with_emoji(draw, line, font, emoji_font, stroke_width=5)
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=5)
        metrics.append({
            "width": line_w,
            "height": bbox[3] - bbox[1],
        })

    if not metrics:
        return np.array(img, dtype=np.uint8)

    line_spacing = 18
    total_h = sum(m["height"] for m in metrics) + line_spacing * (len(lines) - 1)
    max_w = max(m["width"] for m in metrics)

    pad_x, pad_y = 50, 38
    box_w = min(width - 60, max_w + pad_x * 2)
    box_h = total_h + pad_y * 2
    box_x = (width - box_w) // 2
    box_y = (canvas_height - box_h) // 2

    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_w, box_y + box_h)],
        radius=40,
        fill=(0, 0, 0, 175)
    )

    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_w, box_y + 7)],
        radius=6,
        fill=(255, 255, 255, 160)
    )

    cur_y = box_y + pad_y
    for i, line in enumerate(lines):
        lw = metrics[i]["width"]
        lh = metrics[i]["height"]
        lx = (width - lw) // 2

        draw_text_with_emoji(
            draw,
            (lx, cur_y),
            line,
            font,
            emoji_font,
            "white",
            5,
            "black"
        )
        cur_y += lh + line_spacing

    return np.array(img, dtype=np.uint8)


# ================================================================
# PROGRESS BAR (top of reel - shows progress)
# ================================================================

def create_progress_bar_clip(total_duration, width=1080, height=8):
    def make_frame(t):
        progress = min(1.0, max(0.0, t / max(0.01, total_duration)))
        img = Image.new("RGBA", (width, height), (0, 0, 0, 80))
        draw = ImageDraw.Draw(img)
        bar_width = int(width * progress)
        if bar_width > 0:
            draw.rectangle([(0, 0), (bar_width, height)], fill=(255, 255, 255, 200))
        return np.array(img, dtype=np.uint8)

    from moviepy import VideoClip
    clip = VideoClip(make_frame, duration=total_duration)
    return clip.with_position(("center", 0))


# ================================================================
# MAIN CINEMATIC REEL ENGINE
# ================================================================

class ReelVideoEngine:

    def __init__(self, mood=None, aspect_ratio="9:16", caption_style="typing", transition_style="whip_zoom", caption_position="center"):
        ensure_output()
        self.aspect_ratio = aspect_ratio or "9:16"
        self.caption_style = caption_style or "typing"
        self.transition_style = transition_style or "whip_zoom"
        self.caption_position = caption_position or "center"
        ASPECT_MAP = {
            "9:16": (1080, 1920),
            "16:9": (1920, 1080),
            "1:1": (1080, 1080),
            "4:5": (1080, 1350),
        }
        dims = ASPECT_MAP.get(self.aspect_ratio, (1080, 1920))
        self.width = dims[0]
        self.height = dims[1]
        self.fps = FPS
        self.mood = mood or get_active_mood()
        print(f"\nReel Engine initialized | Mood: {self.mood} | Ratio: {self.aspect_ratio} ({self.width}x{self.height}) | Style: {self.caption_style} | Position: {self.caption_position} @ {self.fps}fps\n")

    # ----------------------------------------------------------------
    # FIT MEDIA TO TARGET FRAME ASPECT RATIO
    # ----------------------------------------------------------------

    def _fit_to_aspect(self, clip):
        target_ratio = self.width / self.height
        clip_ratio = clip.w / clip.h

        if clip_ratio > target_ratio:
            clip = clip.resized(height=self.height)
        else:
            clip = clip.resized(width=self.width)

        if clip.w < self.width or clip.h < self.height:
            clip = clip.resized((self.width, self.height))

        clip = clip.cropped(
            x_center=clip.w / 2,
            y_center=clip.h / 2,
            width=self.width,
            height=self.height
        )

        return clip

    # ----------------------------------------------------------------
    # KEN BURNS ZOOM EFFECT ON IMAGE
    # Creates the cinematic slow zoom that makes images come alive
    # ----------------------------------------------------------------

    def _apply_ken_burns(self, image_clip, duration, zoom_in=True, intensity=0.06,
                          pan_x=0.0, pan_y=0.0):
        """Cinematic Ken Burns with optional X/Y pan drift for richer motion parallax.
        pan_x / pan_y are fractional offsets applied to the crop origin (range -0.05..0.05).
        """
        start_scale = 1.0 if zoom_in else 1.0 + intensity
        end_scale = 1.0 + intensity if zoom_in else 1.0

        w = image_clip.w
        h = image_clip.h

        def make_frame(t):
            progress = t / max(duration, 0.01)
            scale = start_scale + (end_scale - start_scale) * progress
            new_w = int(w * scale)
            new_h = int(h * scale)

            frame = image_clip.get_frame(0)
            img = Image.fromarray(frame.astype("uint8")).resize(
                (new_w, new_h), Image.Resampling.LANCZOS
            )

            # Center crop with progressive pan drift
            base_x = (new_w - w) // 2
            base_y = (new_h - h) // 2
            drift_x = int(pan_x * w * progress)
            drift_y = int(pan_y * h * progress)
            x = max(0, min(base_x + drift_x, new_w - w))
            y = max(0, min(base_y + drift_y, new_h - h))

            cropped = np.array(img.crop((x, y, x + w, y + h)), dtype=np.uint8)
            return cropped

        from moviepy import VideoClip
        return VideoClip(make_frame, duration=duration)

    # ----------------------------------------------------------------
    # COLOR GRADE A CLIP
    # ----------------------------------------------------------------

    def _grade_clip(self, clip, mood=None):
        mood = mood or self.mood
        if mood in ["default", "normal", None]:
            return clip

        grade = MOOD_GRADES.get(mood, MOOD_GRADES["default"])
        b = grade.get("brightness", 1.0)
        c = grade.get("contrast", 1.0)
        s = grade.get("saturation", 1.0)
        op = grade.get("tint_opacity", 0)

        if b == 1.0 and c == 1.0 and s == 1.0 and op == 0:
            return clip

        def process_frame(frame):
            arr = frame.astype(np.float32)
            if b != 1.0:
                arr *= b
            if c != 1.0:
                arr = (arr - 128.0) * c + 128.0
            return np.clip(arr, 0, 255).astype(np.uint8)

        return clip.image_transform(process_frame)

    # ----------------------------------------------------------------
    # BUILD A SINGLE VIDEO CLIP SEGMENT
    # Smart tail trimming to avoid TikTok watermarks & outros
    # ----------------------------------------------------------------

    # Tail trimming: skip the last N seconds of source clips to avoid
    # TikTok logos, watermarks, and outro branding
    UNSAFE_TAIL_LONG = 7.0    # Clips > 20s: skip last 7 seconds
    UNSAFE_TAIL_MEDIUM = 3.0  # Clips 8-20s: skip last 3 seconds
    UNSAFE_TAIL_SHORT = 0.0   # Clips < 8s: use fully (too short for watermarks)

    def _get_safe_end(self, clip_duration):
        """Calculate the safe usable end of a source clip, excluding watermark-prone tail."""
        if clip_duration > 20.0:
            return clip_duration - self.UNSAFE_TAIL_LONG
        elif clip_duration > 8.0:
            return clip_duration - self.UNSAFE_TAIL_MEDIUM
        else:
            return clip_duration  # Short clips are likely clean

    def _make_video_clip(self, media_item, duration, use_cycle=0):
        clip = VideoFileClip(str(media_item.path)).without_audio()
        if hasattr(self, "temp_clips"):
            self.temp_clips.append(clip)

        # Calculate the safe usable portion of the source clip
        safe_end = self._get_safe_end(clip.duration)
        usable_duration = max(1.0, safe_end)  # Minimum 1s usable

        if usable_duration > duration + 1.0:
            max_start = max(0, usable_duration - duration - 0.5)
            # If item is reused in a later cycle, pick a completely different temporal third
            if use_cycle > 0:
                step_window = max_start / max(1, use_cycle + 1)
                cycle_min = min(max_start, step_window * (use_cycle % 3))
                cycle_max = min(max_start, cycle_min + step_window)
                start = random.uniform(cycle_min, max(cycle_min, cycle_max))
            else:
                min_start = min(4.0, max_start * 0.3)
                start = random.uniform(min_start, max_start) if max_start > min_start else min_start
            clip = clip.subclipped(start, start + duration)
        elif usable_duration > duration:
            max_start = max(0, usable_duration - duration)
            start = random.uniform(0, max_start)
            clip = clip.subclipped(start, start + duration)
        else:
            clip = clip.subclipped(0, min(usable_duration, duration))
            if clip.duration < duration:
                clip = clip.with_duration(duration)

        clip = self._fit_to_aspect(clip)
        clip = self._grade_clip(clip)
        return clip.with_duration(duration)

    # ----------------------------------------------------------------
    # BUILD A SINGLE IMAGE CLIP SEGMENT (with Ken Burns)
    # ----------------------------------------------------------------

    def _make_image_clip(self, media_item, duration, use_cycle=0):
        with Image.open(str(media_item.path)) as img_raw:
            img = img_raw.convert("RGB")
        img = apply_color_grade(img, self.mood)

        target_w = int(self.width * 1.10)
        target_h = int(self.height * 1.10)

        img_ratio = img.width / img.height
        target_ratio = target_w / target_h

        if img_ratio > target_ratio:
            new_h = target_h
            new_w = int(img.width * (target_h / img.height))
        else:
            new_w = target_w
            new_h = int(img.height * (target_w / img.width))

        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # ── Sharpening: recover detail lost during scaling ──
        if VIDEO_SHARPEN:
            img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=2))

        x = (new_w - target_w) // 2
        y = (new_h - target_h) // 2
        img = img.crop((x, y, x + target_w, y + target_h))

        base_clip = ImageClip(np.array(img, dtype=np.uint8)).with_duration(duration)

        zoom_in = (use_cycle % 2 == 0)
        intensity = random.uniform(0.04, 0.08)
        pan_x = random.uniform(-0.04, 0.04)
        pan_y = random.uniform(-0.04, 0.04)
        graded = self._apply_ken_burns(
            base_clip, duration,
            zoom_in=zoom_in, intensity=intensity,
            pan_x=pan_x, pan_y=pan_y
        )

        graded = graded.resized((self.width, self.height))
        return graded.with_duration(duration)

    # ----------------------------------------------------------------
    # CINEMATIC FALLBACK CLIP
    # ----------------------------------------------------------------

    def _make_fallback_clip(self, duration, index=0):
        clip = make_cinematic_gradient_clip(duration, index)
        return clip.with_duration(duration)

    # ----------------------------------------------------------------
    # ANTI-REPETITION CLIP SELECTOR
    # Ensures maximum variety — no clip repeats until ALL have been used
    # ----------------------------------------------------------------

    def _pick_next_media_item(self, media_items, used_indices, use_counter, last_index=None):
        """
        Pick the next media item using anti-repetition LRU cycling with spacing constraints.
        - Guarantees 100% UNIQUE clips as long as clips are available in the pool.
        - Guarantees no two adjacent cuts ever use the same clip.
        - When all clips have been exhausted, starts a new cycle with a fresh shuffle,
          ensuring the first clip of the new cycle is not the same as the last clip of the previous cycle.
        """
        if not media_items:
            return None, used_indices, use_counter, None

        total = len(media_items)

        # Find unused indices in current cycle
        unused = [i for i in range(total) if i not in used_indices]

        if not unused:
            # All clips used in this cycle — start new cycle with a fresh shuffle
            used_indices = set()
            unused = list(range(total))
            random.shuffle(unused)
            # Prevent immediate repetition at cycle boundary
            if last_index is not None and len(unused) > 1 and unused[0] == last_index:
                unused[0], unused[1] = unused[1], unused[0]
            use_counter += 1

        # Avoid picking last_index if other options exist in unused
        candidates = [i for i in unused if i != last_index] or unused
        idx = candidates[0] if len(candidates) == 1 else random.choice(candidates)
        used_indices.add(idx)

        return media_items[idx], used_indices, use_counter, idx

    def _make_clip_from_item(self, item, duration, gradient_index, use_cycle=0):
        """Make a video/image/fallback clip from a media item."""
        if item is None:
            return self._make_fallback_clip(duration, gradient_index), gradient_index + 1
        try:
            if item.media_type == "video":
                return self._make_video_clip(item, duration, use_cycle=use_cycle), gradient_index
            else:
                return self._make_image_clip(item, duration, use_cycle=use_cycle), gradient_index
        except Exception as e:
            return self._make_fallback_clip(duration, gradient_index), gradient_index + 1

    # ----------------------------------------------------------------
    # BUILD FULL MEDIA SEQUENCE
    # Matches each media item to subtitle segment timing
    # Uses anti-repetition LRU cycling for maximum clip variety
    # ----------------------------------------------------------------

    def _build_media_sequence(self, media_items, subtitles, total_duration=None):
        clips = []
        gradient_index = 0
        used_indices = set()
        use_counter = 0
        last_index = None

        if not subtitles:
            dur = total_duration or float(TARGET_DURATION)
            clip_len = 6.0
            num_segments = max(1, int(dur / clip_len))
            subtitles = []
            for i in range(num_segments):
                subtitles.append({
                    "text": "",
                    "start": i * clip_len,
                    "end": (i + 1) * clip_len if i < num_segments - 1 else dur
                })

        num_clips = len(subtitles)
        
        # Build clips with maximum 2.5s pacing
        for i in range(num_clips - 1):
            segment = subtitles[i]
            raw_dur = float(segment["end"]) - float(segment["start"])
            duration = max(1.0, raw_dur)
            
            # Split long segments > 3.0s into fast 1.5s-2.5s scene cuts
            if duration > 3.0:
                num_subcuts = int(np.ceil(duration / 2.2))
                sub_dur = duration / num_subcuts
                for _ in range(num_subcuts):
                    item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
                    clip, gradient_index = self._make_clip_from_item(item, sub_dur, gradient_index, use_cycle=use_counter)
                    clips.append(clip)
            else:
                item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
                clip, gradient_index = self._make_clip_from_item(item, duration, gradient_index, use_cycle=use_counter)
                clips.append(clip)
            
        # Calculate cumulative start time of the last clip in the composite
        padding = 0.20
        if clips:
            prev_durations_sum = sum(c.duration for c in clips)
            last_clip_start = max(0.0, prev_durations_sum - len(clips) * padding)
        else:
            last_clip_start = 0.0
            
        # Determine duration for the last clip to make the final composite reach total_duration
        if total_duration:
            remaining_tail = max(1.2, total_duration - last_clip_start)
        else:
            last_seg = subtitles[-1]
            remaining_tail = max(1.2, float(last_seg["end"]) - float(last_seg["start"]))
            
        # Split remaining tail > 2.8s into fast 2.0s-2.2s sub-cuts so closing is dynamic (3-5 cuts)
        if remaining_tail > 2.8:
            num_tail_cuts = int(np.ceil(remaining_tail / 2.2))
            tail_sub_dur = remaining_tail / num_tail_cuts
            for _ in range(num_tail_cuts):
                item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
                clip, gradient_index = self._make_clip_from_item(item, tail_sub_dur, gradient_index, use_cycle=use_counter)
                clips.append(clip)
        else:
            item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
            clip, gradient_index = self._make_clip_from_item(item, remaining_tail, gradient_index, use_cycle=use_counter)
            clips.append(clip)

        if media_items:
            total_unique = len(media_items)
            total_used = len(clips)
            cycles = use_counter + 1
            if total_unique >= total_used:
                print(f"  ✨ Anti-Repeat: 100% ZERO REPETITION — {total_used} cuts generated using {total_used} distinct unique clips!")
            else:
                print(f"  Anti-Repeat: {total_used} clips from {total_unique} unique sources ({cycles} cycle{'s' if cycles > 1 else ''} with dynamic offset slicing)")

        # Join video clips sequentially — 'chain' is 3-5x faster than 'compose'
        # because it avoids per-frame compositing overhead at build time.
        from moviepy import concatenate_videoclips
        return concatenate_videoclips(clips, method="chain")

    # ----------------------------------------------------------------
    # BUILD BEAT-SYNCED MEDIA SEQUENCE
    # Uses beat_sync.py cut points for musically-timed clip transitions
    # ----------------------------------------------------------------

    def _build_media_sequence_beat_synced(self, media_items, beat_cuts, total_duration=None):
        """
        Build media sequence driven by beat-detected cut points.
        Each cut is on a musical beat boundary with energy-adaptive durations.
        """
        clips = []
        gradient_index = 0
        used_indices = set()
        use_counter = 0
        last_index = None

        if not beat_cuts:
            # Fallback to standard sequencing
            return self._build_media_sequence(media_items, [], total_duration)

        print(f"  🎵 Building beat-synced media sequence ({len(beat_cuts)} cuts)...")

        for i, cut in enumerate(beat_cuts):
            cut_duration = max(0.5, cut["end"] - cut["start"])

            item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
            clip, gradient_index = self._make_clip_from_item(item, cut_duration, gradient_index, use_cycle=use_counter)
            clips.append(clip)

        # Extend to total_duration if needed
        if total_duration and clips:
            current_total = sum(c.duration for c in clips)
            if current_total < total_duration - 0.5:
                gap = total_duration - current_total
                # Fill gap with additional fast cuts
                num_fill = max(1, int(gap / 2.0))
                fill_dur = gap / num_fill
                for _ in range(num_fill):
                    item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
                    clip, gradient_index = self._make_clip_from_item(item, fill_dur, gradient_index, use_cycle=use_counter)
                    clips.append(clip)

        if media_items:
            total_unique = len(media_items)
            total_used = len(clips)
            cycles = use_counter + 1
            if total_unique >= total_used:
                print(f"  ✨ Anti-Repeat: 100% ZERO REPETITION — {total_used} cuts generated using {total_used} distinct unique clips!")
            else:
                print(f"  Anti-Repeat: {total_used} beat-synced clips from {total_unique} unique sources ({cycles} cycle{'s' if cycles > 1 else ''} with dynamic offset slicing)")

        # Join video clips sequentially
        from moviepy import concatenate_videoclips
        return concatenate_videoclips(clips, method="chain")

    def _extend_to_duration(self, video_track, target_duration, media_items, gradient_index=0):
        """Extend video track to match audio duration with fast sub-cuts (max 2.2s each) without repeating recent clips"""
        if video_track.duration >= target_duration:
            return video_track

        gap = target_duration - video_track.duration
        if gap <= 0.1:
            return video_track

        used_indices = set()
        use_counter = 0
        last_index = None

        extra_clips = []
        if gap > 2.5:
            num_subcuts = int(np.ceil(gap / 2.2))
            sub_dur = gap / num_subcuts
            for _ in range(num_subcuts):
                item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
                clip, gradient_index = self._make_clip_from_item(item, sub_dur, gradient_index, use_cycle=use_counter)
                extra_clips.append(clip)
        else:
            item, used_indices, use_counter, last_index = self._pick_next_media_item(media_items, used_indices, use_counter, last_index=last_index)
            clip, gradient_index = self._make_clip_from_item(item, gap, gradient_index, use_cycle=use_counter)
            extra_clips.append(clip)

        return concatenate_videoclips([video_track] + extra_clips, method="chain")

    # ----------------------------------------------------------------
    # BUILD SUBTITLE LAYERS
    # ----------------------------------------------------------------

    def _build_subtitle_layers(self, subtitles):
        caption_style = getattr(self, "caption_style", "typing") or "typing"
        if caption_style == "none" or not subtitles:
            return []

        use_karaoke = (caption_style in ["karaoke", "typing"]) or SUBTITLE_STYLE.get("karaoke", True)
        mood = self.mood or "peaceful"

        total_subs = len(subtitles)
        processed_chunks = []
        for seg_idx, seg in enumerate(subtitles):
            start = float(seg.get("start", 0))
            end = float(seg.get("end", start + 2))
            text = str(seg.get("text", "")).strip()
            if not text:
                continue

            if self.log_callback and (seg_idx % max(1, total_subs // 4) == 0 or seg_idx == total_subs - 1):
                sub_pct = min(77, int(70 + (seg_idx / max(1, total_subs)) * 7))
                self.log_callback(f"PROGRESS:{sub_pct}% STEP:🔤 Styling typography ({seg_idx + 1}/{total_subs} lines)...")

            pos_mode = getattr(self, "caption_position", "center") or "center"
            if pos_mode == "center":
                pos_y = 0.45
            elif pos_mode == "top":
                pos_y = 0.20
            else:
                pos_y = 0.62  # Mobile/Social safe lower-third
            sub_y = int(self.height * pos_y)
            bg_opacity = SUBTITLE_STYLE.get("bg_opacity", 148)

            words = text.split()
            word_frames = []
            if use_karaoke and words:
                for idx in range(len(words)):
                    arr = build_subtitle_image_karaoke(
                        text=text,
                        active_word_index=idx,
                        width=int(self.width * 0.90),
                        font_size=SUBTITLE_STYLE.get("font_size", 56),
                        text_color=SUBTITLE_STYLE.get("color", "white"),
                        stroke_color=SUBTITLE_STYLE.get("stroke_color", "black"),
                        stroke_width=SUBTITLE_STYLE.get("stroke_width", 3),
                        bg_opacity=bg_opacity,
                        mood=mood,
                    )
                    word_frames.append(arr)
            else:
                img_array = build_subtitle_image(
                    text=text,
                    width=int(self.width * 0.90),
                    font_size=SUBTITLE_STYLE.get("font_size", 56),
                    text_color=SUBTITLE_STYLE.get("color", "white"),
                    stroke_color=SUBTITLE_STYLE.get("stroke_color", "black"),
                    stroke_width=SUBTITLE_STYLE.get("stroke_width", 3),
                    bg_opacity=bg_opacity,
                    mood=mood,
                )
                word_frames = [img_array]

            processed_chunks.append({
                "start": start,
                "end": end,
                "duration": max(0.01, end - start),
                "words": words,
                "word_frames": word_frames,
                "sub_y": sub_y,
                "blank": np.zeros((380, int(self.width * 0.90), 4), dtype=np.uint8)
            })

        if not processed_chunks:
            return []

        total_track_dur = max(c["end"] for c in processed_chunks)

        def make_sub_track_frame(t):
            for chunk in processed_chunks:
                if chunk["start"] <= t < chunk["end"]:
                    dur = chunk["duration"]
                    w_frames = chunk["word_frames"]
                    if len(w_frames) == 1:
                        return w_frames[0]
                    progress = min(1.0, max(0.0, (t - chunk["start"]) / dur))
                    active_idx = min(len(w_frames) - 1, int(progress * len(w_frames)))
                    return w_frames[active_idx]
            return processed_chunks[0]["blank"]

        from moviepy import VideoClip
        sub_y_pos = processed_chunks[0]["sub_y"]
        sub_track_clip = (
            VideoClip(make_sub_track_frame, duration=total_track_dur)
            .with_position(("center", sub_y_pos))
        )

        return [sub_track_clip]

    # ----------------------------------------------------------------
    # BUILD HOOK LAYER
    # ----------------------------------------------------------------

    def _build_hook_layer(self, hook_text, duration=3.0):
        if not hook_text:
            return None

        img_array = build_hook_image(
            text=hook_text,
            width=int(self.width * 0.92),
            mood=self.mood,
        )

        hook_y = int(self.height * 0.14)

        clip = (
            ImageClip(img_array, transparent=True)
            .with_start(0)
            .with_duration(duration)
            .with_position(("center", hook_y))
        )

        return clip

    # ----------------------------------------------------------------
    # AUDIO MIXING - Voice + Background Music with ducking
    # ----------------------------------------------------------------

    def _make_duck_filter(self, subtitles, base_volume, transition_time=0.25):
        """Pre-compute duck envelope as a cached 1ms-resolution lookup table.
        This is called once up-front instead of per-sample during render."""
        intervals = [(float(seg["start"]), float(seg["end"])) for seg in subtitles]
        low_vol = base_volume * 0.40
        high_vol = base_volume * 1.15

        if not intervals:
            def _flat_envelope(t_array):
                return np.full(np.atleast_1d(np.asarray(t_array, dtype=float)).shape, high_vol)
            return _flat_envelope

        # Determine total duration from last interval end + buffer
        max_t = max(end for _, end in intervals) + 1.0
        # 1ms resolution pre-computed lookup table
        _res = 0.001
        _n = int(np.ceil(max_t / _res)) + 2
        _t_lut = np.arange(_n) * _res
        _vols_lut = np.full(_n, high_vol)

        for start, end in intervals:
            si = int(start / _res)
            ei = min(_n - 1, int(end / _res))
            _vols_lut[si:ei + 1] = low_vol
            # Fade-out transition before speech
            fade_n = max(1, int(transition_time / _res))
            fs = max(0, si - fade_n)
            for j in range(fs, si):
                ratio = (si - j) / fade_n
                _vols_lut[j] = min(_vols_lut[j], low_vol + (high_vol - low_vol) * (1.0 - ratio))
            # Fade-in transition after speech
            fe = min(_n - 1, ei + fade_n)
            for j in range(ei, fe + 1):
                ratio = (j - ei) / fade_n
                _vols_lut[j] = min(_vols_lut[j], low_vol + (high_vol - low_vol) * ratio)

        def envelope(t_array):
            t_arr = np.atleast_1d(np.asarray(t_array, dtype=float))
            indices = np.clip((t_arr / _res).astype(int), 0, _n - 1)
            return _vols_lut[indices]

        return envelope

    def _mix_audio(self, voice_audio, music_path=None, subtitles=None):
        clips = [voice_audio]
        
        # Load hook audio if enabled in HOOK_CONFIG or global settings
        hook_enabled = HOOK_CONFIG.get("audio_enabled", False) or getattr(config.settings, "HOOK_AUDIO_ENABLED", False)
        if hook_enabled:
            hook_path = Path("assets/hooks/whoosh.wav")
            if hook_path.exists():
                try:
                    h_clip = AudioFileClip(str(hook_path))
                    if hasattr(self, "temp_clips"):
                        self.temp_clips.append(h_clip)
                    hook_dur = min(h_clip.duration, voice_audio.duration)
                    h_clip = h_clip.subclipped(0, hook_dur).with_start(0)
                    hook_vol = float(HOOK_CONFIG.get("audio_volume", getattr(config.settings, "HOOK_AUDIO_VOLUME", 0.25)))
                    if hasattr(h_clip, "with_volume_scaled"):
                        h_clip = h_clip.with_volume_scaled(hook_vol)
                    else:
                        h_clip = h_clip.volumex(hook_vol)
                    clips.append(h_clip)
                    print(f"  Hook Audio: Added cinematic whoosh sound ({hook_dur:.1f}s, vol={hook_vol})")
                except Exception as e:
                    print(f"  Warning: Failed to load hook audio: {e}")

        if BACKGROUND_MUSIC_ENABLED and music_path and Path(music_path).exists():
            try:
                music = AudioFileClip(str(music_path))
                if hasattr(self, "temp_clips"):
                    self.temp_clips.append(music)
                total_dur = voice_audio.duration

                if music.duration < total_dur:
                    loops = []
                    acc = 0.0
                    while acc < total_dur:
                        remaining = total_dur - acc
                        if music.duration <= remaining:
                            loops.append(music)
                            acc += music.duration
                        else:
                            loops.append(music.subclipped(0, remaining))
                            acc = total_dur
                    music = concatenate_audioclips(loops)

                if music.duration > total_dur:
                    max_start = max(0.0, music.duration - total_dur)
                    import random
                    start_offset = random.uniform(0.0, max_start)
                    print(f"  Background Music: Picking segment at {start_offset:.1f}s (duration: {music.duration:.1f}s)")
                    music = music.subclipped(start_offset, start_offset + total_dur)

                # Apply smooth music fades to prevent start/end click pops
                try:
                    from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
                    from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
                    music = music.with_effects([AudioFadeIn(0.5), AudioFadeOut(1.0)])
                except Exception:
                    pass

                # Apply dynamic ducking if subtitles are available, otherwise static volume
                bg_vol = getattr(config.settings, "BACKGROUND_MUSIC_VOLUME", BACKGROUND_MUSIC_VOLUME)
                if subtitles:
                    print("  Applying dynamic audio ducking...")
                    duck_envelope = self._make_duck_filter(subtitles, bg_vol)
                    music = music.transform(lambda gf, t: gf(t) * duck_envelope(t)[:, None])
                else:
                    if hasattr(music, "with_volume_scaled"):
                        music = music.with_volume_scaled(bg_vol)
                    else:
                        music = music.volumex(bg_vol)

                clips.append(music)
                print("  Background Music: Added")
            except Exception as e:
                print(f"Music mix skipped: {e}")

        if len(clips) > 1:
            try:
                mixed = CompositeAudioClip(clips)
                # Apply soft limiter if enabled to prevent digital clipping/distortion
                if getattr(config.settings, "AUDIO_NORMALIZE_ENABLED", False):
                    mixed = mixed.transform(lambda gf, t: np.tanh(gf(t) * 0.95))
                return mixed
            except Exception as e:
                print(f"Failed to composite audio clips: {e}")
                return voice_audio
        else:
            return voice_audio

    # ----------------------------------------------------------------
    # VIGNETTE LAYER
    # ----------------------------------------------------------------

    def _get_vignette_layer(self, duration):
        try:
            return (
                VIGNETTE_CLIP
                .with_duration(duration)
                .with_position(("center", "center"))
            )
        except Exception:
            return None

    def _close_clip_recursive(self, clip):
        if clip is None:
            return
        if hasattr(clip, "clips") and isinstance(clip.clips, list):
            for sub in clip.clips:
                self._close_clip_recursive(sub)
        if hasattr(clip, "audio") and clip.audio is not None:
            self._close_clip_recursive(clip.audio)
        try:
            clip.close()
        except Exception:
            pass

    # ----------------------------------------------------------------
    # MAIN BUILD REEL FUNCTION
    # ----------------------------------------------------------------
    def build_reel(
        self,
        media_items,
        audio_path,
        subtitles,
        output_name="final_reel.mp4",
        hook_text=None,
        music_path=None,
        show_progress_bar=True,
        log_callback=None,
        beat_cuts=None,
    ):
        ensure_output()
        self.temp_clips = []
        self.log_callback = log_callback

        voice_audio = None
        media_track = None
        final_video = None
        vignette = None
        w_clip = None
        progress_bar = None
        sub_layers = []
        hook_clip = None
        final_audio = None

        is_music_only = not audio_path

        try:
            if not is_music_only:
                audio_path = Path(audio_path)
                if not audio_path.exists():
                    raise FileNotFoundError(f"Audio file not found: {audio_path}")

            print("")
            print("=" * 62)
            print("  VIDEOFACTORY - CINEMATIC REEL ENGINE")
            print("=" * 62)
            print(f"  Mood:      {self.mood}")
            print(f"  Media:     {len(media_items) if media_items else 0} items")
            print(f"  Subtitles: {len(subtitles) if subtitles else 0} lines")
            print(f"  Hook:      {hook_text[:50] if hook_text else 'None'}")
            print(f"  Music:     {'Yes' if music_path else 'No'}")
            print(f"  Mode:      {'Local Media' if media_items else 'Cinematic Gradient'}")
            print("=" * 62)
            print("")

            if is_music_only:
                if not music_path or not Path(music_path).exists():
                    raise ValueError("For music-only mode, a valid music_path must be provided.")
                voice_audio = AudioFileClip(str(music_path))
                self.temp_clips.append(voice_audio)
                total_duration = min(voice_audio.duration, 60.0)
                voice_audio = voice_audio.subclipped(0, total_duration)
                print(f"  [Music-Only Mode] Duration: {total_duration:.1f}s")
            else:
                voice_audio = AudioFileClip(str(audio_path))
                self.temp_clips.append(voice_audio)
                total_duration = voice_audio.duration
                print(f"  [Standard Mode] Duration: {total_duration:.1f}s")

            if self.log_callback:
                self.log_callback("PROGRESS:65% STEP:🎬 Assembling video scenes & kinetic pacing...")

            # Use beat-synced sequencing when beat_cuts are provided (song-to-reel mode)
            if beat_cuts:
                print(f"  Building BEAT-SYNCED media sequence ({len(beat_cuts)} cuts)...")
                media_track = self._build_media_sequence_beat_synced(media_items, beat_cuts, total_duration=total_duration)
            else:
                print(f"  Building media sequence...")
                media_track = self._build_media_sequence(media_items, subtitles, total_duration=total_duration)
            
            # Extend video to match full audio duration so it never goes black
            if media_track.duration < total_duration:
                print(f"  Extending video {media_track.duration:.1f}s to {total_duration:.1f}s")
                media_track = self._extend_to_duration(media_track, total_duration, media_items)

            if self.log_callback:
                self.log_callback("PROGRESS:68% STEP:🎨 Applying color grading & vignette FX...")

            layers = [media_track]

            vignette = self._get_vignette_layer(total_duration)
            if vignette is not None:
                layers.append(vignette)
                print(f"  Vignette:  Added")

            # Check for branding / watermark overlay
            import config.settings
            watermark_enabled = getattr(config.settings, "WATERMARK_ENABLED", False)
            watermark_path = getattr(config.settings, "WATERMARK_PATH", "assets/watermark.png")
            
            w_path = Path(watermark_path)
            if (watermark_enabled or w_path.exists()) and w_path.exists():
                try:
                    w_clip = ImageClip(str(w_path)).with_duration(total_duration)
                    w_pos_raw = getattr(config.settings, "WATERMARK_POSITION", ("right", "top"))
                    if isinstance(w_pos_raw, str):
                        parts = [p.strip() for p in w_pos_raw.split(",") if p.strip()]
                        if len(parts) == 2:
                            try:
                                w_pos = (int(parts[0]), int(parts[1]))
                            except ValueError:
                                w_pos = (parts[0], parts[1])
                        else:
                            w_pos = w_pos_raw
                    else:
                        w_pos = w_pos_raw
                    w_opacity = getattr(config.settings, "WATERMARK_OPACITY", 0.45)
                    w_height = getattr(config.settings, "WATERMARK_HEIGHT", 65)
                    w_margin = getattr(config.settings, "WATERMARK_MARGIN", 35)
                    
                    # Resize keeping aspect ratio
                    w_clip = w_clip.resized(height=w_height)
                    
                    # Set opacity compatibility helper
                    if hasattr(w_clip, "with_opacity"):
                        w_clip = w_clip.with_opacity(w_opacity)
                    else:
                        w_clip = w_clip.image_transform(lambda img: (img * w_opacity).astype(img.dtype))
                        
                    w_clip = w_clip.with_position(w_pos).with_margin(w_margin)
                    layers.append(w_clip)
                    print(f"  Watermark: Added ({w_path.name})")
                except Exception as we:
                    print(f"  Warning: Failed to add watermark overlay: {we}")

            if show_progress_bar:
                try:
                    progress_bar = create_progress_bar_clip(total_duration)
                    layers.append(progress_bar)
                    print(f"  Progress bar: Added")
                except Exception as e:
                    print(f"  Progress bar skipped: {e}")

            # Subtitles / Text Overlays
            if not is_music_only:
                if self.log_callback:
                    self.log_callback("PROGRESS:70% STEP:🔤 Building dynamic karaoke subtitles...")
                print(f"  Building subtitles...")
                sub_layers = self._build_subtitle_layers(subtitles)
                layers.extend(sub_layers)
                print(f"  Subtitles: {len(sub_layers)} clips added")

                if HOOK_CONFIG.get("enabled", False) and hook_text:
                    hook_duration = float(HOOK_CONFIG.get("hook_duration", 3.0))
                    hook_clip = self._build_hook_layer(hook_text, duration=hook_duration)
                    if hook_clip is not None:
                        layers.append(hook_clip)
                        print(f"  Hook:      Added ({hook_duration}s)")

            if self.log_callback:
                self.log_callback("PROGRESS:77% STEP:🎵 Mixing voice track & dynamic music ducking...")
            print(f"  Mixing audio...")
            if is_music_only:
                final_audio = voice_audio
            else:
                final_audio = self._mix_audio(voice_audio, music_path=music_path, subtitles=subtitles)

            if final_audio is not None and is_music_only:
                try:
                    from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
                    from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
                    final_audio = final_audio.with_effects([AudioFadeIn(0.5), AudioFadeOut(0.8)])
                except Exception:
                    pass

            if self.log_callback:
                self.log_callback("PROGRESS:80% STEP:🎞️ Compositing multi-layer timeline & starting encoder...")
            print(f"  Compositing {len(layers)} layers (with Fade In / Out)...")
            final_video = CompositeVideoClip(
                layers,
                size=(self.width, self.height)
            ).with_duration(total_duration)

            try:
                from moviepy.video.fx.FadeIn import FadeIn
                from moviepy.video.fx.FadeOut import FadeOut
                final_video = final_video.with_effects([FadeIn(0.5), FadeOut(0.5)])
            except Exception:
                pass

            if final_audio is not None:
                final_video = final_video.with_audio(final_audio)

            videos_dir = Path(OUTPUT_DIR) / "videos"
            videos_dir.mkdir(parents=True, exist_ok=True)
            output_path = videos_dir / output_name

            print("")
            print(f"  Rendering -> {output_path.name}")
            print(f"  Duration:    {total_duration:.2f}s")
            print(f"  Resolution:  {self.width}x{self.height}")
            print(f"  FPS:         {self.fps}")
            print(f"  Codec:       {VIDEO_CODEC} / {AUDIO_CODEC}")
            print("")

            # ── Determine thread count: 0 = auto (moviepy passes None = all CPUs) ──
            import os as _os
            _threads = ENCODE_THREADS if ENCODE_THREADS > 0 else _os.cpu_count() or 4

            print(f"  Quality:     {VIDEO_QUALITY_PRESET} | CRF {VIDEO_CRF} | {BITRATE} | preset={PRESET}")
            print(f"  Threads:     {_threads} | Audio: {AUDIO_BITRATE}")

            import uuid
            temp_audio = Path("output/temp") / f"temp_snd_{uuid.uuid4().hex[:8]}.m4a"
            temp_audio.parent.mkdir(parents=True, exist_ok=True)

            moviepy_logger = MoviePyLiveProgressLogger(log_callback=self.log_callback) if show_progress_bar else None

            try:
                final_video.write_videofile(
                    str(output_path),
                    fps=self.fps,
                    codec=VIDEO_CODEC,
                    audio_codec=AUDIO_CODEC,
                    bitrate=BITRATE,
                    audio_bitrate=AUDIO_BITRATE,
                    preset=PRESET,
                    ffmpeg_params=["-crf", str(VIDEO_CRF)],
                    threads=_threads,
                    temp_audiofile=str(temp_audio),
                    remove_temp=False,
                    logger=moviepy_logger,
                )
            finally:
                try:
                    if temp_audio.exists():
                        temp_audio.unlink()
                except Exception:
                    pass

            if self.log_callback:
                self.log_callback("PROGRESS:99% STEP:💾 Finalizing MP4 container & sync...")

            size_mb = output_path.stat().st_size / (1024 * 1024)

            print("")
            print("=" * 62)
            print("  REEL COMPLETE!")
            print(f"  File:     {output_path}")
            print(f"  Size:     {size_mb:.1f} MB")
            print(f"  Duration: {total_duration:.2f}s")
            print("=" * 62)
            print("")

            return str(output_path)

        finally:
            print("  Releasing all render clips...")
            # 1. Close all raw clips that read files from disk
            for c in self.temp_clips:
                try:
                    c.close()
                except Exception:
                    pass
            # 2. Close final video composition and recursively close all sub-layers
            if final_video is not None:
                self._close_clip_recursive(final_video)
            else:
                for c in [voice_audio, media_track, final_audio, vignette, w_clip, progress_bar, hook_clip]:
                    if c is not None:
                        try:
                            c.close()
                        except Exception:
                            pass
                for c in sub_layers:
                    try:
                        c.close()
                    except Exception:
                        pass


# ================================================================
# TEST
# ================================================================

if __name__ == "__main__":
    from src.utils.media_manager import MediaManager

    ensure_output()

    # Look in proper subfolders first, then fallback to root
    audio_dir = Path(OUTPUT_DIR) / "audio"
    subs_dir = Path(OUTPUT_DIR) / "subtitles"
    
    latest_audio = get_latest_file(audio_dir, "*.mp3") if audio_dir.exists() else None
    if not latest_audio:
        latest_audio = get_latest_file(OUTPUT_DIR, "*.mp3")
    
    latest_subs = get_latest_file(subs_dir, "*_subtitles.json") if subs_dir.exists() else None
    if not latest_subs:
        latest_subs = get_latest_file(OUTPUT_DIR, "*_subtitles.json")

    if not latest_audio or not latest_subs:
        print("No test audio/subtitles found.")
        print("Run first: python src\\audio\\tts_engine.py")
    else:
        subtitles = load_json(latest_subs)
        print(f"Audio:     {latest_audio.name}")
        print(f"Subtitles: {latest_subs.name}")
        print(f"Lines:     {len(subtitles)}")

        manager = MediaManager(niche="gospel")
        manager.scan()

        media_items = []
        if manager.has_media():
            media_items = manager.pick_media_for_reel(count=len(subtitles))

        from src.utils.media_manager import get_smart_music
        music_path = get_smart_music(niche="gospel")
        hook_text = subtitles[0]["text"] if subtitles else "God has not forgotten you."

        engine = ReelVideoEngine(mood="peaceful")
        out = engine.build_reel(
            media_items=media_items,
            audio_path=str(latest_audio),
            subtitles=subtitles,
            output_name=f"reel_{now_stamp()}.mp4",
            hook_text=hook_text,
            music_path=music_path,
            show_progress_bar=True,
        )

        print(f"\nOpen your reel: {out}\n")