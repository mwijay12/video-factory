# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY - LONGFORM CLIPPER
# Turns long videos (sermons, podcasts, interviews) into vertical
# Shorts/Reels/TikToks with synced captions and a social kit.
#
# Pipeline:
#   1. Extract audio (ffmpeg)
#   2. Transcribe with faster-whisper (word timestamps)
#   3. Score windows for hooks / emotional language / energy
#   4. Reframe to 9:16 and burn kinetic captions
#   5. Write social kit next to each clip
# ================================================================

import json
import re
import subprocess
import time
import wave
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LONGFORM_DIR = BASE_DIR / "assets" / "longform"
CLIPS_DIR = BASE_DIR / "output" / "videos"
TRANSCRIPTS_DIR = BASE_DIR / "output" / "longform"
TEMP_DIR = BASE_DIR / "output" / "temp"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
AUDIO_SAMPLE_RATE = 16000

HOOK_KEYWORDS = {
    "english": [
        "why", "how", "what", "when", "never", "always", "secret", "truth",
        "proof", "warning", "mistake", "you", "your", "nobody", "everybody",
        "stop", "start", "because", "imagine", "remember", "listen",
        "most important", "the problem is", "here is", "the reason",
    ],
    "swahili": [
        "kwa nini", "nini", "vipi", "jinsi", "siri", "ukweli", "ushahidi",
        "onyo", "kosa", "wewe", "wako", "hakuna", "kila mtu", "acha",
        "anza", "kwa sababu", "fikiri", "kumbuka", "sikiliza",
        "muhimu zaidi", "tatizo ni", "hii ndiyo", "sababu ni",
        "usikate tamaa", "mungu", "maisha", "yesu", "ombi", "sala",
        "baraka", "neema", "imani", "upendo", "familia", "kesho", "sasa",
    ],
}

NICHE_HASHTAGS = {
    "gospel": ["#gospel", "#faith", "#jesus", "#bible", "#prayer", "#worship", "#christian"],
    "prayer": ["#prayer", "#faith", "#godisgood", "#blessed", "#worship", "#jesus"],
    "praise": ["#praise", "#worship", "#gospelmusic", "#faith", "#jesus"],
    "motivational": ["#motivation", "#mindset", "#discipline", "#success", "#growth"],
    "tech": ["#tech", "#ai", "#technology", "#future", "#innovation"],
    "swahili": ["#swahili", "#kenya", "#tanzania", "#habari", "#motivation", "#mungu"],
}


# ================================================================
# HELPERS
# ================================================================

def now_stamp():
    return time.strftime("%Y%m%d_%H%M%S")


def sanitize_name(name, max_len=48):
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", str(name)).strip("_")
    return (clean[:max_len] or "clip").lower()


