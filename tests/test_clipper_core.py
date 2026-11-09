# -*- coding: utf-8 -*-
"""
Core unit tests for the Longform Clipper (pure Python — no ffmpeg,
no Whisper model, no network). Run directly:

    python tests/test_clipper_core.py

Also wired into CI (.github/workflows/ci.yml) so scoring/caption/selection
regressions are caught on every push.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np

from src.video.longform_clipper import (
    _box_smooth,
    _duck_gain,
    _flatten_groq,
    _reframe,
    _slugify,
    build_candidates,
    resolve_selection,
    words_to_subtitles,
)


def _fake_words(duration=100.0, wps=3.0, start=1.0, rms=0.12):
    """Regular speech stream at `wps` words/second with sentence marks."""
    sentences = [
        "Mungu ni mwema kila siku na neema yake ni mpya.",
        "Je, umewahi kuona jinsi anavyotenda miujiza leo?",
        "Bibilia inasema sura tatu aya tano ndio msingi wa imani.",
        "Usikate tamaa kwa sababu yeye husikiliza maombi yako.",
    ]
    words, t, i = [], start, 0
    gap = 1.0 / wps
    while t < start + duration:
        for w in sentences[i % len(sentences)].split():
            if t >= start + duration:
                break
            words.append({"word": " " + w, "start": round(t, 3),
                          "end": round(t + gap * 0.8, 3), "rms": rms})
            t += gap
        t += 0.35          # breath between sentences
        i += 1
    return words


# ── build_candidates ────────────────────────────────────────────

def test_build_candidates_scores_and_bounds():
    words = _fake_words(duration=120.0)
    cands = build_candidates(words, min_dur=15, max_dur=40, source_duration=120.0)
    assert cands, "expected candidates"
    for c in cands:
        assert 15 * 0.75 <= c["duration"] <= 40 * 1.2, c
        assert c["rank"] >= 1
        assert c["score"] > 0
    # ranks unique, sorted by score desc
    ranks = [c["rank"] for c in cands]
    assert len(ranks) == len(set(ranks))
    scores = [c["score"] for c in cands]
    assert scores == sorted(scores, reverse=True)
    # questions detected (Swahili interrogatives in the corpus)
    assert any(c["question"] for c in cands)


def test_build_candidates_overlap_dedupe():
    words = _fake_words(duration=60.0)
    # force overlap: build twice and ensure dedupe keeps windows apart
    cands = build_candidates(words, min_dur=10, max_dur=30, source_duration=60.0)
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            a, b = cands[i], cands[j]
            ov = min(a["end"], b["end"]) - max(a["start"], b["start"])
            if ov > 0:
                shorter = min(a["duration"], b["duration"])
                assert ov / shorter <= 0.30, (a, b)


def test_build_candidates_empty():
    assert build_candidates([], 20, 50) == []


# ── words_to_subtitles ──────────────────────────────────────────

def test_words_to_subtitles_chunking():
    words = _fake_words(duration=30.0, wps=3.0)
    cues = words_to_subtitles(words, max_words=4, max_chars=34, max_gap=0.65)
    assert cues
    for cue in cues:
        n_words = len(cue["text"].split())
        assert n_words <= 4, cue
        assert len(cue["text"]) <= 40, cue          # +slack for punctuation
        assert cue["end"] > cue["start"]
        assert cue["words"], "cue must keep word timings for karaoke"
    # no big time gaps inside a cue (breath 0.35s > 0.65? breath is 0.35 →
    # same-cue words must respect max_gap)
    for cue in cues:
        ws = [w["start"] for w in cue["words"]]
        assert ws == sorted(ws)


def test_words_to_subtitles_window_clamp():
    words = _fake_words(duration=30.0, start=10.0)
    cues = words_to_subtitles(words, max_words=4, window=(12.0, 20.0))
    for cue in cues:
        assert cue["start"] >= 12.0
        assert cue["end"] <= 20.0


# ── resolve_selection ───────────────────────────────────────────

def test_resolve_selection_paths():
    words = _fake_words(duration=90.0)
    cands = build_candidates(words, min_dur=12, max_dur=30, source_duration=90.0)
    analysis = {"words": words, "candidates": cands}

    # auto top-N
    r = resolve_selection(analysis, None, count=2)
    assert len(r) == min(2, len(cands))

    # exact window match
    c0 = cands[0]
    r = resolve_selection(analysis, [{"start": c0["start"], "end": c0["end"]}])
    assert r[0]["rank"] == c0["rank"]

    # window not in candidates → rebuilt from words
    r = resolve_selection(analysis, [{"start": 55.0, "end": 70.0}])
    assert len(r) == 1
    assert 54.9 <= r[0]["start"] <= 56.0
    assert len(r[0]["text"]) > 20

    # ranks + duplicate window + unknown rank → deduped/tolerated
    r = resolve_selection(
        analysis,
        [cands[0]["rank"], {"start": c0["start"], "end": c0["end"]}, 999],
    )
    assert len(r) == 1


# ── _reframe (stub clip — pure geometry) ───────────────────────

class _StubClip:
    """Duck-types a moviepy clip: records crop/resize geometry."""
    def __init__(self, w, h):
        self.size = (w, h)
        self.ops = []

    def cropped(self, x_center=None, y_center=None, width=None, height=None, **kw):
        self.ops.append(("crop", x_center, y_center, width, height))
        c = _StubClip(int(width), int(height))
        c.ops = self.ops
        return c

    def resized(self, size):
        self.ops.append(("resize", size))
        c = _StubClip(size[0], size[1])
        c.ops = self.ops
        return c


def test_reframe_geometry():
    # 16:9 landscape → window is 9:16 slice of full height, centered
    s = _reframe(_StubClip(1280, 720), 1080, 1920, "center")
    crop = s.ops[0]
    assert crop[0] == "crop"
    _, x_c, y_c, w, h = crop
    assert h == 720
    assert w == round(720 * 9 / 16)                   # 405
    assert x_c == 640 and y_c == 360                  # centered
    assert s.ops[-1] == ("resize", (1080, 1920))

    # left focus keeps left edge
    s = _reframe(_StubClip(1280, 720), 1080, 1920, "left")
    assert s.ops[0][1] == round(405 / 2)

    # portrait source → trims height instead
    s = _reframe(_StubClip(720, 1280), 1080, 1920, "bottom")
    _, x_c, y_c, w, h = s.ops[0]
    assert w == 720
    assert h == round(720 * 16 / 9)
    assert y_c == 1280 - h // 2                       # bottom focus


# ── ducking envelope ───────────────────────────────────────────

def test_box_smooth_shape_and_mean():
    x = np.zeros(1000, dtype=np.float32)
    x[400:600] = 1.0
    y = _box_smooth(x, 50)
    assert y.shape == x.shape
    assert y.max() <= 1.0 + 1e-6
    assert abs(float(y.mean()) - float(x.mean())) < 0.05
    # smoothing must reduce the sharp edge
    assert np.abs(np.diff(y)).max() < np.abs(np.diff(x)).max()


def test_duck_gain_speech_vs_pause():
    dur, fps = 10.0, 44100
    words = [
        {"start": 2.0, "end": 3.0},    # absolute (offset applied below)
        {"start": 5.0, "end": 6.0},
    ]
    g = _duck_gain(words, dur, offset=0.0, fps=fps, low=0.15, high=0.45)
    assert g.shape == (int(dur * fps),)
    assert np.all(np.isfinite(g))
    pause = g[int(0.5 * fps)]         # opening pause → high
    speech = g[int(2.5 * fps)]        # inside speech → low
    assert pause > 0.35
    assert speech < pause
    # offset mapping: words at absolute 5s with offset 4s → local 1s
    g2 = _duck_gain(words, dur, offset=4.0, fps=fps, low=0.15, high=0.45)
    assert g2[int(1.2 * fps)] < g2[int(0.3 * fps)]


# ── Groq flatten + misc ────────────────────────────────────────

def test_flatten_groq_offsets_words():
    res = {
        "language": "sw",
        "segments": [
            {"text": " a", "start": 0.0, "end": 2.0,
             "words": [{"word": " a", "start": 0.0, "end": 0.9},
                       {"word": " b", "start": 1.0, "end": 1.9}]},
            {"text": " c", "start": 2.0, "end": 4.0,
             "words": [{"word": " c", "start": 2.0, "end": 3.5}]},
        ],
    }
    words, code = _flatten_groq(res, offset=700.0)
    assert code == "sw"
    assert len(words) == 3
    assert words[0]["start"] == 700.0
    assert words[-1]["end"] == 703.5
    assert words[0]["word"] == "a"     # stripped


def test_slugify():
    assert _slugify("Karibu tena wana wa Mungu") == "Karibu_Tena_Wana_Wa"
    assert _slugify("", fallback="clip") == "clip"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception as e:
            failed += 1
            import traceback
            print(f"  ✗ {t.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} clipper core tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
