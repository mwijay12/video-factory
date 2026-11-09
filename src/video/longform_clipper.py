# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY - LONGFORM → VERTICAL SHORTS CLIPPER
# Sermons / podcasts / interviews  →  1080x1920 captioned clips
#
# Pipeline:
#   1. extract_audio     (ffmpeg  → 16kHz mono WAV)
#   2. transcribe_audio  (faster-whisper, word-level timestamps)
#   3. build_candidates  (scored hook/question/number/density windows)
#   4. render_clip       (9:16 reframe + grouped caption overlays)
#   5. _save_social_kit  (copy-paste captions + niche hashtags)
# ================================================================

import json
import os
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import (
    OUTPUT_DIR,
    ASSETS_DIR,
    FPS,
    VIDEO_CODEC,
    AUDIO_CODEC,
    BITRATE,
    PRESET,
    VIDEO_CRF,
    AUDIO_BITRATE,
    ENCODE_THREADS,
)

# ── Layout & limits ─────────────────────────────────────────────
SOURCE_DIR = Path(ASSETS_DIR) / "longform"
TRANSCRIPT_DIR = Path(OUTPUT_DIR) / "longform"
CLIP_WIDTH = 1080
CLIP_HEIGHT = 1920
SUBTITLE_Y_RATIO = 0.58          # captions sit just below centre
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
MAX_CANDIDATES = 12

# faster-whisper language codes
WHISPER_LANG = {
    "auto": None, "": None,
    "english": "en", "en": "en",
    "swahili": "sw", "sw": "sw",
}
LANG_LABEL = {"en": "english", "sw": "swahili"}

# ── Hook / question / number detectors (EN + SW) ───────────────
HOOK_KEYWORDS = [
    # English
    "imagine", "listen", "nobody", "most people", "stop scrolling",
    "never", "always", "the secret", "here's why", "you need to",
    "truth", "mistake", "powerful", "important", "research",
    "finally", "warning", "remember", "right now", "the problem",
    "god", "jesus", "christ", "faith", "prayer", "bible", "church",
    "pastor", "verses", "holy spirit",
    # Swahili
    "sikia", "fikiria", "ukweli", "siri", "usikose", "lazima",
    "kwa nini", "jinsi ya", "tazama", "leo hii", "muhimu sana",
    "unajua", "kumbuka", "hakuna", "mabadiliko", "baraka",
    "maombi", "neema", "yesu", "mungu", "neno la", "kristo",
    "imani", "pendo", "wokovu", "kanisa",
]
QUESTION_STARTERS = [
    "what ", "why ", "how ", "who ", "when ", "where ", "which ",
    "have you", "do you", "are you", "is there", "can you", "did you",
    "nini", "kwa nini", "je ", "je,", "je?", "namna", "lini", "nani",
    "wapi", "umewahi", "unaona", "unafikiri",
]
NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "twenty", "thirty",
    "moja", "mbili", "tatu", "nne", "tano", "sita", "saba", "nane",
    "tisa", "kumi", "kumi na", "ishirini", "thelathini",
}


def log(msg):
    print(msg, flush=True)


# ================================================================
# SOURCE DISCOVERY
# ================================================================

def ensure_source_dir():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    return SOURCE_DIR


