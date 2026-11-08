# -*- coding: utf-8 -*-
"""
src/utils/asset_credits.py — VideoFactory Asset Credits Tracker

Creates a .credits.json sidecar file for every generated video, recording:
  - Which stock clips/images were used (source, license, duration)
  - Which TTS voice & provider generated the audio
  - Which background music track was used
  - Which AI model wrote the script

Usage:
    from src.utils.asset_credits import CreditsBuilder

    builder = CreditsBuilder(video_name="web_gospel_20260629.mp4", niche="gospel", language="swahili")
    builder.add_video_clip(filepath="assets/stock/gospel/sunrise.mp4", source="pexels", duration=3.2)
    builder.add_tts_audio(provider="edge-tts", voice="sw-TZ-RehemaNeural", text="Mungu hakusahau...")
    builder.add_music(filepath="assets/music/piano_sifa_01.mp3", source="local", license="CC-BY-4.0")
    builder.set_script_model(provider="groq", model="llama-3.3-70b-versatile")
    builder.save()  # writes output/videos/web_gospel_20260629.credits.json
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

OUTPUT_VIDEOS = Path("output/videos")


class CreditsBuilder:
    """
    Collects asset usage metadata for a single video and writes it to a JSON sidecar file.

    Args:
        video_name: The filename of the rendered video (e.g. "web_gospel_20260629.mp4")
        niche:      Content niche ("gospel", "motivational", "prayer", etc.)
        language:   Primary language ("swahili", "english")
    """

    def __init__(self, video_name: str, niche: str = "gospel", language: str = "swahili"):
        self.video_name = video_name
        self.niche = niche
        self.language = language
        self._assets: list[dict] = []
        self._ai_models: dict = {}
        self._created_at = datetime.now(timezone.utc).isoformat()

    # ─── Asset Registration ──────────────────────────────────────────────────

    def add_video_clip(
        self,
        filepath: str,
        source: str = "local",
        asset_id: Optional[str] = None,
        url: Optional[str] = None,
        duration_used: float = 0.0,
        license: str = "unknown",
    ) -> "CreditsBuilder":
        """Register a video B-roll clip."""
        self._assets.append({
            "type": "video",
            "source": source,
            "id": asset_id,
            "url": url,
            "license": _resolve_license(source, license),
            "duration_used_sec": round(duration_used, 2),
            "filepath": str(filepath),
        })
        return self

    def add_image(
        self,
        filepath: str,
        source: str = "local",
        asset_id: Optional[str] = None,
        url: Optional[str] = None,
        license: str = "unknown",
    ) -> "CreditsBuilder":
        """Register an image asset."""
        self._assets.append({
            "type": "image",
            "source": source,
            "id": asset_id,
            "url": url,
            "license": _resolve_license(source, license),
            "filepath": str(filepath),
        })
        return self

    def add_tts_audio(
        self,
        provider: str,
        voice: str,
        text: str = "",
        language: Optional[str] = None,
    ) -> "CreditsBuilder":
        """Register TTS audio generation details."""
        self._assets.append({
            "type": "audio",
            "source": "tts",
            "provider": provider,
            "voice": voice,
            "language": language or self.language,
            "text_preview": text[:80] + "..." if len(text) > 80 else text,
        })
        return self

    def add_music(
        self,
        filepath: str,
        source: str = "local",
        license: str = "CC-BY-4.0",
        artist: Optional[str] = None,
        title: Optional[str] = None,
    ) -> "CreditsBuilder":
        """Register background music track."""
        entry = {
            "type": "music",
            "source": source,
            "license": _resolve_license(source, license),
            "filepath": str(filepath),
        }
        if artist:
            entry["artist"] = artist
        if title:
            entry["title"] = title
        self._assets.append(entry)
        return self

    def set_script_model(self, provider: str, model: str) -> "CreditsBuilder":
        """Record the AI model that generated the script."""
        self._ai_models["script_llm"] = f"{provider}/{model}"
        return self

    def set_tts_model(self, provider: str, voice: str) -> "CreditsBuilder":
        """Record the primary TTS provider/voice at the model level."""
        self._ai_models["voice_tts"] = f"{provider}/{voice}"
        return self

    # ─── Output ──────────────────────────────────────────────────────────────

    def build(self) -> dict:
        """Return the credits dict without writing to disk."""
        return {
            "video": self.video_name,
            "created_at": self._created_at,
            "niche": self.niche,
            "language": self.language,
            "assets": self._assets,
            "ai_models": self._ai_models,
            "videofactory_version": "2.0",
        }

    def save(self, output_dir: Optional[Path] = None) -> Path:
        """
        Write the credits JSON sidecar next to the video file.

        Returns the path of the written .credits.json file.
        """
        out_dir = output_dir or OUTPUT_VIDEOS
        out_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(self.video_name).stem
        out_path = out_dir / f"{stem}.credits.json"
        data = self.build()

        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path


# ─── Helpers ──────────────────────────────────────────────────────────────────

_LICENSE_MAP = {
    "pexels":   "Pexels License (free for commercial use, attribution not required)",
    "pixabay":  "Pixabay License (free for commercial use, no attribution required)",
    "local":    "Internal Asset (all rights reserved)",
    "tts":      "TTS Audio (synthesized, no license required)",
    "piano_sifa": "Piano Sifa — Mwijay Davie (internal, all rights reserved)",
}

def _resolve_license(source: str, fallback: str = "unknown") -> str:
    return _LICENSE_MAP.get(source.lower(), fallback)


def load_credits(video_name_or_path: str) -> Optional[dict]:
    """
    Load a .credits.json file for a given video name or path.

    Returns the credits dict, or None if the file doesn't exist.
    """
    p = Path(video_name_or_path)
    # If a full path to .mp4, look for .credits.json in same folder
    if p.suffix.lower() == ".mp4":
        credits_path = p.parent / (p.stem + ".credits.json")
    elif p.suffix.lower() == ".json":
        credits_path = p
    else:
        # Try in output/videos/
        credits_path = OUTPUT_VIDEOS / (Path(video_name_or_path).stem + ".credits.json")

    if not credits_path.exists():
        return None

    return json.loads(credits_path.read_text(encoding="utf-8"))


def list_all_credits() -> list[dict]:
    """
    Returns a list of all .credits.json files found in output/videos/.
    """
    if not OUTPUT_VIDEOS.exists():
        return []
    credits = []
    for f in sorted(OUTPUT_VIDEOS.glob("*.credits.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            credits.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return credits


if __name__ == "__main__":
    # Quick test
    b = CreditsBuilder("test_gospel_20260629.mp4", niche="gospel", language="swahili")
    b.add_video_clip("assets/stock/gospel/sunrise.mp4", source="pexels", asset_id="1234567",
                     url="https://pexels.com/video/1234567", duration_used=3.2)
    b.add_tts_audio(provider="edge-tts", voice="sw-TZ-RehemaNeural",
                    text="Mungu hakusahau. Amini Yeye leo.")
    b.add_music("assets/music/piano_sifa_01.mp3", source="piano_sifa",
                artist="Mwijay Davie", title="Piano Sifa Vol.1")
    b.set_script_model("groq", "llama-3.3-70b-versatile")
    b.set_tts_model("edge-tts", "sw-TZ-RehemaNeural")

    import pprint
    pprint.pprint(b.build())
    print("\nTest passed.")
