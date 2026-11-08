# -*- coding: utf-8 -*-
import os
import re
import json
import time
import asyncio
from pathlib import Path

import edge_tts
from src.utils.retry import retry_async

from config.settings import (
    OUTPUT_DIR,
    ACTIVE_VOICE,
    TTS_RATE,
    TTS_VOLUME,
    TTS_PITCH,
    LANGUAGE,
    TTS_PROVIDER,
    ELEVENLABS_API_KEY,
    PUTER_TOKEN,
)


def load_env_keys():
    from pathlib import Path
    p = Path('.env')
    if not p.exists():
        return []
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.startswith('GEMINI_KEYS=') or line.startswith('GEMINI_KEYS ='):
            parts = line.split('=', 1)
            return [k.strip() for k in parts[1].split(',') if k.strip()]
    return []

GEMINI_BACKUP_KEYS = load_env_keys()

def ensure_output_dir():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


@retry_async(max_attempts=3, base_delay=1.0)
async def generate_elevenlabs_tts(text, voice, api_key):
    import httpx
    import config.settings

    keys = getattr(config.settings, "ELEVENLABS_KEYS", [])
    key_list = keys if keys else ([api_key] if api_key else [])
    if not key_list:
        raise Exception("No ElevenLabs API keys configured")

    # Verified working default premade voice IDs on ElevenLabs API:
    PREMADE_VOICES = {
        "george": "JBFqnCBsd6RMkjVDRZzb",  # Warm storyteller, British / gospel narrative
        "daniel": "onwK4e9ZLuTAKqWW03F9",  # Deep, authoritative male
        "bella": "EXAVITQu4vr4xnSDxMaL",   # Soft, heartfelt, emotional female (gospel/prayer)
        "callum": "N2lVS1w4EtoT3dr4eOWO",  # Expressive, rich male
    }
    ADAM_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # BLACKLISTED
    DEFAULT_VOICE = PREMADE_VOICES["bella"]

    v_str = str(voice or "").lower().strip()
    if "george" in v_str:
        voice_id = PREMADE_VOICES["george"]
    elif "daniel" in v_str:
        voice_id = PREMADE_VOICES["daniel"]
    elif "callum" in v_str:
        voice_id = PREMADE_VOICES["callum"]
    elif "bella" in v_str or "female" in v_str or "prayer" in v_str:
        voice_id = PREMADE_VOICES["bella"]
    elif "(" in str(voice) and ")" in str(voice):
        extracted = str(voice).split("(")[1].split(")")[0].strip()
        voice_id = DEFAULT_VOICE if extracted == ADAM_VOICE_ID else extracted
    elif voice and len(str(voice)) > 15 and not str(voice).startswith("elevenlabs:"):
        voice_id = DEFAULT_VOICE if str(voice).strip() == ADAM_VOICE_ID else str(voice).strip()
    else:
        voice_id = DEFAULT_VOICE

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.78,
            "style": 0.15,
            "use_speaker_boost": True
        }
    }

    last_err = None
    for key in key_list:
        headers = {
            "xi-api-key": key,
            "Content-Type": "application/json",
            "accept": "audio/mpeg"
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    return response.content
                else:
                    last_err = f"Status {response.status_code}: {response.text[:100]}"
                    print(f"  ElevenLabs key failed ({key[:12]}...): {last_err}. Trying next...")
        except Exception as e:
            last_err = str(e)
            print(f"  ElevenLabs key error: {e}. Trying next...")

    raise Exception(f"All ElevenLabs keys failed. Last error: {last_err}")



PUTER_VOICE_MAP = {
    # English Neural -> OpenAI
    "en-US-ChristopherNeural": "onyx",
    "en-US-GuyNeural": "echo",
    "en-US-JennyNeural": "shimmer",
    "en-US-AriaNeural": "nova",
    "en-US-DavisNeural": "onyx",
    
    # Swahili Neural -> OpenAI
    "sw-TZ-RehemaNeural": "shimmer",
    "sw-TZ-DaudiNeural": "echo",
    "sw-KE-RafikiNeural": "echo",
    "sw-KE-ZuriNeural": "shimmer",
}


_GEMINI_KEY_INDEX = 0


async def generate_gemini_tts(text, voice, api_key):
    """Generate TTS via Gemini API (gemini-2.5-flash-preview-tts).
    Handles both key formats:
    - AQ.* keys (Auth Keys, new format): uses x-goog-api-key header
    - AIzaSy* keys (Standard keys, legacy): uses ?key= query param
    """
    import httpx
    import base64
    
    voice_name = "Aoede"
    v_clean = str(voice or "").replace("[GEMINI]", "").replace("[gemini]", "").strip()
    if ":" in v_clean:
        voice_name = v_clean.split(":")[-1].strip()
    elif v_clean:
        voice_name = v_clean

    model = "gemini-2.5-flash-preview-tts"
    payload = {
        "contents": {
            "parts": [{"text": text}]
        },
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        }
    }

    # Detect key format: AQ.* = Auth Key (header), AIzaSy* = Standard (query param)
    is_auth_key = api_key.startswith("AQ.")
    if is_auth_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Gemini TTS Status {response.status_code}: {response.text[:120]}")

        res_data = response.json()
        candidates = res_data.get("candidates", [])
        if not candidates or not candidates[0].get("content"):
            err_msg = res_data.get("error", {}).get("message", "No content")
            raise Exception(f"Gemini TTS empty response: {err_msg}")

        parts = candidates[0]["content"].get("parts", [])
        if not parts:
            raise Exception("No parts in Gemini TTS response")

        audio_base64 = None
        for part in parts:
            if "inlineData" in part and "data" in part["inlineData"]:
                audio_base64 = part["inlineData"]["data"]
                break

        if not audio_base64:
            raise Exception("No inline audio data in Gemini TTS parts")

        audio_bytes = base64.b64decode(audio_base64)
        from src.audio.ffmpeg_ops import pcm_to_mp3
        return pcm_to_mp3(audio_bytes, frame_rate=24000, channels=1)


