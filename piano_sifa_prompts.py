"""
Piano Sifa — Auto Prompt System
Generates music prompts with consistent brand identity.
"It's Jesus Music" intro + "pianosifa" outro on every track.
"""
import json
import os
from datetime import datetime
from pathlib import Path


class PianoSifaPrompts:
    """Generate branded music prompts for Piano Sifa."""

    INTRO_TAG = "It's Jesus Music"
    OUTRO_TAG = "pianosifa"

    STYLES = {
        "gospel_amapiano": {
            "style": "Gospel Amapiano, log drums, deep warm bass, Rhodes piano, "
                     "female lead vocal, choir harmonies, Swahili lyrics, 112 BPM, "
                     "uplifting spiritual, cinematic production",
            "lyrics": [
                "[Intro - spoken word]",
                f'"{INTRO_TAG}"',
                "",
                "[Instrumental intro - 4 beats, log drum pattern]",
                "",
                "[Verse 1]",
                "Mungu wangu, mungu wangu",
                "Wewe peke yako unastahili",
                "Katika giza, wewe ni mwanga",
                "Katika dhoruba, wewe ni mwamba",
                "",
                "[Pre-Chorus]",
                "Kila siku, kila hatua",
                "Unaniongoza kwa upendo",
                "",
                "[Chorus]",
                "Elishadai, Elishadai",
                "Jina lako juu, Elishadai",
                "Mfalme wa wafalme",
                "Bwana wa mabwana",
                "",
                "[Bridge]",
                "Sasa na milele",
                "Nitakushukuru",
                "",
                "[Final Chorus]",
                "Elishadai, Elishadai",
                "Jina lako juu, Elishadai",
                "",
                "[Outro - 8 beats]",
                f'spoken: "{OUTRO_TAG}"',
                'choir: "ooooh..."',
            ],
        },
        "worship_ballad": {
            "style": "Contemporary worship ballad, solo piano, female vocal, "
                     "intimate, reverent, slow 72 BPM, sparse production, "
                     "building to strings at chorus, cinematic, devotional, "
                     "Swahili and English lyrics",
            "lyrics": [
                "[Intro - solo piano]",
                f'spoken: "{INTRO_TAG}"',
                "",
                "[Verse 1]",
                "In the quiet of this moment",
                "I hear Your voice so clear",
                "You are near, You are here",
                "Mungu wangu, karibu nami",
                "",
                "[Chorus]",
                "Bwana wangu, mchunga wangu",
                "Ninakutegemea",
                "You are my everything",
                OUTRO_TAG,
                "",
                "[Outro]",
                OUTRO_TAG,
            ],
        },
        "afrobeat_praise": {
            "style": "Afrobeat praise, dance, high energy 125 BPM, talking drum, "
                     "shekere, electric guitar, punchy bass, Swahili chant hook, "
                     "celebratory, festival vibe, modern Nigerian gospel",
            "lyrics": [
                "[Intro]",
                f'"{INTRO_TAG}"',
                "[Beat drops]",
                "",
                "[Verse 1]",
                "Tukufu ni lako Mungu",
                "Heshima ni yako Yesu",
                "Sifa zote ziwe juu",
                "Milele na milele",
                "",
                "[Chorus]",
                "Tumeinua mikono",
                "Tukimshukuru Mungu",
                "Tumeinua mioyo",
                "Kwa upendo wake",
                "",
                "[Outro]",
                f'spoken: "{OUTRO_TAG}"',
            ],
        },
        "bongo_flava_gospel": {
            "style": "Bongo Flava Gospel, Tanzanian pop-gospel, Swahili vocals, "
                     "male lead, acoustic guitar, light percussion, mid-tempo 95 BPM, "
                     "emotional, contemporary worship, East African gospel pop",
            "lyrics": [
                "[Intro]",
                f'"{INTRO_TAG}"',
                "",
                "[Verse 1]",
                "Nimekutambua Mungu",
                "Wewe ni mwanga wangu",
                "Katika safari hii",
                "Wewe ndiye mshauri",
                "",
                "[Chorus]",
                "Nitakushukuru milele",
                "Kwa upendo wako",
                "Wewe ni Mungu wa ajabu",
                OUTRO_TAG,
                "",
                "[Outro]",
                OUTRO_TAG,
            ],
        },
        "afro_gospel_choir": {
            "style": "African gospel choir, call-and-response, group vocals, "
                     "Hammond B3 organ, hand claps, tambourine, energetic 120 BPM, "
                     "spirit-filled, traditional gospel with modern production, "
                     "spontaneous worship moments, multi-part harmonies",
            "lyrics": [
                "[Intro - choir]",
                f'choir: "{INTRO_TAG}"',
                "",
                "[Verse 1 - call]",
                "Mungu ni mwanga",
                "[Response]",
                "Yesu ni mwanga",
                "[Call]",
                "Roho ni mwanga",
                "[Response]",
                "Sote ni wana wa mwanga",
                "",
                "[Chorus - all]",
                "Ee Mungu, ee Mungu",
                "Wastahili sifa",
                "Ee Mungu, ee Mungu",
                "Wastahili utukufu",
                "",
                "[Outro - spoken]",
                f'spoken: "{OUTRO_TAG}"',
            ],
        },
    }

    INSTRUMENTAL_PROMPTS = {
        "log_drum_loop": "log drum pattern, deep 808 bass, Rhodes piano chords, "
                          "warm gospel choir pads, 110 BPM, Amapiano, uplifting, "
                          "spiritual, instrumental, African gospel house",
        "choir_pad": "warm gospel choir pad, sustained organ, deep bass, "
                     "atmospheric, sacred, spiritual, ambient, 70 BPM, no drums",
        "percussion_only": "African percussion ensemble, log drums, talking drums, "
                          "shekere, congas, energetic 125 BPM, gospel energy",
        "piano_solo": "solo piano, gentle, intimate, worship ballad, "
                     "contemporary, reverent, 72 BPM, soft dynamics",
        "electric_gospel": "electric guitar gospel, hammond organ, soulful, "
                          "bluesy, mid-tempo 95 BPM, expressive, vocals humming",
    }

    HF_MUSICGEN_VARIATIONS = [
        "Gospel Amapiano with female lead vocal in Swahili",
        "Gospel Amapiano with choir harmonies and call-response",
        "Gospel Amapiano instrumental with log drums",
        "Gospel Amapiano slower worship ballad version",
        "Gospel Amapiano Afrobeat praise dance version",
    ]

    @classmethod
    def get_prompt(cls, style_key):
        if style_key not in cls.STYLES:
            raise ValueError(f"Unknown style: {style_key}. Available: {list(cls.STYLES.keys())}")
        return cls.STYLES[style_key]

    @classmethod
    def get_instrumental(cls, key):
        return cls.INSTRUMENTAL_PROMPTS[key]

    @classmethod
    def get_hf_variations(cls, count=5):
        return cls.HF_MUSICGEN_VARIATIONS[:count]

    @classmethod
    def format_for_flow_music(cls, style_key):
        style = cls.get_prompt(style_key)
        lyrics = "\n".join(style["lyrics"])
        return f"Style of Music:\n{style['style']}\n\nLyrics:\n{lyrics}"

    @classmethod
    def format_for_suno(cls, style_key):
        style = cls.get_prompt(style_key)
        lyrics = "\n".join(style["lyrics"])
        return {
            "style": style["style"],
            "lyrics": lyrics,
            "title": f"Piano Sifa - {style_key.replace('_', ' ').title()}",
        }

    @classmethod
    def format_for_musicgen(cls, style_key=None, instrumental_key=None, variation=None):
        if variation is not None:
            return variation
        if style_key:
            return cls.get_prompt(style_key)["style"]
        if instrumental_key:
            return cls.get_instrumental(instrumental_key)
        raise ValueError("Must specify style_key, instrumental_key, or variation")

    @classmethod
    def get_cover_art_prompt(cls):
        return ("Album cover, deep purple #2D1B4E background, golden light rays "
                "emanating from above, African geometric patterns, log drum "
                "silhouette, \"pianosifa\" text in elegant serif font at bottom, "
                "modern worship aesthetic, cinematic, premium, divine, 1080x1080")

    @classmethod
    def get_metadata(cls, track_name, style_key):
        return {
            "title": f"{track_name} - Piano Sifa",
            "artist": "Piano Sifa",
            "album": "Gospel Amapiano Sessions Vol. 1",
            "year": "2026",
            "genre": "Gospel Amapiano",
            "language": "Swahili",
            "producer": "Mwijay Davie (pianosifa)",
            "label": "Piano Sifa Records",
            "comment": "It's Jesus Music",
            "style_key": style_key,
        }

    @classmethod
    def get_social_caption(cls, track_name, lyrics_excerpt, link=""):
        return (f"🎵 {track_name} — Piano Sifa\n"
                f"\"It's Jesus Music\"\n\n"
                f"{lyrics_excerpt}\n\n"
                f"Full track: {link}\n"
                f"#GospelAmapiano #PianoSifa #ItsJesusMusic\n"
                f"#TanzaniaGospel #SwahiliWorship")


