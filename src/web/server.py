# -*- coding: utf-8 -*-
import os
import re
import sys
import asyncio
import threading
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Set Working Directory and PYTHONPATH to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
os.chdir(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

import importlib
import config.settings
from config.settings import (
    OUTPUT_DIR,
    NICHE_CONFIG,
    ACTIVE_VOICE,
    VOICE_OPTIONS,
    STOCK_PATHS,
    ASSETS_DIR,
    TTS_PROVIDER,
    PUTER_TOKEN,
)

app = FastAPI(title="VideoFactory API", version="2.0")

# CORS Middleware (dashboard is local-only; wildcard + credentials is invalid)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories to ensure mounting succeeds
os.makedirs("assets/music", exist_ok=True)
os.makedirs("assets/songs", exist_ok=True)
os.makedirs("assets/hooks", exist_ok=True)
os.makedirs("assets/stock", exist_ok=True)
videos_dir = Path(OUTPUT_DIR) / "videos"
videos_dir.mkdir(parents=True, exist_ok=True)
temp_dir = Path(OUTPUT_DIR) / "temp"
temp_dir.mkdir(parents=True, exist_ok=True)

app.mount("/assets/music", StaticFiles(directory="assets/music"), name="music")
app.mount("/assets/songs", StaticFiles(directory="assets/songs"), name="songs")
app.mount("/assets/hooks", StaticFiles(directory="assets/hooks"), name="hooks")
app.mount("/assets/stock", StaticFiles(directory="assets/stock"), name="stock")
app.mount("/output/videos", StaticFiles(directory=str(videos_dir)), name="output_videos")
app.mount("/output/temp", StaticFiles(directory=str(temp_dir)), name="output_temp")
app.mount("/css", StaticFiles(directory="src/web/css"), name="css")
app.mount("/js", StaticFiles(directory="src/web/js"), name="js")

# Voice preview files
os.makedirs("output/previews", exist_ok=True)
app.mount("/output/previews", StaticFiles(directory="output/previews"), name="previews")

# Process tracking globals
render_process = None
current_render_log_path = None
current_render_output_name = None

# Longform clipper (sermons/podcasts → vertical shorts) job tracking
CLIPPER_STATUS_PATH = Path(OUTPUT_DIR) / "temp" / "clipper_status.json"
CLIPPER_SOURCE_DIR = Path(ASSETS_DIR) / "longform"
CLIPPER_SOURCE_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
clipper_process = None
current_clipper_log_path = None
current_clipper_job = None

pipeline_process = None
current_pipeline_log_path = None

# API Config
@app.get("/api/config")
def get_config():
    niches = list(NICHE_CONFIG.keys())
    
    # Reload config to get latest values
    importlib.reload(config.settings)
    provider = getattr(config.settings, "TTS_PROVIDER", "edge-tts")
    active_voice = getattr(config.settings, "ACTIVE_VOICE", "")
    
    if provider == "elevenlabs":
        voices = {
            "english": [
                "Rachel (21m00Tcm4TlvDq8ikWAM)",
                "Drew (29vD33N1CtxCmqQRPOHJ)",
                "Clyde (2EyyOtef2nt0zpT5pUt5)",
                "Adam (pNInz6obpgqjVWtJ45dB)",
                "Nicole (piTKgcLEGmPEe3aY1Z85)",
                "Bella (EXAVITQu4vr4xnSDxMaL)",
                "Dom (AZnzlk1XhkjRsfKJHSS0)"
            ],
            "swahili": [
                "Swahili Female (Bella - EXAVITQu4vr4xnSDxMaL)",
                "Swahili Male (Adam - pNInz6obpgqjVWtJ45dB)"
            ]
        }
    elif provider == "puter":
        puter_voices = []
        # aws-polly
        for v in ["Joanna", "Matthew", "Ivy", "Justin", "Kendra", "Kimberly", "Salli", "Joey", "Ruth"]:
            puter_voices.append(f"puter:aws-polly:{v}")
        # openai
        for v in ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]:
            puter_voices.append(f"puter:openai:{v}")
        # elevenlabs
        for v in ["21m00Tcm4TlvDq8ikWAM", "AZnzlk1XvdvUeBnXmlld", "EXAVITQu4vr3xnSDxMaL", "ODq5zmih8GrVes37Dizd", "N2lVS1w4EtoT3dr4eOWO"]:
            puter_voices.append(f"puter:elevenlabs:{v}")
        # gemini
        for v in ["Kore", "Zephyr", "Puck", "Charon", "Fenrir", "Leda", "Aoede", "Enceladus"]:
            puter_voices.append(f"puter:gemini:{v}")
        # xai
        for v in ["eve", "ara", "rex", "sal", "leo"]:
            puter_voices.append(f"puter:xai:{v}")
            
        voices = {
            "english": puter_voices,
            "swahili": puter_voices
        }
    else:
        voices = {
            lang: list(opts.values())
            for lang, opts in VOICE_OPTIONS.items()
        }
        
    moods = ["peaceful", "powerful", "hopeful", "emotional", "holy", "cinematic", "whisper", "default"]
    
    return {
        "niches": niches,
        "voices": voices,
        "moods": moods,
        "default_voice": active_voice or ACTIVE_VOICE,
    }

# ============================================================
# TRENDS & SETTINGS ENDPOINTS
# ============================================================

from src.scripts.trending_topics import TrendCollector, trend_to_spiritual_script

@app.get("/api/trends/list")
async def list_trends(refresh: bool = False):
    collector = TrendCollector()
    if refresh:
        try:
            trends = await collector.collect_all_trends()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")
    else:
        trends = collector.get_cached_trends()
        if not trends:
            try:
                trends = await collector.collect_all_trends()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")
    return {"trends": trends}

@app.post("/api/trends/generate-script")
async def generate_trend_script(payload: Dict):
    trend = payload.get("trend")
    niche = payload.get("niche", "gospel")
    language = payload.get("language", "english")
    
    if not trend or not trend.get("title"):
        raise HTTPException(status_code=400, detail="Trend details with title are required")
        
    try:
        script = await trend_to_spiritual_script(trend, niche=niche, language=language)
        if not script:
            raise HTTPException(status_code=500, detail="Failed to generate spiritual script from trend")
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating script: {str(e)}")

def update_settings_on_disk(settings_data: dict, env_data: dict):
    # Update config/settings.py
    settings_file = Path("config/settings.py")
    if settings_file.exists():
        content = settings_file.read_text(encoding="utf-8")
        import re
        for key, val in settings_data.items():
            pattern = rf'^{key}\s*=\s*.*$'
            if isinstance(val, str):
                # Clean windows backslashes in paths/files to use forward slashes
                if any(x in key.lower() for x in ["path", "dir", "folder", "file"]):
                    val = val.replace("\\", "/")
                # Escape backslashes and double quotes for Python string literal syntax
                escaped_val = val.replace("\\", "\\\\").replace('"', '\\"')
                replacement = f'{key} = "{escaped_val}"'
            elif isinstance(val, bool):
                replacement = f'{key} = {val}'
            elif isinstance(val, (int, float)):
                replacement = f'{key} = {val}'
            else:
                continue
            
            content, count = re.subn(pattern, lambda m, rep=replacement: rep, content, flags=re.MULTILINE)
            if count == 0:
                pass
        settings_file.write_text(content, encoding="utf-8")
        
    # Update .env
    env_file = Path(".env")
    env_content = ""
    if env_file.exists():
        env_content = env_file.read_text(encoding="utf-8")
        
    lines = env_content.splitlines()
    updated_keys = set()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            k, v = stripped.split("=", 1)
            k = k.strip()
            if k in env_data:
                lines[idx] = f"{k}={env_data[k]}"
                updated_keys.add(k)
                
    for k, v in env_data.items():
        if k not in updated_keys:
            lines.append(f"{k}={v}")
            
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

