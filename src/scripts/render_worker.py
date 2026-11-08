# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except:
        pass

import json
import asyncio
import time
from pathlib import Path

# Set PYTHONPATH to project root
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import OUTPUT_DIR
from src.audio.tts_engine import TTSEngine
from src.utils.media_manager import MediaManager
from src.video.video_engine import ReelVideoEngine


def log(msg, log_file=None):
    """Write a log line to stdout and optionally append it to the log file."""
    try:
        print(msg, flush=True)
    except Exception:
        try:
            print(msg.encode("ascii", "replace").decode("ascii"), flush=True)
        except Exception:
            pass
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            pass


def progress(pct: int, step: str = "", log_file=None):
    """Emit a structured PROGRESS:N% marker so the server can parse exact status.
    Optionally includes a human-readable STEP label.
    """
    step_suffix = f" STEP:{step}" if step else ""
    log(f"PROGRESS:{pct}%{step_suffix}", log_file)


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--payload":
        print("Usage: python render_worker.py --payload <json_path> [log_file_path]")
        sys.exit(1)

    payload_path = Path(sys.argv[2])
    log_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Clear log file if it exists
    if log_file:
        try:
            Path(log_file).write_text("Starting rendering subprocess...\n", encoding="utf-8")
        except:
            pass

    if not payload_path.exists():
        log(f"ERROR: Payload file not found: {payload_path}", log_file)
        sys.exit(1)

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"ERROR: Failed to parse payload: {e}", log_file)
        sys.exit(1)

    try:
        script = payload.get("script", {})
        niche = payload.get("niche", "gospel")
        mood = payload.get("mood", "peaceful")
        music_path = payload.get("music_path", None)
        output_name = payload.get("output_name", "")
        webhook_url = payload.get("webhook_url", None)

        progress(5, "🚀 Worker started", log_file)

        if music_path == "auto_smart":
            try:
                from src.utils.media_manager import get_smart_music
                music_path = get_smart_music(niche=niche)
                log(f"Auto-selected smart music: {music_path}", log_file)
            except Exception as e:
                log(f"Warning: Failed to auto-select music: {e}", log_file)
                music_path = None

        progress(10, "📝 Script parsed", log_file)
        music_only = payload.get("music_only", False)
        if music_only:
            log("Music-Only Mode active. Skipping voice generation...", log_file)
            tts_result = {"audio_path": None, "subtitles": []}
            progress(40, "✅ Skipped voice generation (Music-Only Mode)", log_file)
        else:
            log("Generating voice narration...", log_file)
            try:
                lines = []
                if script.get("hook"):
                    lines.append(script["hook"])
                body = script.get("body", [])
                if isinstance(body, list):
                    lines.extend(body)
                elif isinstance(body, str):
                    lines.append(body)
                if script.get("cta"):
                    lines.append(script["cta"])

                import config.settings
                import importlib
                importlib.reload(config.settings)

                global_active_voice = getattr(config.settings, "ACTIVE_VOICE", "")
                global_provider = getattr(config.settings, "TTS_PROVIDER", "direct-gemini")

                voice = script.get("voice")
                if global_provider in ["direct-gemini", "puter", "elevenlabs"] or (global_active_voice and any(global_active_voice.startswith(p) for p in ["direct-gemini:", "puter:", "elevenlabs:"])):
                    voice = global_active_voice or "direct-gemini:Aoede"
                elif not voice:
                    voice = global_active_voice or "direct-gemini:Aoede"

                rate = script.get("rate") or "+0%"
                engine = TTSEngine(voice=voice, rate=rate)

                progress(15, "🎙 Generating voice narration...", log_file)
                log("Creating sync voice audio...", log_file)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tts_result = loop.run_until_complete(engine.generate_per_line_synced(lines, prefix=f"web_{niche}"))

                if not tts_result:
                    log("ERROR: Voice generation failed.", log_file)
                    sys.exit(1)

                progress(40, "✅ Voice narrated and synced", log_file)
                log(f"Voice generated: {Path(tts_result['audio_path']).name}", log_file)
            except Exception as e:
                log(f"ERROR: Exception occurred during voice generation: {str(e)}", log_file)
                sys.exit(1)


        progress(50, "🎬 Loading background media assets...", log_file)
        log("Loading background media assets...", log_file)

        safe_niche = niche if niche != 'bedtime_prayer' else 'prayer'
        manager = MediaManager(niche=safe_niche)
        manager.scan()

        media_items = []
        if manager.has_media():
            subs_len = len(tts_result["subtitles"]) if tts_result and "subtitles" in tts_result else 10
            needed_clips = max(35, subs_len * 3)
            media_items = manager.pick_media_for_reel(count=needed_clips, script=script)
            log(f"Loaded {len(media_items)} 100% UNIQUE media items for timeline (Anti-repetition zero clip reuse active).", log_file)
        else:
            log("No local media found. Using gradient fallback.", log_file)

        progress(60, "🗂 Media assets ready", log_file)

        progress(70, "🎞 Rendering video layers...", log_file)
        log("Compiling video layers (Word-by-word Karaoke, safety padding, & dynamic audio ducking active)...", log_file)

        aspect_ratio = payload.get("aspect_ratio", "9:16")
        caption_style = payload.get("caption_style", "typing")
        transition_style = payload.get("transition_style", "whip_zoom")
        video_engine = ReelVideoEngine(mood=mood, aspect_ratio=aspect_ratio, caption_style=caption_style, transition_style=transition_style)

        # Intercept final encode phase via a wrapper hook on build_reel output
        out_path = video_engine.build_reel(
            media_items=media_items,
            audio_path=tts_result["audio_path"],
            subtitles=tts_result["subtitles"],
            output_name=output_name,
            hook_text=script.get("hook", ""),
            music_path=music_path,
            show_progress_bar=True,
            log_callback=lambda m: log(m, log_file)
        )

        log(f"SUCCESS: Rendered reel: {Path(out_path).name}", log_file)
        progress(100, f"✅ Done! → {Path(out_path).name}", log_file)

        if webhook_url:
            import httpx
            try:
                res = httpx.post(webhook_url, json={"status": "success", "file_path": out_path}, timeout=10.0)
                log(f"Webhook triggered: {webhook_url} (status: {res.status_code})", log_file)
            except Exception as e:
                log(f"Webhook failed: {e}", log_file)

        # Clean up temp payload
        try:
            payload_path.unlink()
        except:
            pass

    except Exception as e:
        log(f"ERROR: Exception occurred during render: {str(e)}", log_file)
        if webhook_url:
            import httpx
            try:
                httpx.post(webhook_url, json={"status": "error", "error": str(e)}, timeout=10.0)
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