def list_source_videos():
    """Return longform source videos (newest first) with metadata."""
    ensure_source_dir()
    items = []
    for f in sorted(SOURCE_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix.lower() not in VIDEO_EXTS:
            continue
        st = f.stat()
        transcript = TRANSCRIPT_DIR / f"{f.stem}_transcript.json"
        info = {
            "name": f.name,
            "path": str(f),
            "size_mb": round(st.st_size / (1024 * 1024), 2),
            "duration": probe_duration(f),
            "analyzed": transcript.exists(),
            "analyzed_at": "",
            "candidates_count": 0,
        }
        if transcript.exists():
            try:
                t = json.loads(transcript.read_text(encoding="utf-8"))
                info["analyzed_at"] = t.get("created_at", "")
                info["candidates_count"] = len(t.get("candidates", []))
            except Exception:
                pass
        items.append(info)
    return items


def print_source_list():
    items = list_source_videos()
    print("")
    print("=" * 72)
    print("  LONGFORM SOURCES  (assets/longform/)")
    print("=" * 72)
    if not items:
        print("  No videos found.")
        print("  Drop sermon/podcast files (.mp4 .mov .mkv .webm) into:")
        print(f"  {SOURCE_DIR}")
        print("=" * 72)
        return
    for i, it in enumerate(items, 1):
        dur = f"{int(it['duration'])}s" if it.get("duration") else "?"
        mark = "✓ analyzed" if it["analyzed"] else "not analyzed"
        print(f"  {i:>2}. {it['name']:<44} {dur:>7}  {it['size_mb']:>8.1f} MB  [{mark}]")
    print("=" * 72)
    print("  Render with:  python main.py --clip-longform            (newest source)")
    print("                python main.py --clip-longform <name>     (specific source)")
    print("")


def resolve_video(source):
    """Resolve a user-supplied source name/path against assets/longform."""
    ensure_source_dir()
    if not source or str(source).lower() in ("auto", "newest", "latest"):
        vids = [f for f in SOURCE_DIR.iterdir()
                if f.is_file() and f.suffix.lower() in VIDEO_EXTS]
        if not vids:
            raise FileNotFoundError(
                f"No source videos found in {SOURCE_DIR}. "
                "Add a sermon/podcast video first."
            )
        return max(vids, key=lambda p: p.stat().st_mtime)

    p = Path(str(source))
    if p.exists() and p.is_file() and p.suffix.lower() in VIDEO_EXTS:
        return p

    direct = SOURCE_DIR / p.name
    if direct.exists():
        return direct

    stem = p.stem.lower()
    matches = [f for f in SOURCE_DIR.iterdir()
               if f.is_file() and f.suffix.lower() in VIDEO_EXTS
               and (f.stem.lower() == stem or stem in f.stem.lower())]
    if matches:
        return max(matches, key=lambda q: q.stat().st_mtime)

    raise FileNotFoundError(
        f"Source video '{source}' not found. Use --clip-list to see available files."
    )


# ================================================================
# FFMPEG HELPERS
# ================================================================

def _require_ffmpeg(tool):
    from shutil import which
    if which(tool) is None:
        raise RuntimeError(
            f"'{tool}' not found on PATH. Install ffmpeg "
            "(https://ffmpeg.org) and make sure it is available in your shell."
        )


def probe_duration(path):
    """Duration in seconds via ffprobe (None when unavailable)."""
    try:
        _require_ffmpeg("ffprobe")
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception:
        return None


def extract_audio(video_path, wav_path):
    """Extract 16kHz mono PCM audio (Whisper's preferred input)."""
    _require_ffmpeg("ffmpeg")
    wav_path = Path(wav_path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        "-loglevel", "error", str(wav_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if res.returncode != 0 or not wav_path.exists():
        raise RuntimeError(f"ffmpeg audio extraction failed: {res.stderr[-500:]}")
    return wav_path


def _load_wav(path):
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        data = np.frombuffer(wf.readframes(n), dtype=np.int16).astype(np.float32)
        data /= 32768.0
    return data, sr


def _attach_word_energy(wav_path, words):
    """Per-word RMS (0..1-ish) so candidates can be re-scored from cache."""
    try:
        data, sr = _load_wav(wav_path)
    except Exception:
        return
    for w in words:
        a = int(w.get("start", 0) * sr)
        b = int(w.get("end", 0) * sr)
        if 0 <= a < b <= len(data):
            seg = data[a:b]
            w["rms"] = float(np.sqrt(np.mean(seg * seg)))
        else:
            w["rms"] = 0.0


# ================================================================
# TRANSCRIPTION — local faster-whisper + Groq cloud offload
# ================================================================

def _groq_available():
    try:
        from config.settings import ENV
        return bool((ENV.get("GROQ_KEYS", "") or "").strip()
                    or (ENV.get("GROQ_API_KEY", "") or "").strip())
    except Exception:
        return False


def _flatten_groq(res, offset, language_hint=None):
    """Groq verbose_json → clipper word list (absolute times)."""
    words = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            token = (w.get("word") or "").strip()
            if not token:
                continue
            words.append({
                "word": token,
                "start": round(float(w.get("start", 0)) + offset, 3),
                "end": round(float(w.get("end", 0)) + offset, 3),
            })
    code = language_hint or res.get("language") or None
    return words, code


def _transcribe_groq_chunked(wav_path, language="auto", progress_cb=None,
                             chunk_sec=700):
    """
    Cloud STT via the repo's key-rotating Groq client.
    Long sermons are split into ~700s WAV chunks (25MB upload cap).
    Returns (words, language_code) or (None, None) → caller falls back local.
    """
    from src.audio.lyrics_mode import transcribe_with_groq_api

    wav_path = Path(wav_path)
    if not wav_path.exists():
        return None, None

    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        n_total = wf.getnframes()
        total_sec = n_total / sr
        sw = wf.getsampwidth()
        ch = wf.getnchannels()

        def _read_at(start_sec, count_frames):
            wf.setpos(min(int(start_sec * sr), n_total))
            return wf.readframes(count_frames)

        # single shot — no chunking needed
        if total_sec <= chunk_sec:
            res = transcribe_with_groq_api(wav_path, language=language)
            if not res:
                return None, None
            words, code = _flatten_groq(res, 0.0)
            return (words or None), code

        tmp_dir = TRANSCRIPT_DIR / "_groq_chunks"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        words, code = [], None
        try:
            t0, idx = 0.0, 0
            while t0 < total_sec:
                frames = _read_at(t0, min(int(chunk_sec * sr),
                                          n_total - int(t0 * sr)))
                if not frames:
                    break
                cp = tmp_dir / f"chunk_{idx:03d}.wav"
                with wave.open(str(cp), "wb") as out:
                    out.setnchannels(ch)
                    out.setsampwidth(sw)
                    out.setframerate(sr)
                    out.writeframes(frames)

                res = transcribe_with_groq_api(cp, language=language)
                try:
                    cp.unlink(missing_ok=True)
                except Exception:
                    pass
                if not res:
                    # any chunk failing (keys/rate-limit) → full local retry
                    return None, None

                part, c2 = _flatten_groq(res, t0, language_hint=None)
                words.extend(part)
                code = code or c2

                idx += 1
                t0 += chunk_sec
                if progress_cb:
                    frac = min(1.0, t0 / total_sec)
                    progress_cb(
                        12 + int(frac * 46),
                        f"Groq cloud STT chunk {idx}... {int(frac * 100)}%",
                    )
        finally:
            try:
                if tmp_dir.exists() and not any(tmp_dir.iterdir()):
                    tmp_dir.rmdir()
            except Exception:
                pass

    return (words or None), code


def transcribe_audio(wav_path, model_size="base", language="auto",
                     progress_cb=None, stt="local"):
    """Word-level transcript. stt: 'local' (faster-whisper) | 'groq' (cloud)."""
    if str(stt).lower() == "groq":
        if not _groq_available():
            log("  ⚠ Groq STT requested but GROQ_API_KEY/GROQ_KEYS not set "
                "— falling back to local Whisper.")
        else:
            if progress_cb:
                progress_cb(10, "Groq cloud STT (chunked upload)...")
            g_words, g_code = _transcribe_groq_chunked(
                wav_path, language=language, progress_cb=progress_cb
            )
            if g_words:
                label = LANG_LABEL.get(g_code, g_code or "auto")
                if progress_cb:
                    progress_cb(60, f"Cloud transcript ready ({len(g_words)} words)")
                return {
                    "language": label,
                    "language_code": g_code or "en",
                    "words": g_words,
                    "provider": "groq",
                }
            log("  ⚠ Groq STT unavailable — falling back to local Whisper.")

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from e

    lang_code = WHISPER_LANG.get(str(language).lower(), None)
    if language and str(language).lower() not in WHISPER_LANG:
        lang_code = str(language)[:2]

    if progress_cb:
        progress_cb(10, f"Loading Whisper model '{model_size}'...")

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    total = probe_duration(wav_path) or 0.0
    segments, info = model.transcribe(
        str(wav_path),
        language=lang_code,
        word_timestamps=True,
        vad_filter=True,
        beam_size=1,
    )

    words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                token = (w.word or "").strip()
                if not token:
                    continue
                words.append({
                    "word": w.word if w.word.startswith(" ") else f" {token}",
                    "start": round(float(w.start), 3),
                    "end": round(float(w.end), 3),
                })
        if progress_cb and total > 0 and seg.end > 0:
            frac = min(1.0, float(seg.end) / total)
            progress_cb(
                12 + int(frac * 46),
                f"Transcribing speech... {int(frac * 100)}%",
            )

    detected = getattr(info, "language", None) or lang_code or "en"
    return {
        "language": LANG_LABEL.get(detected, detected),
        "language_code": detected,
        "words": words,
        "provider": "local",
    }


# ================================================================
# CANDIDATE SCORING
# ================================================================

def _blk_dur(block):
    return block[-1]["end"] - block[0]["start"]


def _clean_word(w):
    return (w.get("word") or "").strip()


def _joined_text(block):
    return " ".join(_clean_word(w) for w in block).strip()


def _looks_sentence_end(w):
    t = _clean_word(w).rstrip()
    return bool(t) and t[-1] in ".!?…"


def _split_on_pauses(words, max_gap=1.7):
    blocks, cur = [], []
    for w in words:
        if cur and (w["start"] - cur[-1]["end"]) > max_gap:
            blocks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        blocks.append(cur)
    return blocks


def _split_long(block, min_dur, max_dur):
    """Split an over-long block at sentence ends, then at max_dur."""
    pieces, cur = [], []
    for w in block:
        cur.append(w)
        d = _blk_dur(cur)
        if d >= max_dur:
            pieces.append(cur)
            cur = []
        elif d >= max(min_dur * 0.9, max_dur * 0.6) and _looks_sentence_end(w):
            pieces.append(cur)
            cur = []
    if cur:
        if len(cur) >= 3 and pieces and _blk_dur(cur) < min_dur * 0.8:
            pieces[-1].extend(cur)          # glue tiny tail to previous
        else:
            pieces.append(cur)
    return pieces


def build_candidates(words, min_dur=20.0, max_dur=50.0, source_duration=None):
    """
    Turn a word stream into scored clip candidates.
    EN/SW hook keywords, questions, numbers, word-density, position,
    duration fit and normalised RMS energy, with 30% overlap dedupe.
    """
    if not words:
        return []
    if min_dur <= 0:
        min_dur = 20.0
    if max_dur <= min_dur:
        max_dur = min_dur + 10.0
    source_duration = source_duration or (words[-1]["end"] + 1.0)

    # ── 1. speech blocks: split on pauses, merge short ones, slice long ones ──
    raw_blocks = _split_on_pauses(words)
    blocks = []
    i = 0
    while i < len(raw_blocks):
        cur = list(raw_blocks[i])
        j = i
        # merge forwards while we're under the minimum useful length
        while _blk_dur(cur) < min_dur and j + 1 < len(raw_blocks):
            nxt = raw_blocks[j + 1]
            gap = nxt[0]["start"] - cur[-1]["end"]
            if gap > 2.5 or _blk_dur(cur) + _blk_dur(nxt) > max_dur * 1.2:
                break
            cur.extend(nxt)
            j += 1
        for piece in _split_long(cur, min_dur, max_dur):
            d = _blk_dur(piece)
            wc = len(piece)
            if d >= min(min_dur, 8.0) and wc >= 4 and d <= max_dur * 1.15:
                blocks.append(piece)
        i = j + 1

    # ── 2. score each block ──
    cands = []
    for block in blocks:
        start = float(block[0]["start"])
        end = float(block[-1]["end"])
        dur = max(0.1, end - start)
        text = _joined_text(block)
        if len(text) < 12:
            continue
        text_l = text.lower()

        hooks = sum(
            1 for k in HOOK_KEYWORDS
            if re.search(r"\b" + re.escape(k) + r"\b", text_l)
        )
        question = ("?" in text) or any(
            text_l.startswith(s) or f" {s}" in f" {text_l}"
            for s in QUESTION_STARTERS
        )
        tokens = set(re.findall(r"[a-zà-ÿ']+", text_l))
        has_number = bool(re.search(r"\d", text)) or bool(tokens & NUMBER_WORDS)

        wps = len(block) / dur
        density = max(0.0, 1.0 - abs(wps - 3.0) / 2.5)

        if min_dur <= dur <= max_dur:
            dur_score = 1.0
        else:
            window = max(6.0, (max_dur - min_dur) / 2)
            outside = (min_dur - dur) if dur < min_dur else (dur - max_dur)
            dur_score = max(0.0, 1.0 - outside / window)

        pos = start / max(1.0, source_duration)
        if pos < 0.15:
            pos_score = 1.0                 # intro hook territory
        elif pos < 0.60:
            pos_score = 0.85
        else:
            pos_score = 0.70

        rms_vals = [w.get("rms", None) for w in block if w.get("rms") is not None]
        energy = float(np.mean(rms_vals)) if rms_vals else None

        score = (
            min(hooks, 4) * 1.2
            + (1.6 if question else 0.0)
            + (1.0 if has_number else 0.0)
            + 1.5 * density
            + 1.2 * dur_score
            + 0.6 * pos_score
        )
        cands.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(dur, 2),
            "text": text,
            "words_count": len(block),
            "wps": round(wps, 2),
            "score": round(score, 3),
            "hooks": int(hooks),
            "question": bool(question),
            "number": bool(has_number),
            "energy": None if energy is None else round(energy, 5),
            "position": round(pos, 3),
            "_block": block,
        })

    if not cands:
        return []

    # ── 3. normalised energy component ──
    energies = [c["energy"] for c in cands if c["energy"] is not None]
    e_max = max(energies) if energies else 0.0
    for c in cands:
        if c["energy"] is None or e_max <= 0:
            c["score"] = round(c["score"] + 1.2 * 0.5, 3)
        else:
            c["score"] = round(c["score"] + 1.2 * (c["energy"] / e_max), 3)

    # ── 4. rank, dedupe overlapping windows (keep best 70%) ──
    cands.sort(key=lambda c: c["score"], reverse=True)
    chosen = []
    for c in cands:
        dup = False
        for k in chosen:
            ov = min(c["end"], k["end"]) - max(c["start"], k["start"])
            if ov > 0:
                shorter = min(c["duration"], k["duration"])
                if ov / max(0.001, shorter) > 0.30:
                    dup = True
                    break
        if not dup:
            chosen.append(c)
        if len(chosen) >= MAX_CANDIDATES:
            break

    for idx, c in enumerate(chosen, 1):
        c["rank"] = idx
        c.pop("_block", None)
    return chosen


# ================================================================
# SUBTITLE CHUNKING
# ================================================================

def words_to_subtitles(words, max_words=4, max_chars=34, max_gap=0.65, window=None):
    """Group word-level tokens into short caption cues."""
    max_words = max(1, int(max_words or 4))
    cues, cur = [], []

    def flush():
        if not cur:
            return
        start = float(cur[0]["start"])
        end = float(cur[-1]["end"])
        if end - start < 0.30:
            end = start + 0.45
        text = " ".join(_clean_word(w) for w in cur)
        if text:
            cues.append({
                "text": text,
                "start": start,
                "end": end,
                "words": [dict(w) for w in cur],   # word timings for karaoke
            })

    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            joined = len(" ".join(_clean_word(x) for x in cur)) + 1 + len(_clean_word(w))
            if gap > max_gap or len(cur) >= max_words or joined > max_chars:
                flush()
                cur = []
        cur.append(w)
    flush()

    if window:
        w0, w1 = window
        for cue in cues:
            cue["start"] = max(cue["start"], w0)
            cue["end"] = min(max(cue["end"], cue["start"] + 0.2), w1)
    return cues


# ================================================================
# ANALYSIS
# ================================================================

def transcript_path_for(video_path):
    return TRANSCRIPT_DIR / f"{Path(video_path).stem}_transcript.json"


def analyze_video(source, model="base", language="auto",
                  min_dur=20.0, max_dur=50.0,
                  use_cache=True, progress_cb=None, stt="local"):
    """
    Full analysis: audio → transcript → scored candidates.
    stt: 'local' (faster-whisper) or 'groq' (cloud, chunked upload).
    Reuses a cached transcript when it is fresh and params match;
    min/max re-scoring happens without touching Whisper.
    Returns dict with words + candidates + transcript_path.
    """
    def cb(pct, step):
        if progress_cb:
            progress_cb(pct, step)

    video = resolve_video(source)
    ensure_source_dir()
    cb(3, f"Probing source: {video.name}")

    duration = probe_duration(video)
    t_path = transcript_path_for(video)

    words = None
    detected_lang = language

    # ── cache: fresh transcript + same model/language → skip whisper ──
    if use_cache and t_path.exists():
        try:
            cached = json.loads(t_path.read_text(encoding="utf-8"))
            fresh = t_path.stat().st_mtime >= video.stat().st_mtime
            same_model = cached.get("model") == model
            cached_lang = cached.get("language", "auto")
            same_lang = (
                str(language).lower() == "auto"
                or cached_lang == str(language).lower()
                or cached_lang == LANG_LABEL.get(WHISPER_LANG.get(str(language).lower()))
            )
            if fresh and same_model and same_lang and cached.get("words"):
                words = cached["words"]
                duration = duration or cached.get("duration")
                detected_lang = cached.get("language", "auto")
                cb(8, "Using cached transcript (re-scoring only)...")
        except Exception:
            words = None

    wav_path = TRANSCRIPT_DIR / f"{video.stem}_audio.wav"
    if words is None:
        cb(5, "Extracting audio track (ffmpeg)...")
        extract_audio(video, wav_path)
        try:
            result = transcribe_audio(
                wav_path, model_size=model, language=language,
                progress_cb=cb, stt=stt,
            )
            words = result["words"]
            detected_lang = result["language"]
        finally:
            # per-word energy before cleaning up the wav
            if words and wav_path.exists():
                _attach_word_energy(wav_path, words)
            try:
                if wav_path.exists():
                    wav_path.unlink()
            except Exception:
                pass
        if not words:
            raise RuntimeError(
                "Transcription produced no words — is the audio track empty?"
            )
    else:
        # cached words may lack energy if transcript is old → neutral later
        pass

    cb(62, "Scoring clip candidates (hooks, questions, density)...")
    candidates = build_candidates(words, min_dur=min_dur, max_dur=max_dur,
                                  source_duration=duration)

    cb(90, "Saving transcript...")
    payload = {
        "source": video.name,
        "source_path": str(video),
        "language": detected_lang,
        "model": model,
        "stt": stt,
        "duration": duration,
        "word_count": len(words),
        "min_dur": min_dur,
        "max_dur": max_dur,
        "words": words,
        "candidates": candidates,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        t_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log(f"Warning: could not save transcript: {e}")

    cb(100, f"Analysis complete — {len(candidates)} clip candidates")
    return {
        "source": video.name,
        "source_path": str(video),
        "language": detected_lang,
        "model": model,
        "duration": duration,
        "words": words,
        "candidates": candidates,
        "transcript_path": str(t_path),
    }


# ================================================================
# RENDERING
# ================================================================

def _reframe(clip, target_w, target_h, crop_position="center"):
    """
    Cover-fit any aspect ratio into the 9:16 canvas with a focus point.
    Crops the exact source window FIRST, then scales once — same result
    as resize-then-crop, but ~x8 cheaper per frame (critical: moviepy
    runs this for every frame).
    """
    src_w, src_h = clip.size
    target_ar = target_w / target_h
    src_ar = src_w / src_h

    if src_ar > target_ar:          # source wider than 9:16 → trim width
        win_h = src_h
        win_w = src_h * target_ar
    else:                           # source taller than 9:16 → trim height
        win_w = src_w
        win_h = src_w / target_ar

    pos = (crop_position or "center").lower()
    if pos == "left":
        x_c, y_c = win_w / 2, src_h / 2
    elif pos == "right":
        x_c, y_c = src_w - win_w / 2, src_h / 2
    elif pos == "top":
        x_c, y_c = src_w / 2, win_h / 2
    elif pos == "bottom":
        x_c, y_c = src_w / 2, src_h - win_h / 2
    else:  # center
        x_c, y_c = src_w / 2, src_h / 2

    cropped = clip.cropped(
        x_center=int(round(x_c)),
        y_center=int(round(y_c)),
        width=int(round(win_w)),
        height=int(round(win_h)),
    )
    return cropped.resized((target_w, target_h))


def _make_encode_logger(on_progress):
    """ProgressBarLogger subclass → throttled text progress lines."""
    from proglog import ProgressBarLogger

    class _ClipEncodeLogger(ProgressBarLogger):
        def __init__(self, cb):
            super().__init__()
            self._cb = cb
            self._total = 0
            self._last = -1

        def bars_callback(self, bar, attr, value, old_value=None):
            try:
                if bar == "t" and attr == "total":
                    self._total = int(value or 0)
                elif bar == "t" and attr == "index" and self._total > 0:
                    pct = int(value / self._total * 100)
                    if pct >= self._last + 10 or value >= self._total:
                        self._last = pct
                        log(f"    encode: {pct}%")
                        if self._cb:
                            self._cb(pct)
            except Exception:
                pass

    return _ClipEncodeLogger(on_progress)


def _build_karaoke_track(cues, window_start, window_dur, mood="peaceful", y_pos=0):
    """
    One RGBA VideoClip that swaps pre-rendered word-highlight frames
    (same proven pattern as ReelVideoEngine._build_subtitle_layers).
    Cue times are shifted into the clip's relative timeline.
    """
    from moviepy import VideoClip
    from src.video.video_engine import build_subtitle_image_karaoke

    chunks = []
    blank = None
    for cue in cues:
        text = str(cue.get("text", "")).strip()
        if not text:
            continue
        words_text = text.split()
        word_frames = [
            build_subtitle_image_karaoke(
                text=text,
                active_word_index=i,
                width=980,
                font_size=56,
                mood=mood,
            )
            for i in range(len(words_text))
        ]
        if blank is None:
            blank = np.zeros((380, 980, 4), dtype=np.uint8)

        c_start = max(0.0, float(cue["start"]) - window_start)
        c_end = min(window_dur, float(cue["end"]) - window_start)
        if c_end <= c_start:
            continue
        # shift word times into the clip-relative timeline
        shifted_words = [
            {"start": float(w.get("start", 0)) - window_start,
             "end": float(w.get("end", 0)) - window_start}
            for w in (cue.get("words") or [])
        ]
        chunks.append({
            "start": c_start,
            "end": c_end,
            "duration": max(0.01, c_end - c_start),
            "word_frames": word_frames,
            "cue_words": shifted_words,
        })

    if not chunks or blank is None:
        return None

    def make_frame(t):
        for ch in chunks:
            if ch["start"] <= t < ch["end"]:
                frames = ch["word_frames"]
                if len(frames) <= 1:
                    return frames[0]
                idx = 0
                cw = ch["cue_words"]
                if len(cw) == len(frames):
                    # word-accurate highlight from whisper timings
                    for i, w in enumerate(cw):
                        if t >= w["start"]:
                            idx = i
                else:
                    prog = min(1.0, max(0.0, (t - ch["start"]) / ch["duration"]))
                    idx = int(prog * len(frames))
                return frames[min(idx, len(frames) - 1)]
        return blank

    return VideoClip(make_frame, duration=window_dur).with_position(("center", y_pos))


def _box_smooth(x, kernel):
    """O(n) moving-average smoothing (kills envelope clicks)."""
    k = max(1, int(kernel))
    if k == 1 or len(x) <= k:
        return x
    c = np.cumsum(np.insert(np.asarray(x, dtype=np.float64), 0, 0.0))
    sm = (c[k:] - c[:-k]) / k
    return np.concatenate([np.full(k, sm[0]), sm])[:len(x)].astype(np.float32)


def _duck_gain(words, duration, offset=0.0, fps=44100,
               low=0.16, high=0.42, smooth=0.12):
    """
    Word-timed music gain: low while someone is speaking, open in pauses,
    smoothed to avoid clicks. `offset` maps absolute word times to the
    clip-relative envelope grid.
    """
    n = max(1, int(round(duration * fps)))
    target = np.full(n, float(high), dtype=np.float32)
    for w in (words or []):
        a = int(max(0.0, float(w.get("start", 0)) - offset) * fps)
        b = int(min(duration, float(w.get("end", 0)) - offset + 0.12) * fps)
        if b > a:
            target[max(0, a):min(n, b)] = low
    return _box_smooth(target, int(smooth * fps))


def _build_ducked_music(music_path, words, duration, offset, out_path):
    """Decode music → loop/trim → apply duck envelope → stereo wav bed."""
    from moviepy import AudioFileClip
    try:
        m = AudioFileClip(str(music_path))
        try:
            arr = m.to_soundarray(fps=44100)
        except TypeError:
            arr = m.to_soundarray()
        m.close()
    except Exception as e:
        log(f"  ⚠ music bed skipped: {e}")
        return None
    if arr is None or len(arr) == 0:
        return None

    n = int(round(duration * 44100))
    if len(arr) >= n:
        arr = arr[:n]
    else:
        reps = int(np.ceil(n / len(arr)))
        arr = np.tile(arr, (reps, 1))[:n]

    gain = _duck_gain(words, duration, offset=offset, fps=44100)
    arr = arr * (gain[:, None] if arr.ndim > 1 else gain)

    peak = float(np.max(np.abs(arr))) or 1.0
    if peak > 0.95:
        arr = arr * (0.95 / peak)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(2 if data.ndim > 1 else 1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(data.tobytes())
    return out_path


def render_clip(source_path, candidate, words, output_name,
                crop_position="center", words_per_line=4,
                mood="peaceful", language="swahili",
                caption_style="karaoke", music_path=None,
                encode_cb=None):
    """
    Render one candidate: 9:16 reframe + grouped captions (static or
    karaoke word-highlight) + source audio (optional ducked music bed).
    encode_cb(pct0-100) fires during encoding.
    Returns the output Path.
    """
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
    from src.video.video_engine import build_subtitle_image

    start = float(candidate["start"])
    end = float(candidate["end"])
    dur = end - start

    # words inside the window (tolerance for rounding)
    win_words = [w for w in words
                 if w["end"] > start - 0.05 and w["start"] < end + 0.05]
    if not win_words:
        win_words = [
            {"word": f" {t}", "start": start, "end": end}
            for t in candidate.get("text", "").split()
        ]
    cues = words_to_subtitles(
        win_words, max_words=words_per_line, window=(start, end)
    )

    out_path = Path(OUTPUT_DIR) / "videos" / output_name
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seg = None
    base = None
    final = None
    audio = None
    bed_clip = None
    bed_path = None
    try:
        seg = VideoFileClip(str(source_path)).subclipped(start, end).with_start(0)

        try:
            audio = seg.audio
            if audio is not None:
                audio = audio.with_start(0)
        except Exception:
            audio = getattr(seg, "audio", None)

        base = _reframe(seg, CLIP_WIDTH, CLIP_HEIGHT, crop_position)
        try:
            base = base.without_audio()
        except Exception:
            pass

        layers = [base]
        sub_y = int(CLIP_HEIGHT * SUBTITLE_Y_RATIO)
        style = (caption_style or "karaoke").lower()

        if style == "karaoke" and cues:
            track = _build_karaoke_track(cues, start, dur, mood=mood, y_pos=sub_y)
            if track is not None:
                layers.append(track)
        elif style != "none" and cues:
            for cue in cues:
                img = build_subtitle_image(
                    cue["text"],
                    width=980,
                    font_size=56,
                    mood=mood,
                )
                cue_start = max(0.0, cue["start"] - start)
                cue_end = min(dur, cue["end"] - start)
                if cue_end <= cue_start:
                    continue
                layer = (
                    ImageClip(img, transparent=True)
                    .with_start(cue_start)
                    .with_duration(cue_end - cue_start)
                    .with_position(("center", sub_y))
                )
                layers.append(layer)

        final = CompositeVideoClip(layers, size=(CLIP_WIDTH, CLIP_HEIGHT))
        final = final.with_duration(dur)

        if audio is not None and music_path:
            from moviepy import AudioFileClip, CompositeAudioClip
            bed_path = _build_ducked_music(
                music_path, win_words, dur, offset=start,
                out_path=Path("output/temp") / f"bed_{Path(output_name).stem}.wav",
            )
            if bed_path is not None:
                bed_clip = AudioFileClip(str(bed_path)).with_start(0)
                audio = CompositeAudioClip([audio, bed_clip])

        if audio is not None:
            final = final.with_audio(audio)

        import os as _os
        threads = ENCODE_THREADS if ENCODE_THREADS > 0 else (_os.cpu_count() or 4)

        logger = _make_encode_logger(encode_cb) if encode_cb is not None else None

        final.write_videofile(
            str(out_path),
            fps=FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            bitrate=BITRATE,
            audio_bitrate=AUDIO_BITRATE,
            preset=PRESET,
            ffmpeg_params=["-crf", str(VIDEO_CRF), "-movflags", "+faststart"],
            threads=threads,
            logger=logger,
        )
        return out_path
    finally:
        for c in (final, base, seg, audio, bed_clip):
            try:
                if c is not None:
                    c.close()
            except Exception:
                pass
        if bed_path is not None:
            try:
                Path(bed_path).unlink(missing_ok=True)
            except Exception:
                pass


# ================================================================
# SOCIAL KIT (simple, niche-driven — not the full gospel package)
# ================================================================

def _niche_hashtags(niche, language):
    try:
        from src.utils.social_strategy import HASHTAG_POOLS
    except Exception:
        HASHTAG_POOLS = {}
    pool = HASHTAG_POOLS.get(niche)
    if not pool:
        key = "gospel_swahili" if str(language).lower().startswith("sw") else "gospel_english"
        pool = HASHTAG_POOLS.get(key, [])
    return list(pool[:12])


def _save_social_kit(video_path, title, niche, language, candidate):
    video_path = Path(video_path)
    stem = video_path.stem
    hashtags = _niche_hashtags(niche, language)
    tag_str = " ".join(hashtags)

    excerpt = candidate.get("text", "")[:180].strip()
    if len(candidate.get("text", "")) > 180:
        excerpt += "…"

    is_sw = str(language).lower().startswith("sw")
    if is_sw:
        hook = f"🔥 Kipande kilelekiwa cha neno — {title}"
        caption = (
            f"{hook}\n\n\"{excerpt}\"\n\n"
            f"💙 like, 🔄 share, 🙏 comment AMEN\n\n{tag_str}"
        )
    else:
        hook = f"🔥 The moment you needed to hear — {title}"
        caption = (
            f"{hook}\n\n\"{excerpt}\"\n\n"
            f"💙 like, 🔄 share, 🙏 drop an AMEN\n\n{tag_str}"
        )

    data = {
        "title": title,
        "clip": {
            "start": candidate.get("start"),
            "end": candidate.get("end"),
            "duration": candidate.get("duration"),
            "score": candidate.get("score"),
        },
        "hashtags": hashtags,
        "caption": caption,
        "platforms": {
            "tiktok": caption,
            "instagram": caption,
            "youtube_shorts": caption,
        },
        "generated_by": "VideoFactory Longform Clipper",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    json_path = video_path.parent / f"{stem}_social_kit.json"
    txt_path = video_path.parent / f"{stem}_social_kit.txt"
    try:
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        txt_path.write_text(
            "=" * 64 + "\n"
            f"CLIP SOCIAL KIT — {title}\n"
            + "=" * 64 + "\n\n"
            + "CAPTION (copy & paste):\n"
            + "-" * 64 + "\n"
            + caption + "\n",
            encoding="utf-8",
        )
    except Exception as e:
        log(f"Warning: social kit not saved: {e}")
    return {"json": str(json_path), "txt": str(txt_path)}


# ================================================================
# BATCH RENDER
# ================================================================

def _slugify(text, fallback="clip"):
    words_ = re.findall(r"[A-Za-z0-9]+", str(text or ""))[:4]
    slug = "_".join(w.capitalize() for w in words_)
    return slug or fallback


def _candidate_from_window(words, start, end, rank):
    """Build a candidate straight from a picked time window (UI selection
    may have been made under different scoring params — the moment the
    user chose must be the moment we render)."""
    win = [w for w in words
           if w["end"] > start - 0.05 and w["start"] < end + 0.05]
    text = " ".join(_clean_word(w) for w in win)
    dur = max(0.1, end - start)
    return {
        "rank": rank,
        "start": round(start, 2),
        "end": round(end, 2),
        "duration": round(dur, 2),
        "text": text or "(selected moment)",
        "words_count": len(win),
        "wps": round(len(win) / dur, 2),
        "score": 0.0,
        "hooks": 0,
        "question": False,
        "number": False,
        "energy": None,
        "position": 0.0,
    }


def resolve_selection(analysis, selected, count=3):
    """
    Turn a UI/CLI selection into concrete candidates.
      - None/empty → top `count` by score
      - [{"start","end"}...] → exact moments (matched or rebuilt)
      - [rank ints] → candidates of the current scoring
    """
    candidates = analysis.get("candidates") or []
    if not selected:
        return candidates[:max(1, int(count))]

    words = analysis.get("words") or []
    by_rank = {c["rank"]: c for c in candidates}
    chosen, seen = [], set()

    for item in selected:
        if isinstance(item, dict):
            try:
                w0 = round(float(item["start"]), 2)
                w1 = round(float(item["end"]), 2)
            except (KeyError, TypeError, ValueError):
                continue
            match = next(
                (c for c in candidates
                 if abs(c["start"] - w0) <= 0.15 and abs(c["end"] - w1) <= 0.15),
                None,
            )
            if match is not None:
                key = (round(match["start"], 2), round(match["end"], 2))
            else:
                match = _candidate_from_window(words, w0, w1, len(chosen) + 1)
                key = (w0, w1)
            if key in seen:
                continue
            chosen.append(match)
            seen.add(key)
        else:
            try:
                rank = int(item)
            except (TypeError, ValueError):
                continue
            c = by_rank.get(rank)
            if c is None:
                continue
            key = (round(c["start"], 2), round(c["end"], 2))
            if key in seen:
                continue
            chosen.append(c)
            seen.add(key)
    return chosen


def _resolve_music(music, niche):
    """'none' → None | 'auto' → smart niche pick | path → that file."""
    m = str(music or "none").strip().lower()
    if m in ("", "none", "off", "false", "no"):
        return None
    if m == "auto":
        try:
            from src.utils.media_manager import get_smart_music
            picked = get_smart_music(niche=niche)
            if picked and Path(picked).exists():
                log(f"  🎵 music bed: {Path(picked).name}")
                return str(picked)
        except Exception as e:
            log(f"  ⚠ smart music failed: {e}")
        log("  ⚠ no music found for this niche — rendering without bed")
        return None
    p = Path(music)
    if p.exists():
        return str(p)
    log(f"  ⚠ music file not found: {music}")
    return None


def render_selected_clips(analysis, selected=None, count=3,
                          crop_position="center", words_per_line=4,
                          mood="peaceful", niche="gospel", language="swahili",
                          caption_style="karaoke", music="none",
                          progress_cb=None):
    """
    Render chosen moments from a finished analysis.
    selected: [{"start","end"}...] | [rank ints] | None → top `count`.
    caption_style: 'karaoke' | 'static' | 'none'.
    music: 'none' | 'auto' | file path (ducked under speech).
    Returns list of output descriptors.
    """
    def cb(pct, step):
        if progress_cb:
            progress_cb(pct, step)

    candidates = analysis.get("candidates") or []
    if not candidates and not selected:
        raise ValueError("No candidates available — run analysis first.")

    chosen = resolve_selection(analysis, selected, count=count)
    if not chosen:
        raise ValueError("Selected candidates not found in analysis.")

    source_path = Path(analysis["source_path"])
    words = analysis.get("words") or []
    music_path = _resolve_music(music, niche)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    outputs = []
    n = len(chosen)

    for i, cand in enumerate(chosen):
        base = 48 + int((i / n) * 47)          # 48 → 95 across clips
        title = (cand.get("text", "")[:60] or source_path.stem).strip()
        slug = _slugify(cand.get("text") or source_path.stem,
                        fallback=source_path.stem)
        out_name = f"clip_{slug}_{stamp}.mp4"
        out_path = Path(OUTPUT_DIR) / "videos" / out_name
        suffix = 2
        while out_path.exists():
            out_name = f"clip_{slug}_{stamp}_{suffix}.mp4"
            out_path = Path(OUTPUT_DIR) / "videos" / out_name
            suffix += 1

        cb(base, f"Rendering clip {i + 1}/{n}: {title[:48]}...")
        lo, hi = base, base + int(46 / n)

        def encode_pct(p, _lo=lo, _hi=hi, _i=i):
            cb(_lo + int((_hi - _lo) * p / 100),
               f"Encoding clip {_i + 1}/{n}... {p}%")

        render_clip(
            source_path, cand, words, out_name,
            crop_position=crop_position,
            words_per_line=words_per_line,
            mood=mood, language=language,
            caption_style=caption_style,
            music_path=music_path,
            encode_cb=encode_pct,
        )

        kit = _save_social_kit(out_path, title, niche, language, cand)
        size_mb = round(out_path.stat().st_size / (1024 * 1024), 2) \
            if out_path.exists() else 0
        outputs.append({
            "rank": cand["rank"],
            "name": out_name,
            "url": f"/output/videos/{out_name}",
            "title": title,
            "duration": cand["duration"],
            "size_mb": size_mb,
            "social_kit_url": f"/output/videos/{Path(kit['txt']).name}",
        })
        cb(hi, f"✅ Clip {i + 1}/{n} done: {out_name}")

    cb(100, f"All done — {n} clip(s) rendered")
    return outputs


# ================================================================
# CLI PIPELINE (used by: python main.py --clip-longform [name])
# ================================================================

def run_clipper_pipeline(source="auto", language="swahili", model="base",
                         min_dur=20.0, max_dur=50.0, count=3,
                         crop="center", niche="gospel", mood="peaceful",
                         words_per_line=4, stt="local",
                         captions="karaoke", music="none"):
    log("")
    log("=" * 62)
    log("  LONGFORM CLIPPER — analyze → score → render")
    log("=" * 62)

    def cb(pct, step):
        log(f"  PROGRESS:{pct}% STEP:{step}")

    analysis = analyze_video(
        source, model=model, language=language,
        min_dur=min_dur, max_dur=max_dur, progress_cb=cb, stt=stt,
    )
    log("")
    log(f"  Source:  {analysis['source']}")
    log(f"  Language: {analysis['language']}")
    log(f"  Candidates: {len(analysis['candidates'])}")
    for c in analysis["candidates"][:count]:
        log(f"    #{c['rank']}  [{c['start']:.1f}s → {c['end']:.1f}s] "
            f"score={c['score']:.2f}  {c['text'][:70]}")
    log("")

    outputs = render_selected_clips(
        analysis, selected=None, count=count,
        crop_position=crop, words_per_line=words_per_line,
        mood=mood, niche=niche, language=language,
        caption_style=captions, music=music, progress_cb=cb,
    )

    log("")
    log("=" * 62)
    log(f"  RENDERED {len(outputs)} CLIP(S)")
    log("=" * 62)
    for o in outputs:
        log(f"  🎬 {o['name']}  ({o['duration']}s, {o['size_mb']} MB)")
        log(f"     caption kit: {o['social_kit_url']}")
    log("")
    return outputs
