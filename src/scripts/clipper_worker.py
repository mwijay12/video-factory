# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY - LONGFORM CLIPPER WORKER
# Runs analysis (Whisper transcription + highlight scoring) or
# rendering of selected clips in a separate process so the web
# dashboard stays responsive.
# ================================================================

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

DEFAULT_STATUS_PATH = BASE_DIR / "output" / "temp" / "clipper_status.json"


def write_status(status_path, state):
    status_path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    temp_path = status_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp_path, status_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", choices=["analyze", "render"], required=True)
    parser.add_argument("--payload", required=True)
    args = parser.parse_args()

    payload_path = Path(args.payload)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    status_path = Path(payload.get("status_path") or DEFAULT_STATUS_PATH)
    log_path = payload.get("log_path")

    state = {
        "job": args.job,
        "status": "running",
        "progress": 2,
        "stage": "Starting...",
        "result": None,
        "error": None,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": "",
    }

    def log(message):
        try:
            print(message, flush=True)
        except Exception:
            print(str(message).encode("ascii", "replace").decode("ascii"), flush=True)
        if log_path:
            try:
                with open(log_path, "a", encoding="utf-8") as handle:
                    handle.write(str(message) + "\n")
            except Exception:
                pass

    def progress(pct, stage=""):
        state["progress"] = int(pct)
        if stage:
            state["stage"] = stage
        write_status(status_path, state)
        log(f"PROGRESS:{int(pct)}% STEP:{stage}")

    write_status(status_path, state)

    try:
        if args.job == "analyze":
            from src.video.longform_clipper import analyze_video

            progress(5, "Starting analysis...")
            result = analyze_video(
                video_path=payload.get("video_path"),
                language=payload.get("language"),
                model_size=payload.get("model_size", "base"),
                min_duration=float(payload.get("min_duration", 20)),
                max_duration=float(payload.get("max_duration", 60)),
                count=int(payload.get("count", 5)),
                words_per_line=int(payload.get("words_per_line", 4)),
                progress=progress,
                log=log,
            )
            state["result"] = result
            state["status"] = "done"
            state["progress"] = 100
            state["stage"] = f"Found {len(result.get('candidates', []))} clips"
        else:
            from src.video.longform_clipper import render_selected_clips

            clips = payload.get("clips") or []
            if not clips:
                raise ValueError("No clips selected for rendering.")

            progress(5, f"Preparing to render {len(clips)} clip(s)...")
            result = render_selected_clips(
                video_path=payload.get("video_path"),
                clips=clips,
                aspect_ratio=payload.get("aspect_ratio", "9:16"),
                crop_position=payload.get("crop_position", "center"),
                mood=payload.get("mood", "cinematic"),
                niche=payload.get("niche", "gospel"),
                language=payload.get("language", "english"),
                progress=progress,
                log=log,
            )
            state["result"] = result
            state["status"] = "done"
            state["progress"] = 100
            state["stage"] = f"Rendered {len(result.get('clips', []))} clip(s)"

        log(f"SUCCESS: {state['stage']}")
    except Exception as exc:
        state["status"] = "failed"
        state["error"] = str(exc)
        state["stage"] = "Failed"
        log(f"ERROR: {exc}")
        log(traceback.format_exc())
        write_status(status_path, state)
        sys.exit(1)
    finally:
        write_status(status_path, state)
        try:
            payload_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