@app.get("/api/settings")
def get_settings():
    # Reload config to get latest values
    importlib.reload(config.settings)
    
    # Read environment variables
    env_keys = [
        "OPENAI_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
        "PEXELS_API_KEY", "PIXABAY_API_KEY", "ELEVENLABS_API_KEY",
        "YOUTUBE_API_KEY",
        "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
        # Trending / News API keys
        "NEWSAPI_KEY", "GUARDIAN_KEY", "GNEWS_KEY",
        "PUTER_TOKEN"
    ]
    env_data = {key: config.settings.ENV.get(key, "") for key in env_keys}
    
    return {
        "MODE": getattr(config.settings, "MODE", "data_saver"),
        "CONTENT_MODE": getattr(config.settings, "CONTENT_MODE", "reels"),
        "NICHE": getattr(config.settings, "NICHE", "gospel"),
        "LANGUAGE": getattr(config.settings, "LANGUAGE", "english"),
        "ACTIVE_VOICE": getattr(config.settings, "ACTIVE_VOICE", ""),
        "TTS_RATE": getattr(config.settings, "TTS_RATE", "+0%"),
        "TTS_VOLUME": getattr(config.settings, "TTS_VOLUME", "+0%"),
        "TTS_PITCH": getattr(config.settings, "TTS_PITCH", "+0Hz"),
        "TTS_PROVIDER": getattr(config.settings, "TTS_PROVIDER", "edge-tts"),
        "BACKGROUND_MUSIC_VOLUME": getattr(config.settings, "BACKGROUND_MUSIC_VOLUME", 0.35),
        "BACKGROUND_MUSIC_ENABLED": getattr(config.settings, "BACKGROUND_MUSIC_ENABLED", True),
        "HOOK_AUDIO_ENABLED": getattr(config.settings, "HOOK_AUDIO_ENABLED", False),
        "HOOK_AUDIO_VOLUME": getattr(config.settings, "HOOK_AUDIO_VOLUME", 0.25),
        "AUDIO_NORMALIZE_ENABLED": getattr(config.settings, "AUDIO_NORMALIZE_ENABLED", False),
        "SUBTITLES_ENABLED": getattr(config.settings, "SUBTITLES_ENABLED", False),
        "SUBTITLE_ANIMATION_STYLE": getattr(config.settings, "SUBTITLE_ANIMATION_STYLE", "whisper"),
        "SUBTITLE_FONT_SIZE": getattr(config.settings, "SUBTITLE_FONT_SIZE", 56),
        "SUBTITLE_COLOR": getattr(config.settings, "SUBTITLE_COLOR", "white"),
        "SUBTITLE_STROKE_COLOR": getattr(config.settings, "SUBTITLE_STROKE_COLOR", "black"),
        "SUBTITLE_STROKE_WIDTH": getattr(config.settings, "SUBTITLE_STROKE_WIDTH", 3),
        "SUBTITLE_POSITION_Y": getattr(config.settings, "SUBTITLE_POSITION_Y", 0.68),
        "SUBTITLE_MAX_WORDS_PER_LINE": getattr(config.settings, "SUBTITLE_MAX_WORDS_PER_LINE", 5),
        "SUBTITLE_KARAOKE": getattr(config.settings, "SUBTITLE_KARAOKE", True),
        "SUBTITLE_FONT_PATH": getattr(config.settings, "SUBTITLE_FONT_PATH", ""),
        "SUBTITLE_BG_OPACITY": getattr(config.settings, "SUBTITLE_BG_OPACITY", 148),
        "VIDEO_QUALITY_PRESET": getattr(config.settings, "VIDEO_QUALITY_PRESET", "standard"),
        "WATERMARK_ENABLED": getattr(config.settings, "WATERMARK_ENABLED", False),
        "WATERMARK_PATH": getattr(config.settings, "WATERMARK_PATH", "assets/watermark.png"),
        "WATERMARK_POSITION": ",".join(w_pos) if isinstance(w_pos := getattr(config.settings, "WATERMARK_POSITION", "right,top"), (list, tuple)) else str(w_pos),
        "WATERMARK_OPACITY": getattr(config.settings, "WATERMARK_OPACITY", 0.45),
        "WATERMARK_HEIGHT": getattr(config.settings, "WATERMARK_HEIGHT", 65),
        "WATERMARK_MARGIN": getattr(config.settings, "WATERMARK_MARGIN", 35),
        "api_keys": env_data
    }

@app.post("/api/settings/save")
def save_settings(payload: Dict):
    settings_data = payload.get("settings", {})
    api_keys = payload.get("api_keys", {})
    
    valid_settings = {}
    valid_keys = {}
    
    for k, v in settings_data.items():
        if k in ["MODE", "CONTENT_MODE", "NICHE", "LANGUAGE", "ACTIVE_VOICE", "TTS_RATE", "TTS_VOLUME", "TTS_PITCH", "TTS_PROVIDER",
                 "SUBTITLE_COLOR", "SUBTITLE_STROKE_COLOR", "SUBTITLE_FONT_PATH", "SUBTITLE_ANIMATION_STYLE",
                 "VIDEO_QUALITY_PRESET", "WATERMARK_PATH", "WATERMARK_POSITION"]:
            valid_settings[k] = str(v)
        elif k in ["BACKGROUND_MUSIC_VOLUME", "HOOK_AUDIO_VOLUME", "SUBTITLE_POSITION_Y", "WATERMARK_OPACITY"]:
            try:
                valid_settings[k] = float(v)
            except:
                pass
        elif k in ["BACKGROUND_MUSIC_ENABLED", "HOOK_AUDIO_ENABLED", "AUDIO_NORMALIZE_ENABLED", "SUBTITLES_ENABLED", "SUBTITLE_KARAOKE", "WATERMARK_ENABLED"]:
            valid_settings[k] = bool(v)
        elif k in ["SUBTITLE_FONT_SIZE", "SUBTITLE_STROKE_WIDTH", "SUBTITLE_MAX_WORDS_PER_LINE", "SUBTITLE_BG_OPACITY",
                   "WATERMARK_HEIGHT", "WATERMARK_MARGIN"]:
            try:
                valid_settings[k] = int(v)
            except:
                pass
            
    for k, v in api_keys.items():
        if k in ["OPENAI_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                 "PEXELS_API_KEY", "PIXABAY_API_KEY", "ELEVENLABS_API_KEY",
                 "YOUTUBE_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
                 "NEWSAPI_KEY", "GUARDIAN_KEY", "GNEWS_KEY", "PUTER_TOKEN"]:
            valid_keys[k] = str(v).strip()
            
    try:
        update_settings_on_disk(valid_settings, valid_keys)
        
        # Reload settings module so changes are updated in memory
        importlib.reload(config.settings)
        
        # Also update os.environ and config.settings.ENV in memory
        for k, v in valid_keys.items():
            os.environ[k] = v
            config.settings.ENV[k] = v
            if hasattr(config.settings, k):
                setattr(config.settings, k, v)
                
        # Force reload values in settings
        for k, v in valid_settings.items():
            setattr(config.settings, k, v)
            
        # Update module level globals in server.py
        globals()['ACTIVE_VOICE'] = getattr(config.settings, 'ACTIVE_VOICE', ACTIVE_VOICE)
        globals()['TTS_PROVIDER'] = getattr(config.settings, 'TTS_PROVIDER', 'edge-tts')
        globals()['PUTER_TOKEN'] = getattr(config.settings, 'PUTER_TOKEN', '')
        globals()['OUTPUT_DIR'] = getattr(config.settings, 'OUTPUT_DIR', OUTPUT_DIR)
        globals()['NICHE_CONFIG'] = getattr(config.settings, 'NICHE_CONFIG', NICHE_CONFIG)
        globals()['VOICE_OPTIONS'] = getattr(config.settings, 'VOICE_OPTIONS', VOICE_OPTIONS)
        globals()['STOCK_PATHS'] = getattr(config.settings, 'STOCK_PATHS', STOCK_PATHS)
        globals()['ASSETS_DIR'] = getattr(config.settings, 'ASSETS_DIR', ASSETS_DIR)
        
        return {"message": "Settings saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")

# List background songs
@app.get("/api/songs/list")
def list_songs():
    songs = []
    seen_paths = set()
    audio_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]

    # 1. Scan assets/songs
    songs_base = Path("assets/songs")
    if songs_base.exists():
        for child in sorted(songs_base.rglob("*")):
            if child.is_file() and child.suffix.lower() in audio_extensions:
                norm = str(child.resolve())
                if norm not in seen_paths:
                    seen_paths.add(norm)
                    rel_path = child.relative_to(songs_base)
                    category = rel_path.parent.name or "songs"
                    songs.append({
                        "name": child.name,
                        "category": f"songs/{category}" if category != "songs" else "songs",
                        "path": str(child),
                        "url": f"/assets/songs/{rel_path.as_posix()}"
                    })

    # 2. Scan assets/music
    music_base = Path("assets/music")
    if music_base.exists():
        for child in sorted(music_base.rglob("*")):
            if child.is_file() and child.suffix.lower() in audio_extensions:
                norm = str(child.resolve())
                if norm not in seen_paths:
                    seen_paths.add(norm)
                    rel_path = child.relative_to(music_base)
                    category = rel_path.parent.name or "music"
                    songs.append({
                        "name": child.name,
                        "category": f"music/{category}" if category != "music" else "music",
                        "path": str(child),
                        "url": f"/assets/music/{rel_path.as_posix()}"
                    })

    return {"songs": songs}