def ensure_dirs():
    for folder in (LONGFORM_DIR, CLIPS_DIR, TRANSCRIPTS_DIR, TEMP_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def resolve_video(path_or_name):
    """Accepts an absolute path, a relative path or a filename inside assets/longform."""
    candidate = Path(str(path_or_name))
    if candidate.exists():
        return candidate.resolve()

    if not candidate.is_absolute():
        rooted = BASE_DIR / candidate
        if rooted.exists():
            return rooted.resolve()

    by_name = LONGFORM_DIR / Path(str(path_or_name)).name
    if by_name.exists():
        return by_name.resolve()

    return None


def list_source_videos():
    ensure_dirs()
    videos = []
    for file in sorted(LONGFORM_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append({
                "name": file.name,
                "path": str(file),
                "size_mb": round(file.stat().st_size / (1024 * 1024), 2),
                "created_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(file.stat().st_mtime)),
            })
    return videos


def probe_duration(video_path):
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8", "ignore").strip()
        return float(out)
    except Exception:
        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(str(video_path))
            duration = float(clip.duration)
            clip.close()
            return duration
        except Exception:
            return 0.0


def extract_audio(video_path, output_wav=None):
    ensure_dirs()
    output_wav = Path(output_wav) if output_wav else TEMP_DIR / f"longform_audio_{now_stamp()}.wav"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", str(AUDIO_SAMPLE_RATE),
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("ffmpeg failed to extract audio from the video.")
    return output_wav


def _language_code(language):
    if not language:
        return None
    value = str(language).strip().lower()
    if value in ("auto", "auto-detect", "none"):
        return None
    return {"english": "en", "swahili": "sw", "en": "en", "sw": "sw"}.get(value, value)


def transcribe_audio(audio_path, language=None, model_size="base", progress=None, log=None):
    """Local faster-whisper transcription with word timestamps (cloud-free, long videos safe)."""
    from faster_whisper import WhisperModel

    log = log or print
    lang_code = _language_code(language)

    if progress:
        progress(20, f"Loading Whisper ({model_size}) model...")
    log(f"Transcribing with faster-whisper '{model_size}' (language: {lang_code or 'auto'})...")

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    kwargs = {"word_timestamps": True, "vad_filter": True, "beam_size": 1}
    if lang_code:
        kwargs["language"] = lang_code

    segments_iter, info = model.transcribe(str(audio_path), **kwargs)

    segments = []
    for segment in segments_iter:
        words = []
        if getattr(segment, "words", None):
            for word in segment.words:
                words.append({
                    "word": word.word.strip(),
                    "start": round(float(word.start), 3),
                    "end": round(float(word.end), 3),
                })
        text = (segment.text or "").strip()
        if not text:
            continue
        segments.append({
            "text": text,
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "words": words,
        })

    return {
        "language": info.language,
        "duration": round(float(info.duration), 3),
        "segments": segments,
    }


# ================================================================
# SUBTITLES
# ================================================================

def segments_to_words(segments, start, end):
    words = []
    for segment in segments:
        for word in segment.get("words", []):
            w_start = float(word.get("start", 0))
            w_end = float(word.get("end", w_start))
            if w_end <= start or w_start >= end:
                continue
            words.append({
                "word": str(word.get("word", "")).strip(),
                "start": max(0.0, w_start - start),
                "end": max(0.0, min(w_end, end) - start),
            })

    if words:
        return words

    # Fallback for segments without word timestamps: distribute evenly.
    for segment in segments:
        s_start = float(segment.get("start", 0))
        s_end = float(segment.get("end", s_start))
        if s_end <= start or s_start >= end:
            continue
        tokens = str(segment.get("text", "")).split()
        if not tokens:
            continue
        span = max(0.2, s_end - s_start)
        step = span / len(tokens)
        for index, token in enumerate(tokens):
            w_start = s_start + index * step
            w_end = w_start + step
            if w_end <= start or w_start >= end:
                continue
            words.append({
                "word": token,
                "start": max(0.0, w_start - start),
                "end": max(0.0, min(w_end, end) - start),
            })
    return words


def words_to_subtitles(words, words_per_line=4, max_chars=34, max_gap=0.65):
    """Groups word timestamps into short, punchy caption chunks."""
    if not words:
        return []

    words_per_line = max(2, min(8, int(words_per_line)))
    groups = []
    current = []

    for word in words:
        token = word["word"]
        if not token:
            continue
        candidate_text = " ".join([w["word"] for w in current] + [token])
        gap = word["start"] - current[-1]["end"] if current else 0
        if current and (len(current) >= words_per_line or len(candidate_text) > max_chars or gap > max_gap):
            groups.append(current)
            current = []
        current.append(word)

    if current:
        groups.append(current)

    subtitles = []
    for group in groups:
        start = round(group[0]["start"], 3)
        end = round(group[-1]["end"], 3)
        if end <= start:
            end = round(start + 0.6, 3)
        text = " ".join(w["word"] for w in group).strip()
        if text:
            subtitles.append({"text": text, "start": start, "end": end})

    # Prevent captions from flashing for a single frame.
    for index, subtitle in enumerate(subtitles):
        min_end = subtitle["start"] + 0.45
        if subtitle["end"] < min_end:
            subtitle["end"] = round(min_end, 3)
        if index + 1 < len(subtitles) and subtitle["end"] > subtitles[index + 1]["start"]:
            subtitle["end"] = round(subtitles[index + 1]["start"], 3)

    return subtitles


# ================================================================
# HIGHLIGHT DETECTION
# ================================================================

def _audio_energy_curve(audio_path):
    try:
        with wave.open(str(audio_path), "rb") as wav:
            sample_rate = wav.getframerate()
            frames = wav.readframes(wav.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        return sample_rate, samples
    except Exception:
        return None, None


def _window_rms(sample_rate, samples, start, end):
    if sample_rate is None or samples is None or len(samples) == 0:
        return 0.0
    left = max(0, int(start * sample_rate))
    right = min(len(samples), int(end * sample_rate))
    chunk = samples[left:right]
    if len(chunk) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(chunk))))


def _keyword_hits(text, language):
    lowered = text.lower()
    pool = HOOK_KEYWORDS["swahili"] + HOOK_KEYWORDS["english"]
    if language and str(language).lower() in ("swahili", "sw"):
        pool = HOOK_KEYWORDS["swahili"] + HOOK_KEYWORDS["english"]
    hits = 0
    for keyword in pool:
        if len(keyword) <= 2:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                hits += 1
        elif keyword in lowered:
            hits += 1
    return hits