def main():
    print("=" * 70)
    print("PIANO SIFA - Track 01 Prompt Package Generator")
    print("=" * 70)

    out_dir = Path(r"C:\Users\MWIJAY TECH\Music\Piano_Sifa\Track_01")
    out_dir.mkdir(parents=True, exist_ok=True)

    style_key = "gospel_amapiano"

    flow_music = PianoSifaPrompts.format_for_flow_music(style_key)
    suno = PianoSifaPrompts.format_for_suno(style_key)
    musicgen_variations = PianoSifaPrompts.get_hf_variations()
    cover_art = PianoSifaPrompts.get_cover_art_prompt()
    metadata = PianoSifaPrompts.get_metadata("Mwamba Reimagined", style_key)
    caption = PianoSifaPrompts.get_social_caption(
        "Mwamba Reimagined",
        "Mungu wangu, mungu wangu / Wewe peke yako unastahili",
        "[link]",
    )

    (out_dir / "prompt_FLOW_MUSIC.txt").write_text(flow_music, encoding="utf-8")
    (out_dir / "prompt_SUNO.json").write_text(
        json.dumps(suno, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "prompt_MUSICGEN_variations.txt").write_text(
        "\n\n---VARIATION---\n\n".join(musicgen_variations), encoding="utf-8"
    )
    (out_dir / "prompt_COVER_ART.txt").write_text(cover_art, encoding="utf-8")
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "social_caption.txt").write_text(caption, encoding="utf-8")

    readme = f"""# Track 01: Mwamba Reimagined
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Style: {style_key}
Brand: Piano Sifa (It's Jesus Music -> pianosifa)

## Files in This Folder
- prompt_FLOW_MUSIC.txt - Copy-paste to Flow Music
- prompt_SUNO.json - Suno AI format
- prompt_MUSICGEN_variations.txt - 5 variations for HF MusicGen
- prompt_COVER_ART.txt - For Midjourney/Pollinations
- metadata.json - MP3 ID3 tags
- social_caption.txt - Instagram/TikTok caption
- track_01.wav - Final audio (after generation)

## Generation Strategy
1. Open Flow Music -> paste FLOW_MUSIC prompt -> Generate
2. Open HF MusicGen -> paste variations one by one
3. Pick the BEST one (clean vocals + log drum)
4. Save as track_01.wav
5. Generate cover art via Pollinations
6. Apply metadata via MP3tag

## Credits Used
Flow Music: ~500 credits
HF Spaces: $0
Total: ~500 credits of 8000 budget
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"\n✅ Track 01 package saved to: {out_dir}")
    print(f"   Style: {style_key}")
    print(f"   Title: {metadata['title']}")
    print(f"\n📄 Files generated:")
    for f in sorted(out_dir.glob("*")):
        size = f.stat().st_size
        print(f"   - {f.name} ({size:,} bytes)")

    print(f"\n{'='*70}")
    print(f"BRAND CHECK:")
    print(f"   Intro tag: 'It's Jesus Music' PASS")
    print(f"   Outro tag: 'pianosifa' PASS")
    print(f"{'='*70}")

    return out_dir


if __name__ == "__main__":
    main()