# Upload custom background music
@app.post("/api/songs/upload")
async def upload_custom_song(file: UploadFile = File(...)):
    music_dir = Path("assets/music/custom")
    music_dir.mkdir(parents=True, exist_ok=True)
    
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".mp3", ".wav", ".m4a"]:
        raise HTTPException(status_code=400, detail="Only MP3, WAV or M4A audio files are supported.")
        
    dest_path = music_dir / file.filename
    try:
        content = await file.read()
        dest_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio file: {str(e)}")
        
    return {
        "message": f"Successfully uploaded {file.filename}",
        "song": {
            "name": file.filename,
            "category": "custom",
            "path": str(dest_path),
            "url": f"/assets/music/custom/{file.filename}"
        }
    }


# Get files in stock directories
@app.get("/api/media/list")
def list_media():
    stock_base = Path("assets/stock")
    if not stock_base.exists():
        return {"folders": {}}
    
    folders = {}
    
    # Scrape pinterest stock subdirectories
    pin_base = stock_base / "pinterest"
    if pin_base.exists():
        folders["pinterest"] = [f.name for f in pin_base.iterdir() if f.is_dir()]
        
        # Add character folders
        char_base = pin_base / "characters"
        if char_base.exists():
            folders["characters"] = [f.name for f in char_base.iterdir() if f.is_dir()]
            
    # Add other main folders
    for f in stock_base.iterdir():
        if f.is_dir() and f.name != "pinterest":
            folders[f.name] = []
            
    return {"folders": folders}

# Get files inside a specific stock folder
@app.get("/api/media/files")
def get_media_files(folder: str):
    stock_base = Path("assets/stock")
    
    try:
        clean_folder = Path(folder.strip("/\\")).as_posix()
        target_dir = (stock_base / clean_folder).resolve()
        resolved_base = stock_base.resolve()
        # Verify the path is inside the stock base directory using relative_to, which handles Windows path casing/drive letter comparison automatically.
        target_dir.relative_to(resolved_base)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid folder path: Not inside stock directory")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid folder path: {str(e)}")
        
    if not target_dir.exists() or not target_dir.is_dir():
        return {"files": []}
        
    files = []
    video_exts = [".mp4", ".mov", ".mkv", ".webm"]
    image_exts = [".jpg", ".jpeg", ".png", ".webp"]
    
    for child in sorted(target_dir.iterdir()):
        if child.is_file():
            suffix = child.suffix.lower()
            try:
                rel_path = child.relative_to(stock_base)
                media_url = f"/assets/stock/{rel_path.as_posix()}"
                
                if suffix in video_exts:
                    files.append({
                        "name": child.name,
                        "type": "video",
                        "url": media_url
                    })
                elif suffix in image_exts:
                    files.append({
                        "name": child.name,
                        "type": "image",
                        "url": media_url
                    })
            except Exception:
                pass
    return {"files": files}

# List template/historical scripts
@app.get("/api/scripts/list")
def list_scripts():
    from src.scripts.gospel_script import ScriptManager
    scripts = []
    for niche in ['gospel', 'prayer', 'praise', 'motivational', 'swahili']:
        try:
            mgr = ScriptManager(niche=niche, language='english')
            all_s = mgr.get_all_scripts()
            for s in all_s:
                scripts.append({
                    "niche": niche,
                    "id": s.get("id", "script"),
                    "title": s.get("title", ""),
                    "hook": s.get("hook", ""),
                    "body": s.get("body", []),
                    "cta": s.get("cta", "")
                })
        except:
            pass
    return {"scripts": scripts}

# Generate script via AI
@app.post("/api/script/generate")
async def generate_script(payload: Dict):
    import asyncio
    from src.scripts.ai_generator import AIScriptGenerator
    niche = payload.get("niche", "gospel")
    language = payload.get("language", "english")
    topic = payload.get("topic", None)
    viral = payload.get("viral", False)
    series = payload.get("series", None)
    
    script = None
    try:
        gen = AIScriptGenerator()
        script = await asyncio.wait_for(
            gen.generate(
                niche=niche,
                topic=topic,
                language=language,
                use_viral_hook=viral,
                series=series
            ),
            timeout=30.0
        )
    except Exception as e:
        print(f"AI generator timeout/notice ({e}), using instant local template...")

    if not script:
        try:
            if language == "swahili":
                from src.scripts.swahili_script import SwahiliScriptManager
                mgr = SwahiliScriptManager(niche=niche if niche in ["swahili", "swahili_motivational", "swahili_life"] else "swahili")
                script = mgr.get_random_script()
            else:
                from src.scripts.gospel_script import ScriptManager
                mgr = ScriptManager(niche=niche if niche in ['gospel','prayer','motivational'] else 'gospel', language=language)
                script = mgr.get_random_script()
        except Exception as ex:
            print(f"Local fallback template failed: {ex}")

    if not script:
        raise HTTPException(status_code=500, detail="Script generation failed. Check internet connection or API keys.")
    
    return script

# Organize external raw script (ChatGPT / Claude / Paste) for TTS & B-Roll
@app.post("/api/script/organize_external")
async def organize_external_script(payload: Dict):
    raw_text = payload.get("raw_text", "")
    language = payload.get("language", "swahili")
    niche = payload.get("niche", "gospel")

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text is required")

    import re, time
    # 1. Clean markdown noise: *, #, Markdown headers, stage notes in []
    clean = re.sub(r'[*#_`]', '', raw_text)
    clean = re.sub(r'\[.*?\]', '', clean) # remove [Narrator:], [Music], etc.
    clean = re.sub(r'^\s*(Hook|Body|CTA|Line\s*\d+|Mstari\s*\d+)\s*:\s*', '', clean, flags=re.IGNORECASE | re.MULTILINE)
    
    # Split into lines
    raw_lines = [l.strip() for l in clean.splitlines() if l.strip()]
    if not raw_lines:
        raise HTTPException(status_code=400, detail="No readable text found after cleaning")

    # Hook is line 1, CTA is last line, body lines are middle
    hook = raw_lines[0]
    cta = raw_lines[-1] if len(raw_lines) > 1 else "Andika AMINA kama ulihitaji ujumbe huu"
    body = raw_lines[1:-1] if len(raw_lines) > 2 else (raw_lines[1:] if len(raw_lines) == 2 else [hook])

    # Ensure every body line has (visual search terms in English) in parentheses at the end
    processed_body = []
    broll_keywords = [
        "(nature scenery, divine light)",
        "(gospel worship, praying hands)",
        "(peaceful ocean, warm sunset)",
        "(ancient bible, open scriptures)",
        "(hopeful sunrise, majestic mountains)",
        "(peaceful clouds, sky scenery)"
    ]

    for idx, line in enumerate(body):
        # Check if line already has (visual keywords) at end
        if re.search(r'\([a-zA-Z0-9\s,]+\)$', line):
            processed_body.append(line)
        else:
            kw = broll_keywords[idx % len(broll_keywords)]
            processed_body.append(f"{line} {kw}")

    # Generate a clean title
    title = f"Custom {niche.capitalize()} ({language.capitalize()})"
    if len(hook) > 5:
        title = hook[:40].strip() + "..."

    return {
        "id": f"external_{int(time.time())}",
        "niche": niche,
        "language": language,
        "title": title,
        "hook": hook,
        "body": processed_body,
        "cta": cta,
        "source": "External Paste (Auto-Organized)"
    }

# TTS Line Preview
@app.get("/api/tts/preview")
async def tts_preview(
    text: str,
    voice: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    puter_engine: str = "",
    puter_model: str = "",
    puter_format: str = "",
    puter_instructions: str = "",
):
    from src.audio.tts_engine import TTSEngine
    engine = TTSEngine(voice=voice, rate=rate, pitch=pitch, volume=volume)
    
    temp_dir = Path(OUTPUT_DIR) / "audio" / "_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / "preview_web.mp3"
    
    if temp_file.exists():
        try: temp_file.unlink()
        except: pass
    
    extra_kwargs = {}
    if voice.startswith("puter:"):
        if puter_engine:
            extra_kwargs["engine"] = puter_engine
        if puter_model:
            extra_kwargs["model"] = puter_model
        if puter_format:
            extra_kwargs["output_format"] = puter_format
        if puter_instructions:
            extra_kwargs["instructions"] = puter_instructions
        
    await engine.generate_voice(text, output_name="_temp/preview_web.mp3", **extra_kwargs)
    
    if not temp_file.exists():
        raise HTTPException(status_code=500, detail="Failed to generate TTS preview")
        
    return FileResponse(str(temp_file))