def _make_title(text, max_words=9):
    clean = re.sub(r"\s+", " ", str(text)).strip(" .,!?:;-")
    words = clean.split()
    title = " ".join(words[:max_words]).strip(" .,!?:;-")
    if len(words) > max_words:
        title += "..."
    return title[:70] or "Untitled Clip"


def build_candidates(transcript, video_duration, audio_path=None, min_duration=20,
                     max_duration=60, count=5, language=None, words_per_line=4):
    segments = [s for s in transcript.get("segments", []) if str(s.get("text", "")).strip()]
    if not segments:
        return []

    min_duration = max(8.0, float(min_duration))
    max_duration = max(min_duration + 2.0, float(max_duration))

    sample_rate, samples = _audio_energy_curve(audio_path) if audio_path else (None, None)

    candidates = []
    total = len(segments)

    for i in range(total):
        start = float(segments[i]["start"])
        if start < 0.5:
            continue

        for j in range(i, total):
            end = float(segments[j]["end"])
            duration = end - start
            if duration < min_duration:
                continue
            if duration > max_duration:
                break

            text = " ".join(str(s.get("text", "")).strip() for s in segments[i:j + 1])
            words = len(text.split())
            if words < 8:
                continue

            score = 1.0
            score += min(6.0, _keyword_hits(text, language) * 1.1)
            if "?" in text:
                score += 2.0
            if "!" in text:
                score += 0.8
            if re.search(r"\d", text):
                score += 0.5

            first_words = " ".join(text.lower().split()[:3])
            starters = ("why ", "how ", "what ", "when ", "nini ", "kwa nini", "vipi ", "je ", "kwani ")
            if first_words.startswith(starters):
                score += 1.5

            words_per_second = words / max(1.0, duration)
            if 1.8 <= words_per_second <= 4.2:
                score += 1.0
            elif words_per_second < 1.0 or words_per_second > 5.5:
                score -= 1.0

            if video_duration and start < video_duration * 0.08:
                score -= 0.5
            if 25.0 <= duration <= 50.0:
                score += 0.4

            energy = _window_rms(sample_rate, samples, start, end)

            candidates.append({
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(duration, 3),
                "score": round(score, 4),
                "text": text,
                "title": _make_title(text),
                "hook": _make_title(text, max_words=12),
                "energy": round(energy, 2),
            })

    if not candidates:
        return []

    max_energy = max(c["energy"] for c in candidates) or 1.0
    for candidate in candidates:
        candidate["score"] += 2.5 * (candidate["energy"] / max_energy)

    candidates.sort(key=lambda c: c["score"], reverse=True)

    selected = []
    for candidate in candidates:
        if len(selected) >= int(count):
            break
        overlaps = False
        for chosen in selected:
            overlap_start = max(candidate["start"], chosen["start"])
            overlap_end = min(candidate["end"], chosen["end"])
            overlap = max(0.0, overlap_end - overlap_start)
            shortest = min(candidate["duration"], chosen["duration"])
            if shortest > 0 and overlap / shortest > 0.30:
                overlaps = True
                break
        if overlaps:
            continue
        selected.append(candidate)

    for candidate in selected:
        candidate["subtitles"] = words_to_subtitles(
            segments_to_words(transcript.get("segments", []), candidate["start"], candidate["end"]),
            words_per_line=words_per_line,
        )
        candidate["words_per_line"] = words_per_line

    return selected


# ================================================================
# ANALYSIS
# ================================================================

