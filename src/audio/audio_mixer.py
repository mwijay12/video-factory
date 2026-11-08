# ============================================================
# VIDEOFACTORY - AUDIO MIXER
# Handles all audio mixing for reels
# - Voice + Background music
# - Volume ducking (music goes quiet when voice speaks)
# - Fade in / Fade out
# - Audio normalization
# - Supports any mp3/wav/m4a
# ============================================================

import os
import random
import time
from pathlib import Path

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    concatenate_audioclips,
)

from config.settings import (
    OUTPUT_DIR,
    BACKGROUND_MUSIC_ENABLED,
    BACKGROUND_MUSIC_VOLUME,
    MUSIC_FADE_IN_MS,
    MUSIC_FADE_OUT_MS,
)


# ============================================================
# HELPERS
# ============================================================

def now_stamp():
    return time.strftime("%Y%m%d_%H%M%S")


def ensure_output():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def get_audio_duration(path):
    try:
        clip = AudioFileClip(str(path))
        dur = clip.duration
        clip.close()
        return dur
    except Exception:
        return 0.0

def apply_dynamic_rms_ducking(voice_path, music_path, output_path, ducking_db=-14):
    """Monitors vocal RMS amplitude and smoothly attenuates music during active speech without clicking artifacts."""
    try:
        from pydub import AudioSegment
        voice = AudioSegment.from_file(str(voice_path))
        music = AudioSegment.from_file(str(music_path))
        
        if len(music) < len(voice):
            music = music * (len(voice) // len(music) + 1)
        music = music[:len(voice)]
        
        chunk_ms = 120
        ducked_music = AudioSegment.empty()
        current_duck = 0.0
        target_duck = 0.0
        
        for i in range(0, len(voice), chunk_ms):
            v_chunk = voice[i:i+chunk_ms]
            m_chunk = music[i:i+chunk_ms]
            
            if v_chunk.rms > 350:
                target_duck = float(abs(ducking_db))
            else:
                target_duck = 0.0
                
            # Smooth exponential moving average for gain to prevent abrupt zipper clicks
            current_duck = current_duck * 0.60 + target_duck * 0.40
            
            if current_duck > 0.5:
                ducked_music += m_chunk.lower_db(current_duck)
            else:
                ducked_music += m_chunk
                
        final_mix = ducked_music.overlay(voice)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        final_mix.export(str(output_path), format="mp3")
        print(f"  [PyDub RMS Audio Ducking] Exported smoothed dynamic mix -> {Path(output_path).name}")
        return str(output_path)
    except Exception as e:
        print(f"  Dynamic ducking warning (falling back to MoviePy): {e}")
        return None


def safe_volume(clip, factor):
    try:
        return clip.with_volume_scaled(factor)
    except Exception:
        try:
            return clip.volumex(factor)
        except Exception:
            return clip


# ============================================================
# AUDIO MIXER CLASS
# ============================================================

class AudioMixer:

    def __init__(self):
        ensure_output()

    def loop_music_to_duration(self, music_clip, target_duration):
        if music_clip.duration >= target_duration:
            return music_clip.subclipped(0, target_duration)

        loops = []
        accumulated = 0.0

        while accumulated < target_duration:
            remaining = target_duration - accumulated
            if music_clip.duration <= remaining:
                loops.append(music_clip)
                accumulated += music_clip.duration
            else:
                loops.append(music_clip.subclipped(0, remaining))
                accumulated = target_duration

        return concatenate_audioclips(loops)

    def mix_voice_and_music(
        self,
        voice_path,
        music_path,
        output_name=None,
        music_volume=None,
        fade_in_ms=None,
        fade_out_ms=None,
    ):
        voice_path = Path(voice_path)
        music_path = Path(music_path)

        if not voice_path.exists():
            print(f"Voice file not found: {voice_path}")
            return str(voice_path)

        if not music_path.exists():
            print(f"Music file not found: {music_path}")
            return str(voice_path)

        music_vol = music_volume or BACKGROUND_MUSIC_VOLUME
        fade_in = (fade_in_ms or MUSIC_FADE_IN_MS) / 1000
        fade_out = (fade_out_ms or MUSIC_FADE_OUT_MS) / 1000

        if not output_name:
            output_name = f"mixed_{now_stamp()}.mp3"

        output_path = Path(OUTPUT_DIR) / output_name

        print("")
        print(f"Mixing audio:")
        print(f"  Voice: {voice_path.name}")
        print(f"  Music: {music_path.name}")
        print(f"  Music volume: {music_vol}")

        try:
            voice = AudioFileClip(str(voice_path))
            music = AudioFileClip(str(music_path))
            total_duration = voice.duration

            # Loop music to match voice duration
            music = self.loop_music_to_duration(music, total_duration)

            # Set music volume
            music = safe_volume(music, music_vol)

            # Apply fades to music
            if fade_in > 0 and hasattr(music, 'audio_fadein'):
                music = music.audio_fadein(fade_in)
            if fade_out > 0 and hasattr(music, 'audio_fadeout'):
                music = music.audio_fadeout(fade_out)

            # Composite
            mixed = CompositeAudioClip([music, voice])
            mixed = mixed.with_duration(total_duration)

            # Export
            mixed.write_audiofile(
                str(output_path),
                fps=44100,
                logger=None,
            )

            voice.close()
            music.close()
            mixed.close()

            size_kb = output_path.stat().st_size / 1024
            print(f"  Mixed: {output_path.name} ({size_kb:.0f} KB)")
            return str(output_path)

        except Exception as e:
            print(f"Mixing failed: {e}")
            return str(voice_path)

    def normalize_audio(self, audio_path, output_name=None):
        audio_path = Path(audio_path)

        if not output_name:
            output_name = f"norm_{audio_path.stem}.mp3"

        output_path = Path(OUTPUT_DIR) / output_name

        try:
            clip = AudioFileClip(str(audio_path))
            clip.write_audiofile(str(output_path), fps=44100, logger=None)
            clip.close()
            return str(output_path)
        except Exception as e:
            print(f"Normalize failed: {e}")
            return str(audio_path)

    def extract_audio_from_video(self, video_path, output_name=None):
        video_path = Path(video_path)

        if not output_name:
            output_name = f"{video_path.stem}_audio.mp3"

        output_path = Path(OUTPUT_DIR) / output_name

        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(str(video_path))
            if clip.audio:
                clip.audio.write_audiofile(str(output_path), logger=None)
                print(f"Audio extracted: {output_path.name}")
            clip.close()
            return str(output_path)
        except Exception as e:
            print(f"Extraction failed: {e}")
            return None


# ============================================================
# SONG LYRICS EXTRACTOR (uses Whisper AI)
# This is for your piano songs - extracts lyrics + timestamps
# ============================================================

class LyricsExtractor:

    def __init__(self):
        self.model = None
        self.model_size = "base"

    def load_model(self, size="base"):
        print(f"Loading Whisper model ({size})...")
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(size, device="cpu", compute_type="int8")
            self.model_size = size
            print(f"Whisper model loaded!")
            return True
        except ImportError:
            print("faster-whisper not installed")
            print("Run: pip install faster-whisper")
            return False
        except Exception as e:
            print(f"Model load failed: {e}")
            return False

    def extract_lyrics(self, audio_path, language=None):
        audio_path = Path(audio_path)

        if not audio_path.exists():
            print(f"Audio not found: {audio_path}")
            return []

        if not self.model:
            loaded = self.load_model()
            if not loaded:
                return []

        print(f"Extracting lyrics from: {audio_path.name}")
        print(f"Language hint: {language or 'auto-detect'}")

        try:
            kwargs = {}
            if language:
                kwargs["language"] = language

            segments, info = self.model.transcribe(
                str(audio_path),
                word_timestamps=True,
                **kwargs
            )

            detected_lang = info.language
            print(f"Detected language: {detected_lang}")

            lyrics_data = []

            for segment in segments:
                seg_data = {
                    "text": segment.text.strip(),
                    "start": round(segment.start, 3),
                    "end": round(segment.end, 3),
                    "words": []
                }

                if segment.words:
                    for word in segment.words:
                        seg_data["words"].append({
                            "word": word.word.strip(),
                            "start": round(word.start, 3),
                            "end": round(word.end, 3),
                        })

                lyrics_data.append(seg_data)
                print(f"  {segment.start:.1f}s -> {segment.end:.1f}s | {segment.text.strip()}")

            return lyrics_data

        except Exception as e:
            print(f"Extraction failed: {e}")
            return []

    def extract_and_save(self, audio_path, language=None):
        import json

        audio_path = Path(audio_path)
        lyrics = self.extract_lyrics(audio_path, language=language)

        if not lyrics:
            return None

        output_path = Path(OUTPUT_DIR) / f"{audio_path.stem}_lyrics.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(lyrics, f, indent=2, ensure_ascii=False)

        print(f"Lyrics saved: {output_path}")
        return str(output_path)

    def lyrics_to_subtitles(self, lyrics_data):
        subtitles = []
        for seg in lyrics_data:
            subtitles.append({
                "text": seg["text"],
                "start": seg["start"],
                "end": seg["end"],
            })
        return subtitles


# ============================================================
# SIMPLE HELPERS
# ============================================================

def mix_audio(voice_path, music_path, output_name=None, volume=None):
    mixer = AudioMixer()
    return mixer.mix_voice_and_music(
        voice_path, music_path,
        output_name=output_name,
        music_volume=volume,
    )


def extract_song_lyrics(audio_path, language=None):
    extractor = LyricsExtractor()
    return extractor.extract_and_save(audio_path, language=language)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    from src.utils.media_manager import get_smart_music

    ensure_output()

    print("")
    print("=" * 55)
    print("AUDIO MIXER TEST")
    print("=" * 55)

    from pathlib import Path as P

    # Find latest voice
    output = P(OUTPUT_DIR)
    mp3_files = sorted(output.glob("*.mp3"), key=lambda f: f.stat().st_mtime, reverse=True)
    voice_files = [f for f in mp3_files if "mixed" not in f.name and "norm" not in f.name]

    if not voice_files:
        print("No voice file found. Run tts_engine.py first")
    else:
        voice_path = voice_files[0]
        print(f"Voice: {voice_path.name}")
        print(f"Duration: {get_audio_duration(voice_path):.2f}s")

        music_path = get_smart_music(niche="gospel")

        if music_path:
            mixer = AudioMixer()
            result = mixer.mix_voice_and_music(
                voice_path=str(voice_path),
                music_path=music_path,
                output_name=f"mixed_test_{now_stamp()}.mp3",
            )
            print(f"Mixed audio: {result}")
            print(f"Duration: {get_audio_duration(result):.2f}s")
        else:
            print("No music found - add mp3 to assets/music/worship/")

    print("=" * 55)
    print("")
    print("LYRICS EXTRACTOR INFO:")
    print("Install: pip install faster-whisper")
    print("Then use: extract_song_lyrics('your_song.mp3', language='sw')")
    print("")