async def generate_gemini_tts_with_fallback(text, voice, primary_key=None):
    """
    Circular 19-key Gemini TTS rotator.
    Cycles through all available keys in GEMINI_KEYS to automatically bypass individual 429 RPM limits.
    Advances key index on success for balanced high throughput.
    """
    global _GEMINI_KEY_INDEX
    import config.settings
    env_keys = getattr(config.settings, "GEMINI_KEYS", []) or GEMINI_BACKUP_KEYS

    auth_keys = [k for k in env_keys if k.startswith("AQ.")]
    standard_keys = [k for k in env_keys if k.startswith("AIzaSy")]
    if primary_key and not primary_key.startswith("AQ.") and primary_key not in standard_keys:
        standard_keys.insert(0, primary_key)
    
    merged_keys = auth_keys + standard_keys
    if not merged_keys:
        return None

    num_keys = len(merged_keys)
    start_idx = _GEMINI_KEY_INDEX % num_keys

    # Try every key in circular order across the entire pool
    for offset in range(num_keys):
        idx = (start_idx + offset) % num_keys
        k = merged_keys[idx]
        try:
            result = await generate_gemini_tts(text, voice, k)
            if result:
                # Key succeeded! Advance index for next line
                _GEMINI_KEY_INDEX = (idx + 1) % num_keys
                return result
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                # Rate limit on this key, rotate to next key
                continue
            elif "404" in err_str or "400" in err_str:
                continue
            else:
                continue

    return None