def analyze_video(video_path, language=None, model_size="base", min_duration=20,
                  max_duration=60, count=5, words_per_line=4, progress=None, log=None):
    ensure_dirs()
    log = log or print
    progress = progress or (lambda pct, step="": None)

    requested_path = video_path
    video_path = resolve_video(video_path)
    if not video_path:
        raise FileNotFoundError(f"Longform video not found: {requested_path}")

    duration = probe_duration(video_path)
    log(f"Source: {video_path.name} ({duration:.1f}s)")

    progress(5, "Extracting audio track...")
    wav_path = extract_audio(video_path)
    log(f"Audio extracted: {wav_path.name}")

    try:
        progress(15, "Transcribing audio (Whisper)...")
        transcript = transcribe_audio(
            wav_path,
            language=language,
            model_size=model_size,
            progress=progress,
            log=log,
        )

        progress(70, "Scoring highlight windows...")
        candidates = build_candidates(
            transcript,
            video_duration=duration or transcript.get("duration", 0),
            audio_path=wav_path,
            min_duration=min_duration,
            max_duration=max_duration,
            count=count,
            language=language or transcript.get("language"),
            words_per_line=words_per_line,
        )
    finally:
        try:
            wav_path.unlink()
        except Exception:
            pass

    transcript["source_video"] = str(video_path)
    transcript_path = TRANSCRIPTS_DIR / f"{sanitize_name(video_path.stem)}_{now_stamp()}.json"
    try:
        transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        log(f"Warning: could not save transcript: {exc}")

    if not candidates:
        raise RuntimeError("No usable highlights found. Try a longer video or a smaller min duration.")

    progress(90, "Preparing clip metadata...")
    result = {
        "video_path": str(video_path),
        "video_name": video_path.name,
        "duration": round(duration or transcript.get("duration", 0), 2),
        "language": transcript.get("language"),
        "model_size": model_size,
        "transcript_path": str(transcript_path),
        "candidates": candidates,
    }
    log(f"Found {len(candidates)} highlight candidates.")
    progress(100, "Analysis complete")
    return result


# ================================================================
# RENDERING
# ================================================================

def _target_size(aspect_ratio):
    ratio = str(aspect_ratio or "9:16").strip()
    if ratio == "1:1":
        return 1080, 1080
    if ratio == "16:9":
        return 1920, 1080
    return 1080, 1920


def _reframe(clip, target_w, target_h, crop_position="center"):
    width, height = clip.size
    ratio = target_w / target_h
    position = str(crop_position or "center").lower()

    if width / height > ratio:
        new_width = int(height * ratio)
        if position == "left":
            x1 = 0
        elif position == "right":
            x1 = width - new_width
        else:
            x1 = (width - new_width) // 2
        clip = clip.cropped(x1=x1, y1=0, width=new_width, height=height)
    else:
        new_height = int(width / ratio)
        if position == "top":
            y1 = 0
        elif position == "bottom":
            y1 = height - new_height
        else:
            y1 = (height - new_height) // 2
        clip = clip.cropped(x1=0, y1=y1, width=width, height=new_height)

    return clip.resized((target_w, target_h))


def _caption_layer(subtitle, target_w, target_h, mood, aspect_ratio):
    from moviepy import ImageClip
    from src.video.video_engine import build_subtitle_image

    text = subtitle.get("text", "")
    if not text:
        return None

    font_size = 56 if target_h >= 1600 else 40
    width = int(target_w * 0.92)
    image = build_subtitle_image(
        text=text,
        width=width,
        font_size=font_size,
        text_color="white",
        stroke_color="black",
        stroke_width=3,
        bg_opacity=135,
        mood=mood,
    )

    if aspect_ratio == "1:1":
        top = int(target_h * 0.62)
    else:
        top = int(target_h * 0.58)

    duration = max(0.3, float(subtitle.get("end", 0)) - float(subtitle.get("start", 0)))
    return (
        ImageClip(image)
        .with_start(max(0.0, float(subtitle.get("start", 0))))
        .with_duration(duration)
        .with_position(("center", top))
    )


def _build_hashtags(niche, language):
    key = str(niche or "gospel").lower()
    if key in NICHE_HASHTAGS:
        tags = list(NICHE_HASHTAGS[key])
    else:
        tags = ["#shorts", "#reels", "#viral", "#trending"]
    if str(language).lower() in ("swahili", "sw") and "#swahili" not in tags:
        tags.append("#swahili")
    return tags[:10]