# Trigger background Stock Downloads
@app.post("/api/download")
def download_media(payload: Dict, background_tasks: BackgroundTasks):
    from src.utils.media_downloader import run_pinterest_download, run_pexels_download
    
    source = payload.get("source", "")
    folder = payload.get("folder", "")
    limit = int(payload.get("limit", 5))
    media_type = payload.get("media_type", "video") # video or photo
    engine_type = payload.get("engine", "pinterest") # pinterest or pexels
    
    if not source:
        raise HTTPException(status_code=400, detail="Source/Query is required")
        
    def do_download():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if engine_type == "pinterest":
                print(f"Downloading Pinterest board: {source} into {folder}")
                loop.run_until_complete(run_pinterest_download(source, limit=limit, folder=folder))
            else:
                print(f"Downloading Pexels Stock: {source} into {folder} ({media_type})")
                loop.run_until_complete(run_pexels_download(source, limit=limit, media_type=media_type, folder=folder))
        except Exception as e:
            print(f"Download thread failed: {e}")
            
    background_tasks.add_task(do_download)
    return {"message": "Download started in the background"}

# POST Render video
@app.post("/api/render")
def render_video(payload: Dict):
    global render_process, current_render_log_path, current_render_output_name
    
    if render_process is not None:
        status = get_render_status()
        if status["status"] == "rendering":
            raise HTTPException(status_code=400, detail="A rendering job is already running")
            
    script = payload.get("script", {})
    niche = payload.get("niche", "gospel")
    mood = payload.get("mood", "peaceful")
    language = payload.get("language", "english")
    music_path = payload.get("music_path", None)
    webhook_url = payload.get("webhook_url", None)
    music_only = payload.get("music_only", False)
    aspect_ratio = payload.get("aspect_ratio", "9:16")
    caption_style = payload.get("caption_style", "typing")
    transition_style = payload.get("transition_style", "whip_zoom")
    pitch_shift = float(payload.get("pitch_shift", 1.5))
    eq_preset = payload.get("eq_preset", "warm_studio")
    
    import time, re
    stamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Generate human-readable descriptive name from hook, topic, or script body
    hook_raw = script.get("hook", "") or script.get("topic", "") or payload.get("topic", "")
    if not hook_raw and script.get("body"):
        first_body = script["body"][0] if isinstance(script["body"], list) else script["body"]
        hook_raw = str(first_body)
        
    clean_words = re.findall(r'[a-zA-Z0-9]+', str(hook_raw))
    slug = "_".join([w.capitalize() for w in clean_words[:4]]) if clean_words else "Video"
    output_name = f"{niche}_{slug}_{stamp}.mp4"
    
    # Ensure temp directory exists
    temp_dir = Path("output/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    payload_path = temp_dir / f"payload_{stamp}.json"
    log_path = temp_dir / f"log_{stamp}.log"
    
    payload_data = {
        "script": script,
        "niche": niche,
        "mood": mood,
        "language": language,
        "music_path": music_path,
        "webhook_url": webhook_url,
        "output_name": output_name,
        "music_only": music_only,
        "aspect_ratio": aspect_ratio,
        "caption_style": caption_style,
        "transition_style": transition_style,
        "pitch_shift": pitch_shift,
        "eq_preset": eq_preset
    }
    
    try:
        payload_path.write_text(json.dumps(payload_data, indent=2, ensure_ascii=False), encoding="utf-8")
        log_path.write_text("Starting rendering subprocess...\n", encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize payload/log files: {str(e)}")
        
    cmd = [
        sys.executable,
        "src/scripts/render_worker.py",
        "--payload",
        str(payload_path),
        str(log_path)
    ]
    
    try:
        import os
        sub_env = os.environ.copy()
        sub_env["PYTHONIOENCODING"] = "utf-8"
        sub_env["PYTHONUNBUFFERED"] = "1"
        
        log_fh = open(str(log_path), "a", encoding="utf-8")
        render_process = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            env=sub_env
        )
        
        current_render_log_path = log_path
        current_render_output_name = output_name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to spawn rendering subprocess: {str(e)}")
        
    return {"message": "Rendering started"}

# Transcribe Audio & Preview Lyrics (Whisper AI)
@app.post("/api/lyrics/transcribe")
async def transcribe_lyrics_audio(payload: Dict):
    song_path = payload.get("song_path")
    language = payload.get("language", "swahili")
    words_per_line = int(payload.get("words_per_line", 4))
    
    if not song_path:
        raise HTTPException(status_code=400, detail="song_path is required")
        
    import urllib.parse
    song_path = urllib.parse.unquote(str(song_path))

    song_clean = str(song_path).lstrip("/\\")
    song_file = Path(song_clean)
    if not song_file.exists():
        song_file = Path(song_path)
    
    if not song_file.exists():
        target_name = song_file.name
        matches = (
            list(Path("assets/music").rglob(target_name)) +
            list(Path("assets/songs").rglob(target_name)) +
            list(Path("assets").rglob(target_name)) +
            list(Path("output").rglob(target_name))
        )
        if matches:
            song_file = matches[0]

    if not song_file.exists():
        raise HTTPException(status_code=404, detail=f"Audio file not found: {song_path}")

    start_time = float(payload.get("start_time", 0.0))
    clip_duration = float(payload.get("clip_duration", 30.0))
    audio_mode = payload.get("audio_mode", "clip")

    # Clip audio to selection window if clip mode
    target_audio = song_file
    temp_clip_file = None
    if audio_mode == "clip" and clip_duration > 0:
        try:
            from moviepy import AudioFileClip
            ac = AudioFileClip(str(song_file))
            duration = ac.duration
            st = min(start_time, max(0, duration - 5.0))
            et = min(st + clip_duration, duration)
            
            temp_dir = Path("output/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_clip_file = temp_dir / f"trim_{song_file.stem}_{int(st)}_{int(et)}.mp3"
            
            sub = ac.subclipped(st, et)
            sub.write_audiofile(str(temp_clip_file), logger=None)
            sub.close()
            ac.close()
            target_audio = temp_clip_file
        except Exception as e:
            print(f"  Warning: Audio trimming before transcription failed: {e}")

    try:
        from src.audio.lyrics_mode import LyricsExtractor
        extractor = LyricsExtractor(model_size='base')
        lyrics_data = extractor.extract_lyrics(str(target_audio), language=language)
        
        # Clean up temp file
        if temp_clip_file and temp_clip_file.exists():
            try: temp_clip_file.unlink()
            except: pass

        if not lyrics_data:
            return {"lyrics_text": "", "subtitles": []}
            
        subtitles = extractor.lyrics_to_subtitles(lyrics_data, group_words_per_line=words_per_line)
        lines = [sub["text"] for sub in subtitles if sub.get("text")]
        lyrics_text = "\n".join(lines)
        return {"lyrics_text": lyrics_text, "subtitles": subtitles}
    except Exception as e:
        if temp_clip_file and temp_clip_file.exists():
            try: temp_clip_file.unlink()
            except: pass
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

# Render Song Lyric Video (Song to Reel)
@app.post("/api/lyrics/render")
async def render_lyrics_video(payload: Dict):
    global render_process, current_render_log_path, current_render_output_name
    
    # Check if currently rendering
    if render_process is not None:
        if render_process.poll() is not None:
            render_process = None
        else:
            status = get_render_status()
            if status["status"] == "rendering":
                raise HTTPException(status_code=400, detail="A rendering job is already running")
            
    song_path = payload.get("song_path")
    if song_path:
        import urllib.parse
        song_path = urllib.parse.unquote(str(song_path))
    mode = payload.get("mode", "whisper")
    custom_lyrics = payload.get("custom_lyrics", "")
    niche = payload.get("niche", "gospel")
    mood = payload.get("mood", "peaceful")
    words_per_line = int(payload.get("words_per_line", 4))
    language = payload.get("language", "english")
    audio_mode = payload.get("audio_mode", "clip")
    start_time = float(payload.get("start_time", 0.0))
    clip_duration = payload.get("clip_duration", 30.0)
    end_time = payload.get("end_time", None)
    aspect_ratio = payload.get("aspect_ratio", "9:16")
    
    if not song_path:
        raise HTTPException(status_code=400, detail="song_path is required")
        
    import time
    stamp = time.strftime("%Y%m%d_%H%M%S")
    
    song_name = Path(song_path).stem.replace(" ", "_")
    output_name = f"song_{song_name}_{stamp}.mp4"
    
    temp_dir = Path("output/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    payload_path = temp_dir / f"payload_lyrics_{stamp}.json"
    log_path = temp_dir / f"log_lyrics_{stamp}.log"
    
    caption_style = payload.get("caption_style", "typing")
    transition_style = payload.get("transition_style", "whip_zoom")
    caption_position = payload.get("caption_position", "center")
    song_title = payload.get("song_title", "")
    include_dance = payload.get("include_dance", False)

    payload_data = {
        "song_path": song_path,
        "mode": mode,
        "custom_lyrics": custom_lyrics,
        "niche": niche,
        "mood": mood,
        "words_per_line": words_per_line,
        "language": language,
        "audio_mode": audio_mode,
        "start_time": start_time,
        "clip_duration": clip_duration,
        "end_time": end_time,
        "aspect_ratio": aspect_ratio,
        "caption_style": caption_style,
        "transition_style": transition_style,
        "caption_position": caption_position,
        "song_title": song_title,
        "include_dance": include_dance,
        "output_name": output_name
    }
    
    try:
        payload_path.write_text(json.dumps(payload_data, indent=2, ensure_ascii=False), encoding="utf-8")
        log_path.write_text("Starting lyrics rendering subprocess...\n", encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize payload/log files: {str(e)}")
        
    cmd = [
        sys.executable,
        "src/scripts/lyrics_worker.py",
        "--payload",
        str(payload_path),
        str(log_path)
    ]
    
    try:
        import os
        sub_env = os.environ.copy()
        sub_env["PYTHONIOENCODING"] = "utf-8"
        sub_env["PYTHONUNBUFFERED"] = "1"
        
        log_fh = open(str(log_path), "a", encoding="utf-8")
        render_process = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            env=sub_env
        )
        
        current_render_log_path = log_path
        current_render_output_name = output_name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to spawn lyrics subprocess: {str(e)}")
        
    return {"message": "Lyrics rendering started"}
        
# Helper to extract telemetry from step labels and log markers
def extract_render_telemetry(step_label: str, log_content: str):
    current_frame = None
    total_frames = None
    fps = None
    eta = ""
    
    frame_m = re.search(r'frame\s+(\d+)/(\d+)', step_label, re.IGNORECASE)
    if frame_m:
        current_frame = int(frame_m.group(1))
        total_frames = int(frame_m.group(2))
    else:
        frame_logs = re.findall(r'frame\s+(\d+)/(\d+)', log_content, re.IGNORECASE)
        if frame_logs:
            current_frame = int(frame_logs[-1][0])
            total_frames = int(frame_logs[-1][1])
            
    fps_m = re.search(r'([\d.]+)\s*fps', step_label, re.IGNORECASE)
    if fps_m:
        try:
            fps = float(fps_m.group(1))
        except:
            pass
        
    eta_m = re.search(r'~([\w\s]+left)', step_label, re.IGNORECASE)
    if eta_m:
        eta = eta_m.group(1).strip()
        
    return {
        "current_frame": current_frame,
        "total_frames": total_frames,
        "fps": fps,
        "eta": eta
    }

# Track last seen progress to enforce monotonic increasing values during active renders
last_render_progress = 0

# GET Render status
# ────────────────────────────────────────────────────────────────
# LONGFORM CLIPPER — sermons/podcasts → captioned vertical shorts
# ────────────────────────────────────────────────────────────────
import time


def _clipper_read_status() -> Dict:
    if not CLIPPER_STATUS_PATH.exists():
        return {}
    try:
        return json.loads(CLIPPER_STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _clipper_is_active() -> bool:
    if clipper_process is None:
        return False
    return clipper_process.poll() is None


def _clipper_log_tail(max_chars: int = 8000) -> str:
    p = Path(current_clipper_log_path) if current_clipper_log_path else None
    if p is None or not p.exists():
        # Server restart / foreign job: fall back to newest clipper log on disk
        temp_dir = Path("output/temp")
        try:
            logs = sorted(temp_dir.glob("clipper_log_*.log"),
                          key=lambda x: x.stat().st_mtime, reverse=True)
        except Exception:
            logs = []
        p = logs[0] if logs else None
    if p is None or not p.exists():
        return ""
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if len(txt) > max_chars:
        txt = "…" + txt[-max_chars:]
    return txt


def _spawn_clipper_job(job: str, payload: Dict):
    global clipper_process, current_clipper_log_path, current_clipper_job

    if _clipper_is_active():
        raise HTTPException(status_code=400, detail="A clipper job is already running")

    stamp = time.strftime("%Y%m%d_%H%M%S")
    temp_dir = Path("output/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    payload_path = temp_dir / f"clipper_payload_{stamp}.json"
    log_path = temp_dir / f"clipper_log_{stamp}.log"

    try:
        payload_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        log_path.write_text(f"Starting clipper {job} job...\n", encoding="utf-8")
        # Seed status so the first poll never sees a stale previous result
        CLIPPER_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        CLIPPER_STATUS_PATH.write_text(json.dumps({
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
            "started_at": stamp,
            "updated_at": stamp,
        }, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to initialize clipper job files: {str(e)}")

    cmd = [
        sys.executable,
        "src/scripts/clipper_worker.py",
        "--job", job,
        "--payload", str(payload_path),
    ]

    try:
        sub_env = os.environ.copy()
        sub_env["PYTHONIOENCODING"] = "utf-8"
        sub_env["PYTHONUNBUFFERED"] = "1"
        log_fh = open(str(log_path), "a", encoding="utf-8")
        clipper_process = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            env=sub_env,
        )
        current_clipper_log_path = log_path
        current_clipper_job = job
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to spawn clipper subprocess: {str(e)}")

    return log_path


@app.get("/api/clipper/sources")
def clipper_sources():
    from src.video.longform_clipper import list_source_videos
    try:
        items = list_source_videos()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"sources": items, "active": _clipper_is_active()}


@app.post("/api/clipper/upload")
async def clipper_upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in CLIPPER_SOURCE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video type '{suffix}'. "
                   f"Supported: {', '.join(sorted(CLIPPER_SOURCE_EXTS))}",
        )

    CLIPPER_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.strip() or "video.mp4"
    safe_name = re.sub(r"[^\w.\- ()]", "_", safe_name)
    dest = CLIPPER_SOURCE_DIR / safe_name

    try:
        with open(dest, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    return {
        "message": f"Uploaded {safe_name}",
        "name": safe_name,
        "size_mb": round(dest.stat().st_size / (1024 * 1024), 2),
    }


def _clipper_validate_source(source) -> str:
    if not source:
        raise HTTPException(status_code=400, detail="source is required")
    from src.video.longform_clipper import resolve_video
    try:
        resolve_video(source)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid source: {str(e)}")
    return source


@app.post("/api/clipper/analyze")
def clipper_analyze(payload: Dict):
    if _clipper_is_active():
        raise HTTPException(status_code=400, detail="A clipper job is already running")

    source = _clipper_validate_source(payload.get("source"))
    try:
        min_dur = float(payload.get("min_dur", 20))
        max_dur = float(payload.get("max_dur", 50))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="min_dur/max_dur must be numbers")
    if max_dur <= min_dur:
        raise HTTPException(status_code=400, detail="max_dur must be greater than min_dur")

    _spawn_clipper_job("analyze", {
        "source": source,
        "language": payload.get("language", "auto"),
        "model": payload.get("model", "base"),
        "min_dur": min_dur,
        "max_dur": max_dur,
    })
    return {"message": "Clipper analysis started", "job": "analyze"}


@app.post("/api/clipper/render")
def clipper_render(payload: Dict):
    if _clipper_is_active():
        raise HTTPException(status_code=400, detail="A clipper job is already running")

    source = _clipper_validate_source(payload.get("source"))
    try:
        min_dur = float(payload.get("min_dur", 20))
        max_dur = float(payload.get("max_dur", 50))
        count = int(payload.get("count", 3))
        words_per_line = int(payload.get("words_per_line", 4))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400,
                            detail="count / words_per_line / min_dur / max_dur must be numbers")
    if max_dur <= min_dur:
        raise HTTPException(status_code=400, detail="max_dur must be greater than min_dur")

    selected = payload.get("selected") or None
    if selected is not None:
        if not isinstance(selected, list):
            raise HTTPException(
                status_code=400,
                detail="selected must be a list of time windows or ranks")
        norm = []
        for item in selected:
            if isinstance(item, dict):
                try:
                    norm.append({"start": float(item["start"]),
                                 "end": float(item["end"])})
                except (KeyError, TypeError, ValueError):
                    raise HTTPException(
                        status_code=400,
                        detail="selected windows need numeric start/end")
            else:
                try:
                    norm.append(int(item))
                except (TypeError, ValueError):
                    raise HTTPException(
                        status_code=400,
                        detail="selected must contain integers or {start,end} objects")
        selected = norm or None

    _spawn_clipper_job("render", {
        "source": source,
        "language": payload.get("language", "auto"),
        "model": payload.get("model", "base"),
        "min_dur": min_dur,
        "max_dur": max_dur,
        "count": max(1, min(10, count)),
        "words_per_line": max(1, min(8, words_per_line)),
        "crop": payload.get("crop", "center"),
        "niche": payload.get("niche", "gospel"),
        "mood": payload.get("mood", "peaceful"),
        "selected": selected,
    })
    return {"message": "Clipper render started", "job": "render"}


@app.get("/api/clipper/status")
def clipper_status():
    st = _clipper_read_status()
    alive = _clipper_is_active()
    status = st.get("status", "idle")
    error = st.get("error")

    if alive:
        status = "running"
    elif status == "running":
        # Worker never finalized: process died or server restarted mid-job
        status = "failed"
        error = error or "Clipper worker exited unexpectedly — check the log."

    progress = 0 if status == "idle" else int(st.get("progress") or 0)
    if status == "completed":
        progress = 100

    return {
        "status": status,
        "job": st.get("job") or current_clipper_job or "",
        "progress": progress,
        "step": st.get("step", ""),
        "log": _clipper_log_tail(),
        "candidates": st.get("candidates", []),
        "outputs": st.get("outputs", []),
        "error": error,
        "source": st.get("source", ""),
        "language": st.get("language", ""),
        "duration": st.get("duration"),
        "transcript_path": st.get("transcript_path", ""),
        "active": alive,
    }


@app.get("/api/render/status")
def get_render_status():
    global render_process, current_render_log_path, current_render_output_name, last_render_progress
    
    if render_process is None:
        last_render_progress = 0
        return {
            "status": "idle",
            "progress": 0,
            "log": "",
            "output_file": "",
            "step_label": "",
            "current_frame": None,
            "total_frames": None,
            "fps": None,
            "eta": ""
        }
        
    exit_code = render_process.poll()
    
    log_content = ""
    if current_render_log_path and current_render_log_path.exists():
        try:
            log_content = current_render_log_path.read_text(encoding="utf-8")
        except Exception as e:
            log_content = f"Error reading log: {str(e)}"

    # ── Parse structured PROGRESS:N% markers emitted by render_worker ──
    progress = 5
    step_label = ""
    progress_matches = re.findall(r'PROGRESS:(\d+)%(?:\s+STEP:(.+))?', log_content)
    if progress_matches:
        # Find maximum progress seen so far in this run
        all_pcts = [int(m[0]) for m in progress_matches]
        progress = max(all_pcts) if all_pcts else 5
        last = progress_matches[-1]
        step_label = last[1].strip() if last[1] else step_label
    else:
        # Legacy fallback for older log formats
        if "Generating voice narration" in log_content:
            progress = 15
        if "Creating sync voice audio" in log_content:
            progress = 25
        if "Voice generated:" in log_content:
            progress = 40
        if "Loading background media assets" in log_content:
            progress = 50
        if "Loaded" in log_content and "media items" in log_content:
            progress = 60
        if "Compiling video layers" in log_content or "Assembling video scenes" in log_content:
            progress = 65
        if "Building dynamic karaoke" in log_content or "Styling typography" in log_content:
            progress = 72

    # Enforce monotonic progress (never goes backwards)
    progress = max(progress, last_render_progress)
    last_render_progress = progress

    status = "rendering"
    output_file = ""
            
    if exit_code is not None:
        if exit_code == 0 or "SUCCESS:" in log_content:
            status = "completed"
            progress = 100
            last_render_progress = 100
            output_file = current_render_output_name or ""
            if not step_label:
                step_label = "✅ Render complete!"
        else:
            status = "failed"
            if not step_label:
                step_label = "❌ Render failed"

    telemetry = extract_render_telemetry(step_label, log_content)
            
    return {
        "status": status,
        "progress": progress,
        "log": log_content,
        "output_file": output_file,
        "step_label": step_label,
        **telemetry
    }

# API to get pipeline log history
@app.get("/api/pipeline/log")
def get_pipeline_log():
    try:
        from src.scripts.scheduler import PUBLISH_LOG
        if not PUBLISH_LOG.exists():
            return {"log": {}}
        return {"log": json.loads(PUBLISH_LOG.read_text(encoding="utf-8"))}
    except Exception as e:
        return {"log": {}, "error": str(e)}

# API to get pipeline config details
@app.get("/api/pipeline/config")
def get_pipeline_config():
    from config.settings import ENV
    platforms_str = ENV.get("PUBLISH_PLATFORMS", "youtube")
    active_platforms = [p.strip().lower() for p in platforms_str.split(",") if p.strip()]
    
    # Check if directory exist for profiles
    youtube_profile = Path("assets/browser_profiles/youtube").exists()
    tiktok_profile = Path("assets/browser_profiles/tiktok").exists()
    instagram_profile = Path("assets/browser_profiles/instagram").exists()
    
    return {
        "active_platforms": active_platforms,
        "youtube_ready": youtube_profile,
        "tiktok_ready": tiktok_profile,
        "instagram_ready": instagram_profile,
        "niche": ENV.get("NICHE", "gospel")
    }

# API to trigger publisher daily pipeline run
@app.post("/api/pipeline/run")
def trigger_pipeline(payload: Dict):
    global pipeline_process, current_pipeline_log_path
    
    if pipeline_process is not None:
        status = get_pipeline_status()
        if status["status"] == "running":
            raise HTTPException(status_code=400, detail="Pipeline run is already active")
            
    force = payload.get("force", False)
    
    import time
    stamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Ensure temp directory exists
    temp_dir = Path("output/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = temp_dir / f"pipeline_{stamp}.log"
    
    try:
        log_path.write_text("Starting automated pipeline subprocess...\n", encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize pipeline log file: {str(e)}")
        
    cmd = [
        sys.executable,
        "src/scripts/scheduler.py"
    ]
    if force:
        cmd.append("--force")
        
    try:
        import os
        sub_env = os.environ.copy()
        sub_env["PYTHONIOENCODING"] = "utf-8"
        sub_env["PYTHONUNBUFFERED"] = "1"
        
        log_file_handle = open(log_path, "w", encoding="utf-8")
        pipeline_process = subprocess.Popen(
            cmd,
            stdout=log_file_handle,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=sub_env
        )
        log_file_handle.close()
        
        current_pipeline_log_path = log_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to spawn pipeline subprocess: {str(e)}")
        
    return {"message": "Pipeline run started"}

# API to get publisher daily pipeline status
@app.get("/api/pipeline/status")
def get_pipeline_status():
    global pipeline_process, current_pipeline_log_path
    
    if pipeline_process is None:
        return {"status": "idle", "progress": 0, "log": "", "step_label": ""}
        
    exit_code = pipeline_process.poll()
    
    log_content = ""
    if current_pipeline_log_path and current_pipeline_log_path.exists():
        try:
            log_content = current_pipeline_log_path.read_text(encoding="utf-8")
        except Exception as e:
            log_content = f"Error reading log: {str(e)}"

    # ── Parse structured PROGRESS:N% markers ──
    progress = 5
    step_label = ""
    progress_matches = re.findall(r'PROGRESS:(\d+)%(?:\s+STEP:(.+))?', log_content)
    if progress_matches:
        last = progress_matches[-1]
        progress = int(last[0])
        step_label = last[1].strip() if last[1] else step_label
    else:
        # Legacy fallback
        if "Step 1" in log_content:
            progress = 20
        if "Step 2" in log_content:
            progress = 40
        if "Step 3" in log_content:
            progress = 60
        if "Step 4" in log_content:
            progress = 80
        if "Step 5" in log_content:
            progress = 90

    status = "running"
        
    if exit_code is not None:
        if exit_code == 0 or "completed successfully" in log_content:
            status = "completed"
            progress = 100
            if not step_label:
                step_label = "✅ Pipeline complete!"
        else:
            status = "failed"
            if not step_label:
                step_label = "❌ Pipeline failed"
            
    return {
        "status": status,
        "progress": progress,
        "log": log_content,
        "step_label": step_label
    }

# ============================================================
# SCHEDULED VIDEO UPLOAD QUEUE
# ============================================================
import datetime

QUEUE_DB = Path("output/upload_queue.json")

def load_queue_db() -> List[Dict]:
    if not QUEUE_DB.exists():
        return []
    try:
        return json.loads(QUEUE_DB.read_text(encoding="utf-8"))
    except Exception:
        return []
        
def save_queue_db(data: List[Dict]):
    QUEUE_DB.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_DB.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

async def run_item_upload_process(item_id: str):
    print(f"[Queue Daemon] Launching upload process for queue item: {item_id}", flush=True)
    
    db = load_queue_db()
    item = next((x for x in db if x["id"] == item_id), None)
    if not item:
        return
        
    video_path = item.get("video_path")
    title = item.get("title", "")
    caption = item.get("description", "")
    thumbnail = item.get("thumbnail_path")
    platforms = item.get("platforms", [])
    
    log_dir = Path("output/temp")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    failed_platforms = []
    
    for platform in platforms:
        db = load_queue_db()
        item = next((x for x in db if x["id"] == item_id), None)
        if item:
            item["publish_log"] += f"[{platform.upper()}] Uploading...\n"
            save_queue_db(db)
            
        log_path = log_dir / f"queue_upload_{item_id}_{platform}.log"
        
        cmd = [
            sys.executable,
            "src/utils/uploader.py",
            "--platform", platform,
            "--video", str(video_path),
            "--title", title,
            "--caption", caption
        ]
        if thumbnail and platform == "youtube":
            cmd.extend(["--thumbnail", str(thumbnail)])
            
        try:
            log_file_handle = open(log_path, "w", encoding="utf-8")
            import os
            sub_env = os.environ.copy()
            sub_env["PYTHONIOENCODING"] = "utf-8"
            
            proc = subprocess.Popen(
                cmd,
                stdout=log_file_handle,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=sub_env
            )
            
            while proc.poll() is None:
                await asyncio.sleep(1)
                
            log_file_handle.close()
            
            log_text = ""
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8")
                
            exit_code = proc.poll()
            # Success = exit 0 OR success string present in log
            upload_ok = (exit_code == 0) or ("[SUCCESS]" in log_text) or ("SUCCESS" in log_text and "ERROR" not in log_text)
            if upload_ok:
                success_count += 1
                db = load_queue_db()
                item = next((x for x in db if x["id"] == item_id), None)
                if item:
                    item["publish_log"] += f"[{platform.upper()}] ✅ SUCCESS! Video uploaded.\n"
                    save_queue_db(db)
            else:
                failed_platforms.append(platform)
                # Grab last 5 lines of log for display
                log_tail = "\n".join(log_text.strip().splitlines()[-5:]) if log_text else "No log output."
                db = load_queue_db()
                item = next((x for x in db if x["id"] == item_id), None)
                if item:
                    item["publish_log"] += f"[{platform.upper()}] ❌ FAILED (exit={exit_code}).\nLast log:\n{log_tail}\n"
                    save_queue_db(db)
        except Exception as ex:
            failed_platforms.append(platform)
            db = load_queue_db()
            item = next((x for x in db if x["id"] == item_id), None)
            if item:
                item["publish_log"] += f"[{platform.upper()}] EXCEPTION: {str(ex)}\n"
                save_queue_db(db)
                
    db = load_queue_db()
    item = next((x for x in db if x["id"] == item_id), None)
    if item:
        if success_count == len(platforms):
            item["status"] = "published"
            item["published_at"] = datetime.datetime.now().isoformat()
        elif success_count > 0:
            item["status"] = "partial_success"
            item["published_at"] = datetime.datetime.now().isoformat()
            item["error_message"] = f"Failed on: {failed_platforms}"
        else:
            item["status"] = "failed"
            item["error_message"] = f"Failed on all platforms: {failed_platforms}"
        save_queue_db(db)

async def check_and_publish_queue_items():
    db = load_queue_db()
    changed = False
    
    for item in db:
        if item.get("status") != "pending":
            continue
            
        sched_time_str = item.get("scheduled_time")
        if not sched_time_str:
            continue
            
        try:
            sched_dt = datetime.datetime.fromisoformat(sched_time_str.replace("Z", ""))
            now_dt = datetime.datetime.now()
            
            if now_dt >= sched_dt:
                item["status"] = "publishing"
                item["publish_log"] = "Publishing started...\n"
                changed = True
                asyncio.create_task(run_item_upload_process(item["id"]))
        except Exception as pe:
            print(f"Error parsing date {sched_time_str}: {pe}", flush=True)
            item["status"] = "failed"
            item["error_message"] = f"Invalid scheduled time format: {str(pe)}"
            changed = True
            
    if changed:
        save_queue_db(db)

async def check_upload_queue_loop():
    print("Starting scheduled upload queue checker daemon...", flush=True)
    while True:
        try:
            await check_and_publish_queue_items()
        except Exception as e:
            print(f"[Queue Daemon Error]: {e}", flush=True)
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_upload_queue_loop())

# Upload custom video/thumbnail
@app.post("/api/queue/upload")
async def queue_upload(
    video: UploadFile = File(...),
    thumbnail: Optional[UploadFile] = File(None)
):
    temp_dir = Path("assets/stock/uploaded_queue")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    import time
    stamp = int(time.time())
    
    # Save video
    video_ext = Path(video.filename).suffix
    video_name = f"queue_{stamp}{video_ext}"
    video_path = temp_dir / video_name
    
    try:
        content = await video.read()
        video_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")
        
    # Save thumbnail if uploaded
    thumb_path = None
    if thumbnail:
        thumb_ext = Path(thumbnail.filename).suffix
        thumb_name = f"queue_{stamp}_thumb{thumb_ext}"
        thumb_file_path = temp_dir / thumb_name
        try:
            content = await thumbnail.read()
            thumb_file_path.write_bytes(content)
            thumb_path = str(thumb_file_path)
        except Exception as e:
            print(f"Failed to save thumbnail: {e}")
            
    return {
        "video_path": str(video_path),
        "thumbnail_path": thumb_path
    }

# Perfect Description with AI
@app.post("/api/queue/perfect-description")
async def perfect_description(payload: Dict):
    draft = payload.get("description", "")
    niche = payload.get("niche", "gospel")
    
    if not draft:
        return {"perfected_description": ""}
        
    prompt = f"""
You are an expert short-form content creator and copywriter.
Take the following video description/caption draft and perfect it to be highly engaging, emotional, and viral for a short-form video (YouTube Shorts, TikTok, or Instagram Reels) in the '{niche}' niche.
Add appropriate emojis, improve hook/flow, add trending hashtags relevant to the niche, and make the CTA extremely compelling.

Draft Description:
"{draft}"

Return ONLY the polished, perfected description. No preamble, no comments, no intro. Just the polished text.
"""
    from src.scripts.ai_generator import (
        GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY,
        generate_with_groq, generate_with_gemini, generate_with_openrouter
    )
    
    raw = None
    if GROQ_API_KEY:
        raw = await generate_with_groq(prompt)
    if not raw and GEMINI_API_KEY:
        raw = await generate_with_gemini(prompt)
    if not raw and OPENROUTER_API_KEY:
        raw = await generate_with_openrouter(prompt)
        
    if raw:
        result = raw.strip().strip('"').strip("'").strip()
        return {"perfected_description": result}
        
    return {"perfected_description": draft + "\n\n#reels #shorts #motivation"}

# Add item to queue
@app.post("/api/queue/add")
def queue_add(payload: Dict):
    db = load_queue_db()
    
    import time
    item_id = f"q_{int(time.time())}"
    
    new_item = {
        "id": item_id,
        "video_path": payload.get("video_path"),
        "title": payload.get("title", "Visual Short"),
        "description": payload.get("description", ""),
        "thumbnail_path": payload.get("thumbnail_path"),
        "platforms": payload.get("platforms", ["youtube"]),
        "scheduled_time": payload.get("scheduled_time"),
        "status": "pending",
        "publish_log": "",
        "created_at": datetime.datetime.now().isoformat()
    }
    
    db.append(new_item)
    save_queue_db(db)
    return {"message": "Video scheduled successfully", "id": item_id}

# Get list of queued items
@app.get("/api/queue/list")
def queue_list():
    return {"queue": load_queue_db()}

# Delete queued item
@app.delete("/api/queue/delete/{item_id}")
def queue_delete(item_id: str):
    db = load_queue_db()
    item = next((x for x in db if x["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
        
    video_path = item.get("video_path")
    if video_path:
        try: Path(video_path).unlink()
        except: pass
    thumb_path = item.get("thumbnail_path")
    if thumb_path:
        try: Path(thumb_path).unlink()
        except: pass
        
    db = [x for x in db if x["id"] != item_id]
    save_queue_db(db)
    return {"message": "Queue item deleted successfully"}

# Immediately trigger upload for a queued item (no wait for schedule)
@app.post("/api/queue/publish-now/{item_id}")
async def queue_publish_now(item_id: str):
    db = load_queue_db()
    item = next((x for x in db if x["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if item.get("status") in ("publishing", "published"):
        raise HTTPException(status_code=400, detail=f"Item is already {item['status']}")

    # Mark as publishing immediately
    item["status"] = "publishing"
    item["publish_log"] = "Manual publish triggered...\n"
    save_queue_db(db)

    # Launch upload in background
    asyncio.create_task(run_item_upload_process(item_id))
    return {"message": "Upload triggered immediately. Check queue for progress."}

# List rendered videos
@app.get("/api/videos/rendered")
def list_rendered_videos():
    import time
    videos_dir = Path(OUTPUT_DIR) / "videos"
    if not videos_dir.exists():
        return {"videos": []}
    
    videos = []
    video_exts = [".mp4", ".mov", ".mkv", ".webm"]
    for child in sorted(videos_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if child.is_file() and child.suffix.lower() in video_exts:
            kit_json = videos_dir / f"{child.stem}_social_kit.json"
            has_kit = kit_json.exists()
            videos.append({
                "name": child.name,
                "path": str(child),
                "url": f"/output/videos/{child.name}",
                "size_mb": round(child.stat().st_size / (1024 * 1024), 2),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(child.stat().st_mtime)),
                "has_social_kit": has_kit,
                "social_kit_url": f"/api/videos/social-kit/{child.name}" if has_kit else None
            })
    return {"videos": videos}

# Get Social Media Kit for a rendered video
@app.get("/api/videos/social-kit/{video_name}")
def get_video_social_kit(video_name: str):
    videos_dir = Path(OUTPUT_DIR) / "videos"
    v_stem = Path(video_name).stem
    json_path = videos_dir / f"{v_stem}_social_kit.json"
    txt_path = videos_dir / f"{v_stem}_social_kit.txt"

    if not json_path.exists():
        # Auto-generate on the fly if not yet generated
        try:
            from src.utils.social_strategy import generate_social_package, save_social_kit
            clean_name = v_stem
            data = generate_social_package(song_name=clean_name)
            save_social_kit(str(videos_dir / video_name), data)
            return {"social_kit": data, "txt_preview": txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""}
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Social kit not found: {str(e)}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        txt_content = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""
        return {"social_kit": data, "txt_preview": txt_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read social kit: {str(e)}")

# Add rendered video to queue
@app.post("/api/queue/add-rendered")
def queue_add_rendered(payload: Dict):
    import shutil
    video_name = payload.get("video_name")
    if not video_name:
        raise HTTPException(status_code=400, detail="video_name is required")
        
    videos_dir = Path(OUTPUT_DIR) / "videos"
    src_path = videos_dir / video_name
    if not src_path.exists():
        raise HTTPException(status_code=404, detail="Rendered video not found")
        
    # Copy to uploaded_queue
    temp_dir = Path("assets/stock/uploaded_queue")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    import time
    stamp = int(time.time())
    dest_name = f"queue_{stamp}{src_path.suffix}"
    dest_path = temp_dir / dest_name
    
    try:
        shutil.copy2(src_path, dest_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy video: {str(e)}")
        
    # Add to database
    db = load_queue_db()
    item_id = f"q_{stamp}"
    
    new_item = {
        "id": item_id,
        "video_path": str(dest_path),
        "title": payload.get("title", video_name),
        "description": payload.get("description", ""),
        "thumbnail_path": None,
        "platforms": payload.get("platforms", ["youtube"]),
        "scheduled_time": payload.get("scheduled_time"),
        "status": "pending",
        "publish_log": "",
        "created_at": datetime.datetime.now().isoformat()
    }
    
    db.append(new_item)
    save_queue_db(db)
    return {"message": "Rendered video scheduled successfully", "id": item_id}

# Check platform login session health
@app.get("/api/publisher/check-session")
def check_session(platform: str):
    import time
    def launch_session():
        from playwright.sync_api import sync_playwright
        from src.utils.uploader import SocialUploader
        uploader = SocialUploader(platform=platform)
        
        with sync_playwright() as p:
            print(f"[Session Check] Launching headful browser for {platform}...")
            context = uploader._get_browser_context(p, headless=False)
            page = context.new_page()
            
            if platform == "youtube":
                page.goto("https://studio.youtube.com")
            elif platform == "tiktok":
                page.goto("https://www.tiktok.com/creator-center/upload")
            elif platform == "instagram":
                page.goto("https://www.instagram.com/")
                
            try:
                for _ in range(600): # 10 minutes max
                    if page.is_closed() or not context.pages:
                        break
                    time.sleep(1)
            except Exception:
                pass
            finally:
                try: context.close()
                except: pass
                print(f"[Session Check] Browser closed for {platform}")

    threading.Thread(target=launch_session, daemon=True).start()
    return {"message": f"Browser opened for {platform.upper()}. Verify your session or log in, then close the browser window when done."}

# Temporary Admin Helper for Git Setup
@app.get("/api/admin/run_command")
def run_command_endpoint(cmd: str):
    import subprocess
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent))
        return {
            "stdout": res.stdout,
            "stderr": res.stderr,
            "exit_code": res.returncode
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Maintenance Endpoints ────────────────────────────────────────────────────

@app.get("/api/maintenance/disk-usage")
def api_disk_usage():
    """Returns disk usage summary for all output folders."""
    try:
        from src.utils.cleanup import get_disk_usage_summary
        return get_disk_usage_summary()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/maintenance/cleanup")
def api_cleanup(days: int = 30, temp_days: int = 7, dry_run: bool = False):
    """
    Runs full cleanup: archive old videos, delete old temp files, remove failed renders.
    Set dry_run=true to preview without deleting.
    """
    try:
        from src.utils.cleanup import run_full_cleanup
        return run_full_cleanup(days=days, temp_days=temp_days, dry_run=dry_run)
    except Exception as e:
        return {"error": str(e)}


# ─── Voice Lab Endpoints ──────────────────────────────────────────────────────

@app.get("/api/tts/voices")
async def api_tts_voices(force_refresh: bool = False):
    """Returns all available voices across all TTS providers."""
    try:
        from src.utils.voice_catalog import get_all_voices
        voices = await get_all_voices(force_refresh=force_refresh)
        return {"voices": voices, "total": len(voices)}
    except Exception as e:
        return {"error": str(e), "voices": []}


@app.post("/api/tts/preview")
async def api_tts_preview(body: dict):
    """
    Generates a short TTS preview audio file.
    Body: {"voice": "sw-TZ-RehemaNeural", "text": "...", "rate": "+0%"}
    Returns: {"audio_url": "/output/previews/preview_xxx.mp3"}
    """
    try:
        from src.utils.voice_catalog import preview_voice, cleanup_old_previews
        voice = body.get("voice", "")
        text  = body.get("text", "Mungu hakusahau.")[:200]
        rate  = body.get("rate", "+0%")
        if not voice:
            raise HTTPException(400, "voice is required")
        # Background cleanup of old previews
        cleanup_old_previews(max_age_minutes=60)
        audio_url = await preview_voice(voice_id=voice, text=text, rate=rate)
        if not audio_url:
            raise HTTPException(500, "Preview generation failed — check server logs")
        return {"audio_url": audio_url, "voice": voice}
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/tts/preview/cleanup")
def api_tts_cleanup():
    """Deletes preview MP3 files older than 60 minutes."""
    try:
        from src.utils.voice_catalog import cleanup_old_previews
        deleted = cleanup_old_previews(max_age_minutes=60)
        return {"deleted": deleted}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/videos/{video_name}/credits")
def api_video_credits(video_name: str):
    """Returns the asset credits JSON for a specific video."""
    try:
        from src.utils.asset_credits import load_credits
        data = load_credits(video_name)
        if data is None:
            raise HTTPException(status_code=404, detail=f"No credits file found for '{video_name}'")
        return data
    except HTTPException:

        raise
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/videos/credits/all")
def api_all_credits():
    """Returns credits metadata for all generated videos."""
    try:
        from src.utils.asset_credits import list_all_credits
        return {"credits": list_all_credits()}
    except Exception as e:
        return {"error": str(e)}


# Serve favicon files from src/web/
_web_dir = Path(__file__).parent

@app.get("/favicon.ico", include_in_schema=False)
def favicon_ico():
    f = _web_dir / "favicon.ico"
    return FileResponse(str(f), media_type="image/x-icon") if f.exists() else HTMLResponse("", 404)

@app.get("/favicon.png", include_in_schema=False)
def favicon_png():
    f = _web_dir / "favicon.png"
    return FileResponse(str(f), media_type="image/png") if f.exists() else HTMLResponse("", 404)

@app.get("/favicon-192.png", include_in_schema=False)
def favicon_192():
    f = _web_dir / "favicon-192.png"
    return FileResponse(str(f), media_type="image/png") if f.exists() else HTMLResponse("", 404)

# Serve HTML dashboard
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        return "<h3>Error: index.html not found!</h3>"
    return html_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    import webbrowser
    import socket
    import time
    
    def find_free_port(start_port: int = 8000) -> int:
        port = start_port
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('0.0.0.0', port))
                    return port
                except OSError:
                    port += 1
        return start_port

    port = find_free_port(8000)
    
    # Auto-open web page
    def open_browser(p):
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{p}")
        
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    print(f"Starting VideoFactory Dashboard Server on:")
    print(f"  - http://localhost:{port}")
    print(f"  - http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