@retry_async(max_attempts=3, base_delay=1.0)
async def generate_puter_tts(text, voice, token, speed=1.0, **extra):
    import httpx
    
    sub_provider = "openai"
    actual_voice = "alloy"
    
    # Parse voice string format e.g. "puter:aws-polly:Joanna"
    if isinstance(voice, str) and voice.startswith("puter:"):
        parts = voice.split(":")
        if len(parts) >= 3:
            sub_provider = parts[1]
            actual_voice = parts[2]
        elif len(parts) == 2:
            actual_voice = parts[1]
            if actual_voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
                sub_provider = "openai"
    else:
        # Backward compatibility for plain voices
        actual_voice = PUTER_VOICE_MAP.get(voice, "alloy")
        if voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
            actual_voice = voice
        sub_provider = "openai"

    # If it is OpenAI and we want to use the standard direct openai-compatible endpoint:
    if sub_provider == "openai":
        url = "https://api.puter.com/puterai/openai/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "model": extra.get("model", "tts-1"),
            "input": text,
            "voice": actual_voice,
            "speed": speed,
        }
        if extra.get("output_format"):
            data["response_format"] = extra["output_format"]
        if extra.get("instructions"):
            data["instructions"] = extra["instructions"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code != 200:
                raise Exception(f"Puter AI OpenAI-direct TTS failed: Status {response.status_code}, {response.text}")
            return response.content

    # For other sub-providers (aws-polly, elevenlabs, gemini, xai, openai), use the low-level driver call API:
    url = "https://api.puter.com/drivers/call"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    args = {
        "text": text,
        "voice": actual_voice,
        "provider": sub_provider,
        "speed": speed,
    }
    
    # Add sensible defaults for sub-providers (override with extra kwargs)
    if sub_provider == "aws-polly":
        args["language"] = extra.get("language", "en-US")
        args["engine"] = extra.get("engine", "neural")
    elif sub_provider == "elevenlabs":
        args["model"] = extra.get("model", "eleven_multilingual_v2")
        if extra.get("output_format"):
            args["output_format"] = extra["output_format"]
    elif sub_provider == "gemini":
        args["model"] = extra.get("model", "gemini-2.5-flash-preview-tts")
        if extra.get("instructions"):
            args["instructions"] = extra["instructions"]
    elif sub_provider == "xai":
        args["language"] = extra.get("language", "en")
        if extra.get("output_format"):
            args["output_format"] = extra["output_format"]
    elif sub_provider == "openai":
        args["model"] = extra.get("model", "tts-1")
        
    payload = {
        "interface": "puter-tts",
        "driver": sub_provider if sub_provider in ["aws-polly", "elevenlabs", "gemini", "xai", "openai"] else "aws-polly",
        "method": "synthesize",
        "args": args
    }
    
    print(f"Calling Puter driver endpoint for {sub_provider}:{actual_voice}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Puter driver call failed: Status {response.status_code}, {response.text}")
            
        content_type = response.headers.get("content-type", "").lower()
        
        if "json" in content_type:
            try:
                res_data = response.json()
                result = res_data
                if isinstance(res_data, dict):
                    if "result" in res_data:
                        result = res_data["result"]
                    elif "data" in res_data:
                        result = res_data["data"]
                
                # Check for base64 or URL redirect
                if isinstance(result, dict):
                    if "base64" in result:
                        import base64
                        return base64.b64decode(result["base64"])
                    elif "base64_data" in result:
                        import base64
                        return base64.b64decode(result["base64_data"])
                    elif "url" in result:
                        audio_url = result["url"]
                        audio_res = await client.get(audio_url)
                        if audio_res.status_code == 200:
                            return audio_res.content
                        raise Exception(f"Failed to fetch audio from redirect URL: {audio_url}")
                    elif "audio" in result:
                        audio_val = result["audio"]
                        if isinstance(audio_val, str):
                            if "," in audio_val:
                                audio_val = audio_val.split(",", 1)[1]
                            import base64
                            return base64.b64decode(audio_val)
                elif isinstance(result, str):
                    if result.startswith("http://") or result.startswith("https://"):
                        audio_res = await client.get(result)
                        if audio_res.status_code == 200:
                            return audio_res.content
                        raise Exception(f"Failed to fetch audio from URL: {result}")
                    try:
                        import base64
                        return base64.b64decode(result)
                    except:
                        pass
                raise Exception(f"Could not extract audio data from Puter driver response: {res_data}")
            except Exception as e:
                raise Exception(f"Puter JSON parsing failed: {e}. Raw response: {response.text}")
        
        return response.content



def safe_filename(text, max_len=50):
    text = text.strip().lower()
    text = re.sub(r'[^a-zA-Z0-9_\- ]+', '', text)
    text = re.sub(r'\s+', '_', text)
    return text[:max_len] if text else 'voice'


def now_stamp():
    return time.strftime('%Y%m%d_%H%M%S')


def get_default_voice(language='english'):
    if language == 'swahili':
        import config.settings
        gemini_key = getattr(config.settings, "GEMINI_API_KEY", "")
        puter_token = getattr(config.settings, "PUTER_TOKEN", "")
        if gemini_key:
            return 'direct-gemini:Puck'
        elif puter_token:
            return 'puter:gemini:Puck'
        return 'en-US-ChristopherNeural'
    return ACTIVE_VOICE



def is_edge_voice(voice):
    return isinstance(voice, str) and voice.endswith("Neural") and len(voice.split("-")) >= 3


class TTSEngine:

    def __init__(self, voice=None, rate=None, volume=None, pitch=None):
        ensure_output_dir()
        self.voice = voice or get_default_voice(LANGUAGE)
        self.rate = rate or TTS_RATE
        self.volume = volume or TTS_VOLUME
        self.pitch = pitch or TTS_PITCH

    async def generate_voice(self, text, output_name=None, **extra_puter_kwargs):
        ensure_output_dir()
        audio_dir = Path(OUTPUT_DIR) / 'audio'
        audio_dir.mkdir(parents=True, exist_ok=True)

        if not output_name:
            output_name = f'voice_{now_stamp()}.mp3'

        output_path = audio_dir / output_name

        import config.settings
        import importlib
        importlib.reload(config.settings)
        
        provider = getattr(config.settings, "TTS_PROVIDER", "edge-tts")
        el_key = getattr(config.settings, "ELEVENLABS_API_KEY", "")
        puter_token = getattr(config.settings, "PUTER_TOKEN", "")
        gemini_key = getattr(config.settings, "GEMINI_API_KEY", "")

        # Auto-detect provider from voice string
        voice_str = str(self.voice or "").strip()
        clean_v = voice_str.replace("[GEMINI]", "").replace("[gemini]", "").strip()
        if clean_v.startswith("puter:gemini:") or clean_v.startswith("gemini:"):
            gem_name = clean_v.split(":")[-1].strip()
            self.voice = f"direct-gemini:{gem_name}"
            provider = "direct-gemini"
        elif clean_v.startswith("direct-gemini:"):
            provider = "direct-gemini"
        elif clean_v.lower() in ["aoede", "puck", "charon", "kore", "fenrir", "zephyr", "leda", "enceladus"] or "[gemini]" in voice_str.lower():
            self.voice = f"direct-gemini:{clean_v}"
            provider = "direct-gemini"
        elif clean_v.startswith("puter:"):
            provider = "puter"
        elif clean_v.startswith("elevenlabs:") or ("(" in clean_v and ")" in clean_v and len(clean_v.split("(")[1].split(")")[0]) > 10):
            provider = "elevenlabs"

        audio_bytes = None
        error_msg = None

        if provider == "direct-gemini":
            try:
                audio_bytes = await generate_gemini_tts_with_fallback(text, self.voice, gemini_key)
            except Exception as e:
                error_msg = f"Direct Gemini failed: {e}"
        elif provider == "elevenlabs" and el_key:
            try:
                audio_bytes = await generate_elevenlabs_tts(text, self.voice, el_key)
            except Exception as e:
                error_msg = f"ElevenLabs failed: {e}"
        elif provider == "puter" and puter_token:
            try:
                opts = dict(extra_puter_kwargs)
                audio_bytes = await generate_puter_tts(text, self.voice, puter_token, **opts)
            except Exception as e:
                error_msg = f"Puter failed: {e}"

        if audio_bytes:
            output_path.write_bytes(audio_bytes)
        else:
            if error_msg:
                print(f"  {error_msg}. Falling back to edge-tts.")
            fallback_voice = self.voice
            if provider in ["elevenlabs", "puter", "direct-gemini"] or not is_edge_voice(fallback_voice):
                from config.settings import LANGUAGE
                fallback_voice = get_default_voice(LANGUAGE)
            
            if not is_edge_voice(fallback_voice):
                from config.settings import LANGUAGE
                if LANGUAGE == 'swahili':
                    fallback_voice = 'sw-KE-RafikiNeural'
                else:
                    fallback_voice = 'en-US-ChristopherNeural'
                
            comm = edge_tts.Communicate(
                text=text,
                voice=fallback_voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
            )
            await comm.save(str(output_path))

        return str(output_path)

    async def generate_per_line_synced(self, lines, prefix='reel'):

        import config.settings
        import importlib
        importlib.reload(config.settings)
        
        provider = getattr(config.settings, "TTS_PROVIDER", "edge-tts")
        el_key = getattr(config.settings, "ELEVENLABS_API_KEY", "")
        puter_token = getattr(config.settings, "PUTER_TOKEN", "")
        gemini_key = getattr(config.settings, "GEMINI_API_KEY", "")

        # Auto-detect provider and canonicalize voice string
        voice_str = str(self.voice or "").strip()
        clean_v = voice_str.replace("[GEMINI]", "").replace("[gemini]", "").strip()
        if clean_v.startswith("puter:gemini:") or clean_v.startswith("gemini:"):
            gem_name = clean_v.split(":")[-1].strip()
            self.voice = f"direct-gemini:{gem_name}"
            provider = "direct-gemini"
        elif clean_v.startswith("direct-gemini:"):
            provider = "direct-gemini"
        elif clean_v.lower() in ["aoede", "puck", "charon", "kore", "fenrir", "zephyr", "leda", "enceladus"] or "[gemini]" in voice_str.lower():
            self.voice = f"direct-gemini:{clean_v}"
            provider = "direct-gemini"
        elif clean_v.startswith("puter:"):
            provider = "puter"
        elif clean_v.startswith("elevenlabs:") or ("(" in clean_v and ")" in clean_v and len(clean_v.split("(")[1].split(")")[0]) > 10):
            provider = "elevenlabs"

        ensure_output_dir()
        audio_dir = Path(OUTPUT_DIR) / 'audio'
        subs_dir = Path(OUTPUT_DIR) / 'subtitles'
        temp_dir = Path(OUTPUT_DIR) / 'audio' / '_temp'
        audio_dir.mkdir(parents=True, exist_ok=True)
        subs_dir.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        cleaned = [l.strip() for l in lines if l and l.strip()]
        if not cleaned:
            return None

        timestamp = now_stamp()
        file_base = f'{prefix}_{timestamp}'

        # Determine consistent fallback voice once for entire reel
        fallback_voice = self.voice
        if provider in ["elevenlabs", "puter", "direct-gemini"] or not is_edge_voice(fallback_voice):
            fallback_voice = 'sw-KE-RafikiNeural' if any(w in " ".join(cleaned).lower() for w in ["mungu", "yesu", "bwana", "amina", "roho", "maisha", "imani", "kwa", "katika", "yako", "wako"]) else 'en-US-ChristopherNeural'
        if not is_edge_voice(fallback_voice):
            fallback_voice = 'sw-KE-RafikiNeural'
        puter_failed = False
        gemini_failed = False
        elevenlabs_failed = False

        line_audios = []

        for i, line in enumerate(cleaned):
            # Sanitize line - remove problematic characters
            safe_line = line.strip()
            # Remove emojis and special unicode that might break TTS
            safe_line = ''.join(c for c in safe_line if ord(c) < 128 or c.isalpha() or c.isspace() or c in '.,!?')
            safe_line = safe_line.strip()
            
            if len(safe_line) < 2:
                print(f'  Line {i+1} too short after cleanup, skipping')
                continue

            temp_path = temp_dir / f'{file_base}_line_{i:03d}.mp3'
            
            # Try TTS with fast fallback
            success = False
            for attempt in range(2):
                try:
                    # Remove stale file before retry
                    if temp_path.exists():
                        try:
                            temp_path.unlink()
                        except:
                            pass

                    audio_bytes = None
                    error_msg = None

                    try:
                        if provider == "direct-gemini":
                            audio_bytes = await generate_gemini_tts_with_fallback(safe_line, self.voice, gemini_key)
                        elif provider == "elevenlabs" and el_key and not elevenlabs_failed:
                            audio_bytes = await generate_elevenlabs_tts(safe_line, self.voice, el_key)
                        elif provider == "puter" and puter_token and not puter_failed:
                            speed = 1.0
                            rate_str = self.rate
                            if rate_str and rate_str.endswith('%'):
                                try:
                                    pct = float(rate_str.rstrip('%'))
                                    speed = max(0.85, min(1.20, 1.0 + pct / 100.0))
                                except:
                                    pass
                            if i == 0:
                                print(f'  TTS speed: {speed:.2f}x (rate={self.rate})')
                            audio_bytes = await generate_puter_tts(safe_line, self.voice, puter_token, speed=speed)
                    except Exception as e:
                        error_msg = str(e)[:80]
                        if provider == "puter":
                            puter_failed = True
                        elif provider == "elevenlabs":
                            elevenlabs_failed = True

                    if audio_bytes:
                        temp_path.write_bytes(audio_bytes)
                    else:
                        if error_msg and i == 0:
                            print(f"  {error_msg}. Using stable edge-tts voice.")
                        comm = edge_tts.Communicate(
                            text=safe_line,
                            voice=fallback_voice,
                            rate=self.rate,
                            volume=self.volume,
                            pitch=self.pitch,
                        )
                        await asyncio.wait_for(comm.save(str(temp_path)), timeout=8)
                    
                    # Verify file was created with content
                    if temp_path.exists() and temp_path.stat().st_size > 500:
                        success = True
                        break
                    else:
                        await asyncio.sleep(0.3)
                except asyncio.TimeoutError:
                    print(f'  Line {i+1} timeout on attempt {attempt+1}')
                    await asyncio.sleep(0.5)
                except Exception as e:
                    error_str = str(e)[:80]
                    print(f'  Line {i+1} attempt {attempt+1} failed: {error_str}')
                    await asyncio.sleep(0.5)
            
            if not success:
                print(f'  Line {i+1} skipped: TTS failed')
                continue

            try:
                from src.audio.ffmpeg_ops import get_audio_duration
                duration_s = get_audio_duration(temp_path)
                if duration_s < 0.3:
                    print(f'  Line {i+1} too short ({duration_s:.2f}s), skipping')
                    continue
            except Exception as e:
                print(f'  Line {i+1} could not be read: {e}')
                continue

            line_audios.append((temp_path, line, duration_s))

        if not line_audios:
            return None

        from src.audio.ffmpeg_ops import trim_audio_silence, generate_silence, concat_audio_files

        gap_ms = 380
        gap_sec = gap_ms / 1000.0
        print(f'  Gap: {gap_ms}ms between lines')

        gap_path = temp_dir / f"{file_base}_gap_silence.mp3"
        generate_silence(gap_path, gap_sec)

        valid_audios = []
        subtitles = []
        current_time = 0.0

        print(f'  Building and trimming {len(line_audios)} lines')

        concat_list = []

        for i, (path, line, dur) in enumerate(line_audios):
            try:
                if not path.exists() or path.stat().st_size < 500:
                    print(f'  Skipping invalid file: {path.name}')
                    continue
                
                trimmed_path = temp_dir / f"{file_base}_trimmed_{i:03d}.mp3"
                trimmed_dur = trim_audio_silence(path, trimmed_path, threshold_db=-50.0)
                
                if trimmed_dur < 0.2:
                    print(f'  Skipping too-short audio after trimming: {path.name}')
                    continue
                    
                valid_audios.append((trimmed_path, line, trimmed_dur))
            except Exception as e:
                print(f'  Cannot process {path.name}: {e}')
                continue

        if not valid_audios:
            print('  ERROR: No valid audio files produced')
            return None

        for i, (trimmed_path, line, trimmed_dur) in enumerate(valid_audios):
            concat_list.append(trimmed_path)
            if i < len(valid_audios) - 1:
                concat_list.append(gap_path)

            subtitles.append({
                'text': line,
                'start': round(current_time, 3),
                'end': round(current_time + trimmed_dur, 3),
            })
            current_time += trimmed_dur + (gap_sec if i < len(valid_audios) - 1 else 0.0)

        final_audio = audio_dir / f'{file_base}.mp3'
        
        # Concatenate using ffmpeg
        concat_audio_files(concat_list, final_audio)

        # Clean studio audio loudness normalization (EBU R128 -16 LUFS)
        normalize_studio_audio(final_audio, target_lufs=-16.0)

        subs_path = subs_dir / f'{file_base}_subtitles.json'
        with open(subs_path, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, indent=2, ensure_ascii=False)

        # Cleanup temporary files (original line files, trimmed files, gap file)
        for path, _, _ in line_audios:
            try: path.unlink()
            except: pass
        for trimmed_path, _, _ in valid_audios:
            try: trimmed_path.unlink()
            except: pass
        try:
            gap_path.unlink()
        except:
            pass

        print(f'  PERFECT SYNC: {len(subtitles)} lines, total {current_time:.2f}s')

        return {
            'audio_path': str(final_audio),
            'subtitles_path': str(subs_path),
            'subtitles': subtitles,
            'timings_path': str(subs_path),
            'word_boundaries': [],
            'text': ' '.join(cleaned),
            'lines': cleaned,
        }

    async def generate_from_lines(self, lines, prefix='reel'):
        return await self.generate_per_line_synced(lines, prefix=prefix)


async def generate_voice(text, output_name=None, voice=None):
    engine = TTSEngine(voice=voice)
    return await engine.generate_voice(text, output_name=output_name)


def normalize_studio_audio(audio_path, target_lufs=-16.0):
    """
    Applies clean broadcast standard studio audio normalization (EBU R128 loudnorm).
    Guarantees consistent, punchy, distortion-free vocal levels without altering natural pitch, speed, or timbre.
    """
    import subprocess
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return False

    temp_output = audio_path.with_name(f"norm_{audio_path.name}")
    af_chain = f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11"

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-af", af_chain,
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(temp_output)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        if res.returncode == 0 and temp_output.exists() and temp_output.stat().st_size > 500:
            temp_output.replace(audio_path)
            return True
    except Exception as e:
        print(f"  Studio normalization note: {e}")
    return False


if __name__ == '__main__':
    async def test():
        print('')
        print('=' * 55)
        print('TTS ENGINE TEST - Per Line Perfect Sync')
        print('=' * 55)

        lines = [
            'God has not forgotten you.',
            'Even in your darkest moment.',
            'He sees every tear you have cried.',
            'Your breakthrough is coming.',
            'Share this with someone who needs it today.',
        ]

        engine = TTSEngine()
        result = await engine.generate_per_line_synced(lines, prefix='test_sync')

        if result:
            print(f'Audio:     {result["audio_path"]}')
            print(f'Subtitles: {result["subtitles_path"]}')
            print('')
            print('Subtitle preview:')
            for item in result['subtitles']:
                print(f'  {item["start"]}s -> {item["end"]}s | {item["text"]}')
        print('=' * 55)

    asyncio.run(test())
