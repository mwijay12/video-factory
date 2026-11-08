# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import httpx
from pathlib import Path

# Add project root to sys.path so we can import modules
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import config.settings
from main import generate_narration_reel

TOKEN = getattr(config.settings, "TELEGRAM_BOT_TOKEN", "")

async def get_bot_updates(offset=0):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 30}
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.get(url, params=params)
            if r.status_code == 200:
                return r.json().get("result", [])
    except Exception as e:
        print(f"Error checking updates: {e}")
    return []

async def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

async def send_video(chat_id, video_path, caption="Here is your VideoFactory Reel! 🎬"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    try:
        # Increase timeout for uploading large video files
        async with httpx.AsyncClient(timeout=180) as client:
            with open(video_path, "rb") as f:
                files = {"video": f}
                data = {"chat_id": chat_id, "caption": caption}
                r = await client.post(url, data=data, files=files)
                if r.status_code != 200:
                    print(f"Failed to upload video: {r.status_code} - {r.text}")
                    await send_message(chat_id, f"❌ Failed to upload video file (Status {r.status_code}).")
    except Exception as e:
        print(f"Error sending video: {e}")
        await send_message(chat_id, f"❌ Upload error: {e}")

async def process_command(chat_id, text):
    parts = text.split()
    cmd = parts[0].lower()
    
    if cmd == "/start" or cmd == "/help":
        help_text = (
            "<b>Welcome to VideoFactory Bot!</b> 🎬\n\n"
            "Use the following commands to generate Reels on the fly:\n"
            "• <code>/generate gospel</code> - Gospel reel (English)\n"
            "• <code>/generate swahili</code> - Gospel reel (Swahili)\n"
            "• <code>/generate motivational</code> - Motivational reel\n"
            "• <code>/generate tech</code> - Tech reel\n"
            "• <code>/status</code> - Check bot configuration and key stats"
        )
        await send_message(chat_id, help_text)
        
    elif cmd == "/status":
        import config.settings
        import importlib
        importlib.reload(config.settings)
        
        status_text = (
            "🟢 <b>VideoFactory Status</b>\n\n"
            f"• <b>Active Voice:</b> <code>{getattr(config.settings, 'ACTIVE_VOICE', 'default')}</code>\n"
            f"• <b>TTS Provider:</b> <code>{getattr(config.settings, 'TTS_PROVIDER', 'edge-tts')}</code>\n"
            f"• <b>ElevenLabs Keys:</b> <code>{len(getattr(config.settings, 'ELEVENLABS_KEYS', []))}</code> loaded\n"
            f"• <b>Groq Keys:</b> <code>{len(getattr(config.settings, 'GROQ_KEYS', []))}</code> loaded\n"
            f"• <b>OpenRouter Keys:</b> <code>{len(getattr(config.settings, 'OPENROUTER_KEYS', []))}</code> loaded\n"
            f"• <b>Ollama Keys:</b> <code>{len(getattr(config.settings, 'OLLAMA_KEYS', []))}</code> loaded"
        )
        await send_message(chat_id, status_text)
        
    elif cmd == "/generate":
        niche = "gospel"
        lang = "english"
        
        if len(parts) > 1:
            niche = parts[1].lower()
            
        if niche == "swahili":
            niche = "gospel"
            lang = "swahili"
            
        if niche not in ["gospel", "motivational", "tech", "swahili"]:
            await send_message(chat_id, f"⚠️ Unknown niche: <i>{niche}</i>. Using <i>gospel</i>.")
            niche = "gospel"
            
        await send_message(chat_id, f"🚀 <b>Starting video generation...</b>\nNiche: <code>{niche}</code>\nLanguage: <code>{lang}</code>\n\nThis will take about 1-2 minutes. Please wait...")
        
        try:
            # Run the generator pipeline programmatically in a separate executor thread to avoid blocking polling
            loop = asyncio.get_running_loop()
            output_path = await loop.run_in_executor(
                None, 
                lambda: asyncio.run(
                    generate_narration_reel(
                        niche=niche, 
                        language=lang, 
                        use_ai=True
                    )
                )
            )
            
            if output_path and Path(output_path).exists():
                await send_message(chat_id, "📤 <b>Uploading your video...</b>")
                caption = f"🎬 <b>VideoFactory Reel</b>\nNiche: {niche}\nLanguage: {lang}\nFile: {Path(output_path).name}"
                await send_video(chat_id, output_path, caption)
            else:
                await send_message(chat_id, "❌ Error: Video render finished but output file was not found.")
        except Exception as e:
            print(f"Generation error: {e}")
            await send_message(chat_id, f"❌ <b>Generation Failed!</b>\nError:\n<code>{str(e)[:400]}</code>")
            
    else:
        await send_message(chat_id, "❓ Unknown command. Send /help to see all available commands.")

async def bot_loop():
    if not TOKEN:
        print("Telegram token is not set. Please update your .env file.")
        return
        
    print("Telegram Bot started! Press Ctrl+C to exit.")
    offset = 0
    while True:
        try:
            updates = await get_bot_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "").strip()
                
                if not text or not chat_id:
                    continue
                    
                print(f"Received message: '{text}' from Chat ID: {chat_id}")
                await process_command(chat_id, text)
        except Exception as e:
            print(f"Error in main polling loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(bot_loop())
    except KeyboardInterrupt:
        print("\nBot stopped.")