def _save_social_kit(video_path, title, hook, subtitles, niche, language):
    tags = _build_hashtags(niche, language)
    punchline = " ".join(s["text"] for s in subtitles[:3]).strip()
    data = {
        "title": title,
        "hook": hook,
        "punchline": punchline,
        "niche": niche,
        "language": language,
        "hashtags": tags,
        "youtube_shorts": {
            "title": f"{title} #Shorts",
            "description": f"{hook}\n\n{punchline}\n\n{' '.join(tags)}",
        },
        "tiktok": {
            "caption": f"{hook}\n\n{punchline}\n\n{' '.join(tags)}",
        },
        "instagram": {
            "caption": f"{title}\n\n{hook}\n\n{' '.join(tags)}",
        },
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    output_path = Path(video_path)
    json_path = output_path.with_name(f"{output_path.stem}_social_kit.json")
    txt_path = output_path.with_name(f"{output_path.stem}_social_kit.txt")

    try:
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = [
            "=" * 62,
            f"SOCIAL KIT - {title}",
            "=" * 62,
            "",
            "HOOK:",
            hook,
            "",
            "CAPTION (TikTok / Reels):",
            data["tiktok"]["caption"],
            "",
            "YOUTUBE SHORTS TITLE:",
            data["youtube_shorts"]["title"],
            "",
            "YOUTUBE SHORTS DESCRIPTION:",
            data["youtube_shorts"]["description"],
            "",
            "HASHTAGS:",
            " ".join(tags),
            "",
            "=" * 62,
        ]
        txt_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        print(f"  Warning: social kit not saved: {exc}")

    return data


def render_clip(video_path, clip, output_name=None, aspect_ratio="9:16",
                crop_position="center", mood="cinematic", niche="gospel",
                language="english", log=None):
    from moviepy import VideoFileClip, CompositeVideoClip
    import config.settings as settings

    log = log or print
    requested_path = video_path
    video_path = resolve_video(video_path)
    if not video_path:
        raise FileNotFoundError(f"Longform video not found: {requested_path}")

    start = float(clip.get("start", 0))
    end = float(clip.get("end", start + 30))
    if end <= start:
        raise ValueError("Clip end must be greater than clip start.")

    title = clip.get("title") or _make_title(clip.get("text", ""))
    hook = clip.get("hook") or title
    subtitles = clip.get("subtitles") or []

    ensure_dirs()
    target_w, target_h = _target_size(aspect_ratio)
    if output_name is None:
        stamp = now_stamp()
        output_name = f"clip_{sanitize_name(title)}_{stamp}.mp4"
    output_path = CLIPS_DIR / output_name

    log(f"Rendering clip: {title} ({start:.1f}s - {end:.1f}s)")

    source = VideoFileClip(str(video_path))
    source_duration = float(source.duration)
    render_end = min(end, source_duration)
    base = None
    final = None
    layers = []
    try:
        base = source.subclipped(start, render_end)
        base = _reframe(base, target_w, target_h, crop_position)

        for subtitle in subtitles:
            if float(subtitle.get("end", 0)) <= 0:
                continue
            layer = _caption_layer(subtitle, target_w, target_h, mood, aspect_ratio)
            if layer is not None:
                layers.append(layer)

        final = CompositeVideoClip([base] + layers, size=(target_w, target_h))
        final = final.with_duration(max(0.5, float(base.duration)))

        temp_audio = TEMP_DIR / f"clipper_audio_{sanitize_name(title)}_{int(time.time())}.m4a"
        threads = settings.ENCODE_THREADS or None
        final.write_videofile(
            str(output_path),
            fps=settings.FPS,
            codec=settings.VIDEO_CODEC,
            audio_codec=settings.AUDIO_CODEC,
            bitrate=settings.BITRATE,
            audio_bitrate=settings.AUDIO_BITRATE,
            preset=settings.PRESET,
            ffmpeg_params=["-crf", str(settings.VIDEO_CRF), "-movflags", "+faststart"],
            threads=threads,
            temp_audiofile=str(temp_audio),
            remove_temp=True,
            logger=None,
        )
    finally:
        for layer in layers:
            try:
                layer.close()
            except Exception:
                pass
        try:
            if final is not None:
                final.close()
        except Exception:
            pass
        try:
            if base is not None:
                base.close()
        except Exception:
            pass
        try:
            source.close()
        except Exception:
            pass

    social_kit = _save_social_kit(
        output_path,
        title=title,
        hook=hook,
        subtitles=subtitles,
        niche=niche,
        language=language,
    )

    log(f"Done: {output_path.name}")
    return {
        "name": output_path.name,
        "path": str(output_path),
        "url": f"/output/videos/{output_path.name}",
        "title": title,
        "hook": hook,
        "start": start,
        "end": end,
        "duration": round(render_end - start, 2),
        "social_kit": social_kit,
    }


def render_selected_clips(video_path, clips, aspect_ratio="9:16", crop_position="center",
                          mood="cinematic", niche="gospel", language="english",
                          progress=None, log=None):
    log = log or print
    progress = progress or (lambda pct, step="": None)
    total = max(1, len(clips))
    outputs = []

    for index, clip in enumerate(clips):
        base_pct = 5 + int((index / total) * 88)
        progress(base_pct, f"Rendering clip {index + 1}/{total}...")
        output = render_clip(
            video_path,
            clip,
            aspect_ratio=aspect_ratio,
            crop_position=crop_position,
            mood=mood,
            niche=niche,
            language=language,
            log=log,
        )
        outputs.append(output)

    progress(100, f"Rendered {len(outputs)} clip(s)")
    return {"clips": outputs}

