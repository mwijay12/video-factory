"""
Piano Sifa — Hugging Face Inference API Generator
Uses HF Inference API to call MusicGen without local install.
Free tier: ~1000 calls/month.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import base64
from pathlib import Path
from datetime import datetime

# Try to use huggingface_hub if available (best)
try:
    from huggingface_hub import InferenceClient
    HAS_HF_HUB = True
except ImportError:
    HAS_HF_HUB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


HF_API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-large"


class PianoSifaHFGenerator:
    """Generate Piano Sifa tracks via Hugging Face Inference API."""

    VARIATIONS = [
        "Gospel Amapiano with female lead vocal in Swahili",
        "Gospel Amapiano with choir harmonies and call-response",
        "Gospel Amapiano instrumental with log drums",
        "Gospel Amapiano slower worship ballad version",
        "Gospel Amapiano Afrobeat praise dance version",
    ]

    def __init__(self, hf_token=None):
        self.hf_token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        if not self.hf_token:
            print("⚠️  No HF_TOKEN found. Using free tier (rate limited).")
            print("   Get a free token at: https://huggingface.co/settings/tokens")
        else:
            print(f"✅ HF token found (length: {len(self.hf_token)})")

    def generate(self, prompt, duration=15, output_path=None):
        """Generate audio via HF Inference API.
        
        Args:
            prompt: text description of music
            duration: seconds (5-30 typical)
            output_path: where to save WAV (optional)
        
        Returns:
            bytes of audio or None
        """
        if not HAS_REQUESTS:
            print("❌ requests library not installed. pip install requests")
            return None

        headers = {}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": int(duration * 50),  # MusicGen uses ~50 tokens/sec
                "do_sample": True,
                "temperature": 1.0,
                "top_k": 250,
            }
        }

        try:
            print(f"  Calling MusicGen API...")
            print(f"  Prompt: {prompt[:80]}...")
            print(f"  Duration: {duration}s")
            
            response = requests.post(
                HF_API_URL,
                headers=headers,
                json=payload,
                timeout=120,
            )

            if response.status_code == 200:
                audio_bytes = response.content
                print(f"  ✅ Got {len(audio_bytes):,} bytes")
                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(audio_bytes)
                    print(f"  💾 Saved: {output_path}")
                return audio_bytes
            elif response.status_code == 503:
                print(f"  ⏳ Model loading (cold start)... retry in 30s")
                time.sleep(30)
                return self.generate(prompt, duration, output_path)
            else:
                print(f"  ❌ Error {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            return None

    def generate_variations(self, output_dir, count=3, duration=15):
        """Generate multiple variations for A/B testing."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i in range(min(count, len(self.VARIATIONS))):
            prompt = self.VARIATIONS[i]
            print(f"\n[Variation {i+1}/{count}]")
            output_path = out_dir / f"variation_{i+1:02d}_{datetime.now().strftime('%H%M%S')}.wav"
            audio = self.generate(prompt, duration, output_path)
            results.append({
                "index": i + 1,
                "prompt": prompt,
                "path": str(output_path) if output_path.exists() else None,
                "size": len(audio) if audio else 0,
                "success": audio is not None,
            })
            time.sleep(2)  # Be nice to API

        return results


def main():
    print("=" * 70)
    print("PIANO SIFA - HF MusicGen Generator (Inference API)")
    print("=" * 70)

    generator = PianoSifaHFGenerator()

    out_dir = Path(r"C:\Users\MWIJAY TECH\Music\Piano_Sifa\Track_01\HF_Variations")
    print(f"\n📂 Output: {out_dir}")

    print("\n🎵 Generating 3 variations...")
    results = generator.generate_variations(out_dir, count=3, duration=10)

    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} Variation {r['index']}: {r['size']:,} bytes")
        print(f"      {r['prompt']}")
        if r["path"]:
            print(f"      File: {r['path']}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\n✅ {success_count}/{len(results)} variations generated successfully")

    if success_count == 0:
        print("\n💡 If 0 succeeded, possible reasons:")
        print("   1. HF token missing — get free token: https://huggingface.co/settings/tokens")
        print("   2. Rate limit hit — wait 1 hour")
        print("   3. Model loading — first call takes ~30s")
        print("   4. Use browser-based HF Spaces instead (no token needed)")


if __name__ == "__main__":
    main()
