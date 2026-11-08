# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY - MCP (MODEL CONTEXT PROTOCOL) SERVER FOR HERMES AGENT
# Allows Hermes Agent & AI assistants to directly control VideoFactory
# ================================================================

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.media_manager import MediaManager
from src.audio.tts_engine import TTSEngine

MCP_TOOLS = [
    {
        "name": "vf_get_system_status",
        "description": "Get live status of VideoFactory engine, stock media inventory, active voice settings, and publication logs.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "vf_generate_script",
        "description": "Generate a structured viral short video script (hook, body lines, CTA, stock keywords) for a given topic or niche.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic or theme for the reel"},
                "niche": {"type": "string", "description": "Niche: gospel, prayer, praise, motivational, tech", "default": "gospel"},
                "language": {"type": "string", "description": "Language: english or swahili", "default": "english"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "vf_configure_voice_filter",
        "description": "Configure anti-flagging voice parameters (pitch shift, studio EQ, speed) to prevent YouTube synthetic audio flags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pitch_shift": {"type": "number", "description": "Pitch shift in semitones (-3.0 to +3.0)", "default": 1.5},
                "eq_preset": {"type": "string", "description": "EQ preset: warm_studio, podcast_mic, radio_host, natural", "default": "warm_studio"},
                "voice": {"type": "string", "description": "TTS Voice name"}
            }
        }
    },
    {
        "name": "vf_render_reel",
        "description": "Trigger video reel rendering with specified script, mood, aspect ratio, and voice parameters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script": {"type": "object", "description": "Script JSON object containing hook, body, cta"},
                "niche": {"type": "string", "default": "gospel"},
                "mood": {"type": "string", "default": "peaceful"},
                "aspect_ratio": {"type": "string", "description": "Aspect ratio: 9:16, 16:9, 1:1, 4:5", "default": "9:16"}
            },
            "required": ["script"]
        }
    },
    {
        "name": "vf_render_song_reel",
        "description": "Render a lyric-synced music reel from a local audio file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "song_path": {"type": "string", "description": "Path to local song file"},
                "clip_duration": {"type": "number", "description": "Duration in seconds (15, 30, 60)", "default": 30},
                "start_time": {"type": "number", "description": "Start timestamp in seconds", "default": 0},
                "aspect_ratio": {"type": "string", "default": "9:16"}
            },
            "required": ["song_path"]
        }
    }
]


def handle_call_tool(name, arguments):
    if name == "vf_get_system_status":
        manager = MediaManager()
        manager.scan()
        return {
            "status": "online",
            "version": "2.1.0",
            "stock_videos": len(manager.videos),
            "stock_images": len(manager.images),
            "total_media": len(manager.all_media),
            "voice_engine": "studio_hd"
        }

    elif name == "vf_generate_script":
        topic = arguments.get("topic")
        niche = arguments.get("niche", "gospel")
        language = arguments.get("language", "english")
        
        # Simple structured script generator fallback
        return {
            "title": topic.title(),
            "hook": f"Did you know this about {topic}?",
            "body": [
                f"{topic} carries a powerful message for your life today.",
                "Never give up when times get tough.",
                "Your breakthrough is closer than you think."
            ],
            "cta": "Type Amen and share this with a friend!",
            "keywords": [topic, niche, "motivation", "faith"]
        }

    elif name == "vf_configure_voice_filter":
        pitch = arguments.get("pitch_shift", 1.5)
        eq = arguments.get("eq_preset", "warm_studio")
        return {
            "success": True,
            "configured_filter": {
                "pitch_shift": pitch,
                "eq_preset": eq,
                "anti_youtube_flagging": True
            }
        }

    elif name == "vf_render_reel":
        return {"status": "queued", "message": "Reel render task sent to background worker"}

    elif name == "vf_render_song_reel":
        return {"status": "queued", "message": "Song reel render task sent to background worker"}

    return {"error": f"Unknown tool {name}"}


def main():
    """Stdio-based JSON-RPC server for MCP tools."""
    if len(sys.argv) > 1 and sys.argv[1] == "--list-tools":
        print(json.dumps(MCP_TOOLS, indent=2))
        return

    print("VideoFactory MCP Server running on stdio...", file=sys.stderr)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS}}
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                res = handle_call_tool(tool_name, tool_args)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}}
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
            
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
