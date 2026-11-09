# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY - LONGFORM CLIPPER WORKER (subprocess job runner)
#
#   python src/scripts/clipper_worker.py --job analyze --payload p.json
#   python src/scripts/clipper_worker.py --job render  --payload p.json
#
# Emits  PROGRESS:N% STEP:...  lines on stdout (captured into the
# job log by the web server) and writes atomic status JSON to
# output/temp/clipper_status.json for the status endpoint.
# ================================================================

import os
import sys
import json
import time
import traceback
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

STATUS_PATH = Path(BASE_DIR) / "output" / "temp" / "clipper_status.json"

# ── status helpers ─────────────────────────────────────────────

_state = {}


def _atomic_write_status():
    try:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATUS_PATH.with_name(STATUS_PATH.name + ".tmp")
        tmp.write_text(
            json.dumps(_state, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        os.replace(tmp, STATUS_PATH)
    except Exception as e:
        print(f"Warning: could not write status file: {e}", flush=True)


def _init_status(job, payload):
    _state.update({
        "job": job,
        "status": "running",
        "progress": 1,
        "step": "Worker starting...",
        "source": payload.get("source", ""),
        "language": payload.get("language", "auto"),
        "model": payload.get("model", "base"),
        "duration": None,
        "word_count": None,
        "transcript_path": "",
        "candidates": [],
        "outputs": [],
        "error": None,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    _atomic_write_status()


def emit(pct=None, step=None):
    """Progress callback: print marker for the log + persist status."""
    if pct is not None:
        _state["progress"] = max(0, min(100, int(pct)))
    if step is not None:
        _state["step"] = str(step)
    _state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    parts = [f"PROGRESS:{_state['progress']}%"]
    if _state.get("step"):
        parts.append(f"STEP:{_state['step']}")
    print(" ".join(parts), flush=True)
    _atomic_write_status()


def scale(lo, hi):
    """Remap a 0-100 sub-progress into the [lo, hi] range."""

    def cb(pct, step=""):
        v = lo + int((hi - lo) * max(0, min(100, int(pct))) / 100)
        emit(v, step)

    return cb


def _fail(message):
    _state["status"] = "failed"
    _state["error"] = str(message)
    _state["step"] = f"❌ {message}"
    _state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"PROGRESS:{_state['progress']}% STEP:{_state['step']}", flush=True)
    print(f"ERROR: {message}", flush=True)
    _atomic_write_status()


def _complete(**extra):
    _state.update(extra)
    _state["status"] = "completed"
    _state["progress"] = 100
    _state["error"] = None
    _state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _atomic_write_status()
    print(f"PROGRESS:100% STEP:{_state.get('step') or '✅ Complete'}", flush=True)


# ── main ───────────────────────────────────────────────────────

def main():
    import argparse

    p = argparse.ArgumentParser(description="VideoFactory longform clipper worker")
    p.add_argument("--job", required=True, choices=["analyze", "render"])
    p.add_argument("--payload", required=True, help="Path to payload JSON")
    args = p.parse_args()

    try:
        payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: failed to load payload: {e}", flush=True)
        sys.exit(1)

    _init_status(args.job, payload)

    source = payload.get("source") or "auto"
    model = payload.get("model", "base")
    language = payload.get("language", "auto")
    min_dur = float(payload.get("min_dur", 20))
    max_dur = float(payload.get("max_dur", 50))

    try:
        from src.video.longform_clipper import (
            analyze_video,
            render_selected_clips,
        )

        # ── shared phase: analysis (cached transcript reused) ──
        if args.job == "analyze":
            analysis_cb = emit
        else:
            analysis_cb = scale(2, 45)

        analysis = analyze_video(
            source,
            model=model,
            language=language,
            min_dur=min_dur,
            max_dur=max_dur,
            use_cache=True,
            progress_cb=analysis_cb,
        )

        cands = analysis.get("candidates") or []
        meta = {
            "source": analysis["source"],
            "language": analysis.get("language", language),
            "duration": analysis.get("duration"),
            "word_count": len(analysis.get("words") or []),
            "transcript_path": analysis.get("transcript_path", ""),
            "candidates": cands,
        }

        if args.job == "analyze":
            _complete(**meta)
            print(f"SUCCESS: analyzed {analysis['source']} "
                  f"→ {len(cands)} candidates", flush=True)
            return

        # ── render phase ──
        emit(46, f"{len(cands)} candidates ready — rendering clips...")
        outputs = render_selected_clips(
            analysis,
            selected=payload.get("selected") or None,
            count=int(payload.get("count", 3)),
            crop_position=payload.get("crop", "center"),
            words_per_line=int(payload.get("words_per_line", 4)),
            mood=payload.get("mood", "peaceful"),
            niche=payload.get("niche", "gospel"),
            language=analysis.get("language", "swahili"),
            progress_cb=scale(46, 99),
        )
        _complete(**meta, outputs=outputs)
        print(f"SUCCESS: rendered {len(outputs)} clip(s)", flush=True)

    except Exception as e:
        traceback.print_exc()
        _fail(f"{type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
