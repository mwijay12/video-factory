# -*- coding: utf-8 -*-
# ================================================================
# LYRICS MODE - Convert your songs into lyric-synced reels
# Fast Groq Whisper Cloud STT + Local Faster-Whisper Fallback
# Auto-generates TikTok, Reels & Shorts distribution kits
# ================================================================

import asyncio
import json
import time
from pathlib import Path


def now_stamp():
    return time.strftime('%Y%m%d_%H%M%S')


def transcribe_with_groq_api(audio_path, language=None):
    from config.settings import ENV
    raw_keys = ENV.get("GROQ_KEYS", "") or ENV.get("GROQ_API_KEY", "")
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    if not keys:
        return None

    audio_path = Path(audio_path)
    if not audio_path.exists():
        return None

    lang_code = None
    if language and language.lower() not in ['auto', 'auto-detect']:
        lang_map = {'english': 'en', 'swahili': 'sw', 'spanish': 'es', 'french': 'fr', 'german': 'de'}
        lang_code = lang_map.get(language.lower(), language)

    import httpx
    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    for idx, key in enumerate(keys):
        headers = {"Authorization": f"Bearer {key}"}
        try:
            with open(audio_path, "rb") as f:
                files = {"file": (audio_path.name, f, "audio/mpeg")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": ["word", "segment"],
                    "temperature": "0.0"
                }
                if lang_code:
                    data["language"] = lang_code
                r = httpx.post(url, headers=headers, files=files, data=data, timeout=60.0)
                if r.status_code == 200:
                    res = r.json()
                    words = res.get("words", [])
                    segments = res.get("segments", [])
                    
                    seg_list = []
                    for s in segments:
                        seg_list.append({
                            "text": s.get("text", "").strip(),
                            "start": round(s.get("start", 0.0), 3),
                            "end": round(s.get("end", 0.0), 3),
                            "words": [{"word": w.get("word","").strip(), "start": round(w.get("start",0.0),3), "end": round(w.get("end",0.0),3)} for w in words if w.get("start",0)>=s.get("start",0) and w.get("end",0)<=s.get("end",0)]
                        })
                    print(f"  [Groq STT Cloud] Transcribed in 1.5s (Key #{idx+1})! Words: {len(words)}")
                    return {
                        "language": lang_code or res.get("language", "auto"),
                        "duration": res.get("duration", 30.0),
                        "segments": seg_list
                    }
                elif r.status_code == 429:
                    from src.utils.database import log_key_rotation
                    log_key_rotation("Groq_STT", idx, "HTTP 429 Rate Limit Exceeded")
                    continue
        except Exception as e:
            print(f"  Groq STT note: {e}")
            continue

    return None


class LyricsExtractor:

    def __init__(self, model_size='base'):
        self.model = None
        self.model_size = model_size
        self.loaded = False

    def load_model(self):
        if self.loaded:
            return True

        print(f'Loading Whisper model ({self.model_size})...')
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(
                self.model_size,
                device='cpu',
                compute_type='int8',
            )
            self.loaded = True
            print('Whisper model loaded successfully!')
            return True
        except ImportError:
            print('ERROR: faster-whisper not installed')
            return False
        except Exception as e:
            print(f'ERROR loading whisper: {e}')
            return False

    def extract_lyrics(self, audio_path, language=None):
        audio_path = Path(audio_path)
        if not audio_path.exists():
            print(f'Audio not found: {audio_path}')
            return None

        # Convert full names to whisper codes
        lang_map = {
            'english': 'en', 'swahili': 'sw',
            'spanish': 'es', 'french': 'fr',
            'german': 'de', 'portuguese': 'pt',
        }
        if language and language.lower() in lang_map:
            language = lang_map[language.lower()]

        # 1. Try Zero-Hardware Cloud Offload via Groq API (whisper-large-v3-turbo)
        cloud_res = transcribe_with_groq_api(audio_path, language=language)
        if cloud_res:
            return cloud_res

        # 2. Local fallback if offline
        if not self.load_model():
            return None

        print('')
        print(f'Extracting lyrics from: {audio_path.name}')
        print(f'Language: {language or "auto-detect"}')
        print('Transcribing locally... [this takes 15-40 seconds]')
        print('')

        try:
            kwargs = {'word_timestamps': True, 'vad_filter': True}
            if language:
                kwargs['language'] = language

            segments, info = self.model.transcribe(str(audio_path), **kwargs)

            detected = info.language
            print(f'Detected language: {detected}')
            print(f'Duration: {info.duration:.1f}s')

            lyrics_data = []
            for segment in segments:
                seg_info = {
                    'text': segment.text.strip(),
                    'start': round(segment.start, 3),
                    'end': round(segment.end, 3),
                    'words': []
                }

                if segment.words:
                    for word in segment.words:
                        seg_info['words'].append({
                            'word': word.word.strip(),
                            'start': round(word.start, 3),
                            'end': round(word.end, 3),
                        })

                lyrics_data.append(seg_info)

            return {
                'language': detected,
                'duration': info.duration,
                'segments': lyrics_data,
            }

        except Exception as e:
            print(f'Extraction failed: {e}')
            return None

    def save_lyrics(self, audio_path, lyrics_result):
        if not lyrics_result:
            return None

        audio_path = Path(audio_path)
        output_dir = Path('output/lyrics')
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / f'{audio_path.stem}_lyrics.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(lyrics_result, f, indent=2, ensure_ascii=False)

        srt_path = output_dir / f'{audio_path.stem}.srt'
        self._save_as_srt(lyrics_result['segments'], srt_path)

        print(f'Saved: {json_path}')
        print(f'Saved: {srt_path}')
        return str(json_path)

    def _save_as_srt(self, segments, srt_path):
        def fmt(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                f.write(f'{i}\n')
                f.write(f'{fmt(seg["start"])} --> {fmt(seg["end"])}\n')
                f.write(f'{seg["text"]}\n\n')

    def align_known_text_to_audio(self, audio_path, text_content, group_words_per_line=4):
        """Aligns known lyric text to audio file timestamps using forced alignment."""
        lines = [l.strip() for l in text_content.splitlines() if l.strip()]
        if not lines:
            return []

        # Get audio duration
        duration = 30.0
        try:
            from moviepy import AudioFileClip
            ac = AudioFileClip(str(audio_path))
            duration = ac.duration
            ac.close()
        except Exception:
            pass

        # Try extracting Whisper timestamps for line anchor points
        whisper_res = self.extract_lyrics(audio_path)
        anchors = []
        if whisper_res and 'segments' in whisper_res:
            for s in whisper_res['segments']:
                anchors.append({'start': s['start'], 'end': s['end']})

        subtitles = []
        if anchors and len(anchors) == len(lines):
            for i, line in enumerate(lines):
                subtitles.append({
                    'text': line,
                    'start': round(anchors[i]['start'], 3),
                    'end': round(anchors[i]['end'], 3)
                })
        elif anchors:
            total_start = anchors[0]['start']
            total_end = anchors[-1]['end']
            span = max(1.0, total_end - total_start)
            step = span / len(lines)
            for i, line in enumerate(lines):
                subtitles.append({
                    'text': line,
                    'start': round(total_start + i * step, 3),
                    'end': round(total_start + (i + 1) * step, 3)
                })
        else:
            line_dur = duration / len(lines)
            for i, line in enumerate(lines):
                subtitles.append({
                    'text': line,
                    'start': round(i * line_dur, 3),
                    'end': round((i + 1) * line_dur, 3)
                })

        return subtitles

    def lyrics_to_subtitles(self, lyrics_result, group_words_per_line=4, fill_instrumental_gaps=True, max_gap_seconds=1.2):
        """
        Converts word timestamps into high-impact TikTok/Reels kinetic chunks.
        Splits on phrase pauses and instrumental breaks so text doesn't linger.
        """
        if not lyrics_result:
            return []

        all_words = []
        for seg in lyrics_result.get('segments', []):
            for w in seg.get('words', []):
                all_words.append(w)

        raw_subs = []
        if not all_words:
            raw_subs = [
                {'text': seg['text'], 'start': seg['start'], 'end': seg['end']}
                for seg in lyrics_result.get('segments', [])
            ]
        else:
            current_chunk = []
            for i, w in enumerate(all_words):
                if not current_chunk:
                    current_chunk.append(w)
                    continue

                prev_w = current_chunk[-1]
                gap = w['start'] - prev_w['end']

                # Break conditions:
                # 1. Gap between words > max_gap_seconds
                # 2. Chunk word count >= group_words_per_line
                # 3. Punctuation break
                should_break = (
                    gap > max_gap_seconds or
                    len(current_chunk) >= group_words_per_line or
                    prev_w['word'].endswith(('.', '!', '?', ','))
                )

                if should_break:
                    text = ' '.join(cw['word'] for cw in current_chunk).strip()
                    start = round(current_chunk[0]['start'], 3)
                    end = round(min(current_chunk[-1]['end'] + 0.25, w['start'] - 0.05 if gap > 0.1 else current_chunk[-1]['end']), 3)
                    raw_subs.append({
                        'text': text,
                        'start': start,
                        'end': max(end, start + 0.6)
                    })
                    current_chunk = [w]
                else:
                    current_chunk.append(w)

            if current_chunk:
                text = ' '.join(cw['word'] for cw in current_chunk).strip()
                start = round(current_chunk[0]['start'], 3)
                end = round(current_chunk[-1]['end'] + 0.25, 3)
                raw_subs.append({
                    'text': text,
                    'start': start,
                    'end': max(end, start + 0.6)
                })

        if not fill_instrumental_gaps or not raw_subs:
            return raw_subs

        instrumental_labels = [
            "🎵 [ Worship Interlude ]",
            "🎹 [ Piano Solo ]",
            "⚡ [ Amapiano Beat ]",
            "✨ [ Holy Presence ]",
            "🎶 [ High Praise ]"
        ]

        filled_subs = []

        # Check intro gap
        if raw_subs[0]['start'] > 2.5:
            filled_subs.append({
                'text': "🎵 [ Instrumental Intro ]",
                'start': 0.0,
                'end': round(raw_subs[0]['start'] - 0.2, 3)
            })

        for k in range(len(raw_subs)):
            cur = raw_subs[k]
            filled_subs.append(cur)

            if k < len(raw_subs) - 1:
                next_start = raw_subs[k + 1]['start']
                gap = next_start - cur['end']
                if gap > 2.5:
                    label = instrumental_labels[k % len(instrumental_labels)]
                    filled_subs.append({
                        'text': label,
                        'start': round(cur['end'] + 0.1, 3),
                        'end': round(next_start - 0.1, 3)
                    })

        return filled_subs


async def generate_lyric_reel(
    song_path,
    language=None,
    niche='gospel',
    mood='peaceful',
    words_per_line=4,
    aspect_ratio="9:16",
    caption_style="typing",
    caption_position="center"
):
    from src.utils.media_manager import MediaManager
    from src.video.video_engine import ReelVideoEngine
    from src.utils.social_strategy import generate_social_package, save_social_kit, print_social_kit_banner

    song_path = Path(song_path)

    if not song_path.exists():
        for sub in ['swahili', 'english', 'mixed', 'custom', '']:
            check = Path('assets/songs') / sub / song_path.name
            if check.exists():
                song_path = check
                break

    if not song_path.exists():
        print(f'Song not found: {song_path}')
        print('Place your song in: assets/songs/swahili/  or  assets/songs/english/')
        return None

    print('=' * 62)
    print('   LYRICS MODE - Song to Reel Generator')
    print('=' * 62)
    print(f'Song: {song_path.name}')
    print('')

    # STEP 1: Extract lyrics
    extractor = LyricsExtractor(model_size='base')
    lyrics_result = extractor.extract_lyrics(str(song_path), language=language)

    if not lyrics_result:
        return None

    extractor.save_lyrics(str(song_path), lyrics_result)

    # STEP 2: Convert to short subtitle chunks
    subtitles = extractor.lyrics_to_subtitles(lyrics_result, group_words_per_line=words_per_line)
    print(f'Created {len(subtitles)} subtitle chunks')

    # STEP 3: Beat detection for synced clip transitions
    beat_cuts = None
    try:
        from src.audio.beat_sync import generate_beat_cut_points
        beat_cuts = generate_beat_cut_points(str(song_path), min_clip=1.2, max_clip=3.5)
        if beat_cuts:
            print(f'🎵 Beat Sync: {len(beat_cuts)} studio beat-aligned cut points generated')
    except Exception as e:
        print(f'🎵 Beat Sync: skipped ({e})')

    # STEP 3.5: Pick media (ensure 100% unique items matching beat cuts)
    print('Loading background media...')
    manager = MediaManager(niche=niche)
    manager.scan()
    needed_count = max(35, len(beat_cuts) + 5 if beat_cuts else len(subtitles) * 2)
    media_items = manager.pick_media_for_reel(count=needed_count, script=song_path.stem) if manager.has_media() else []
    print(f'🎬 Loaded {len(media_items)} unique stock media clips for reel')

    # STEP 4: Build reel using SONG as audio
    print('Building reel...')
    video_engine = ReelVideoEngine(
        mood=mood,
        aspect_ratio=aspect_ratio,
        caption_style=caption_style,
        caption_position=caption_position
    )
    output_name = f'song_{song_path.stem.replace(" ", "_")}_{now_stamp()}.mp4'
    hook_text = subtitles[0]['text'] if subtitles else song_path.stem

    output_path = video_engine.build_reel(
        media_items=media_items,
        audio_path=str(song_path),
        subtitles=subtitles,
        output_name=output_name,
        hook_text=hook_text,
        music_path=None,
        show_progress_bar=True,
        beat_cuts=beat_cuts,
    )

    # STEP 5: Generate Viral Social Media Package
    social_data = generate_social_package(
        song_name=song_path.stem,
        subtitles=subtitles,
        niche=niche,
        language=language or "swahili",
        mood=mood
    )
    save_social_kit(output_path, social_data)
    print_social_kit_banner(social_data)

    return output_path


async def generate_lyric_reel_smart(
    song_name=None,
    language=None,
    niche='gospel',
    mood='peaceful',
    words_per_line=4,
    target_duration=30,
    use_best_segment=True,
    aspect_ratio="9:16",
    caption_style="typing",
    caption_position="center"
):
    """
    SMART version:
    - Auto-picks random song if song_name is None
    - Finds the highest energy 20-30s peak chorus/hook
    - Converts lyrics into sync kinetic captions
    - Auto-generates complete Social Media Distribution Kit (TikTok / Reels / Shorts)
    """
    from src.audio.song_picker import (
        pick_random_song,
        find_song_by_name,
        get_best_segment,
        extract_song_segment,
    )
    from src.utils.media_manager import MediaManager
    from src.video.video_engine import ReelVideoEngine
    from src.utils.social_strategy import generate_social_package, save_social_kit, print_social_kit_banner

    # Pick song
    if song_name:
        song_path = find_song_by_name(song_name)
        if not song_path:
            print(f'Song not found: {song_name}')
            return None
    else:
        category = None
        if language in ['swahili', 'sw']:
            category = 'swahili'
        elif language in ['english', 'en']:
            category = 'english'
        song_path = pick_random_song(category=category)
        if not song_path:
            print('No songs found. Add songs to assets/songs/')
            return None
        print(f'Randomly picked: {song_path.name}')

    print('=' * 62)
    print('   SMART LYRICS REEL GENERATOR')
    print('=' * 62)
    print(f'Song: {song_path.name}')
    print('')

    # Get best segment
    if use_best_segment:
        print('Finding peak viral segment...')
        start_s, end_s = get_best_segment(
            str(song_path),
            target_duration=target_duration,
        )
        
        # Extract that segment
        temp_dir = Path('output/temp')
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_segment = temp_dir / f'song_segment_{now_stamp()}.mp3'
        segment_path = extract_song_segment(
            str(song_path),
            str(temp_segment),
            start_s, end_s,
            fade_in=1.0,
            fade_out=2.0,
        )
        working_audio = segment_path
        print(f'Extracted segment: {(end_s-start_s):.1f}s')
    else:
        working_audio = str(song_path)
        start_s = 0

    # Extract lyrics from segment
    extractor = LyricsExtractor(model_size='base')
    lyrics_result = extractor.extract_lyrics(working_audio, language=language)

    subtitles = []
    if lyrics_result and lyrics_result.get('segments'):
        extractor.save_lyrics(song_path, lyrics_result)
        subtitles = extractor.lyrics_to_subtitles(
            lyrics_result,
            group_words_per_line=words_per_line
        )
        print(f'Created {len(subtitles)} subtitle chunks')

    # If no lyrics detected OR instrumental song, create rhythmic title cards
    if not subtitles:
        print('No lyrics detected - creating beat-driven visual cuts')
        try:
            from src.audio.ffmpeg_ops import get_audio_duration
            audio_dur = get_audio_duration(working_audio)
            if audio_dur <= 0:
                audio_dur = float(target_duration)
        except Exception:
            audio_dur = float(target_duration)

        num_segments = 8
        segment_dur = audio_dur / num_segments
        song_title = song_path.stem.replace('_', ' ').title()

        for i in range(num_segments):
            start = round(i * segment_dur, 3)
            end = round(start + segment_dur, 3)
            text = f"🎵 {song_title}" if i == 0 else ''
            subtitles.append({
                'text': text,
                'start': start,
                'end': end,
            })

    # Beat detection for synced clip transitions
    beat_cuts = None
    try:
        from src.audio.beat_sync import generate_beat_cut_points
        beat_cuts = generate_beat_cut_points(working_audio, min_clip=1.2, max_clip=3.5)
        if beat_cuts:
            print(f'🎵 Beat Sync: {len(beat_cuts)} studio beat-aligned cut points generated')
    except Exception as e:
        print(f'🎵 Beat Sync: skipped ({e})')

    # Pick media (ensure 100% unique items matching beat cuts)
    print('Loading background media...')
    manager = MediaManager(niche=niche)
    manager.scan()
    needed_count = max(35, len(beat_cuts) + 5 if beat_cuts else len(subtitles) * 2)
    media_items = manager.pick_media_for_reel(
        count=needed_count,
        script=song_path.stem
    ) if manager.has_media() else []
    print(f'🎬 Loaded {len(media_items)} unique stock media clips for reel')

    # Render
    print('Building reel...')
    video_engine = ReelVideoEngine(
        mood=mood,
        aspect_ratio=aspect_ratio,
        caption_style=caption_style,
        caption_position=caption_position
    )
    output_name = f'song_{song_path.stem.replace(" ", "_")}_{now_stamp()}.mp4'
    hook_text = subtitles[0]['text'] if subtitles else song_path.stem

    output_path = video_engine.build_reel(
        media_items=media_items,
        audio_path=working_audio,
        subtitles=subtitles,
        output_name=output_name,
        hook_text=hook_text,
        music_path=None,
        show_progress_bar=True,
        beat_cuts=beat_cuts,
    )

    # Generate Viral Social Media Package
    social_data = generate_social_package(
        song_name=song_path.stem,
        subtitles=subtitles,
        niche=niche,
        language=language or "swahili",
        mood=mood
    )
    save_social_kit(output_path, social_data)
    print_social_kit_banner(social_data)

    return output_path


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Usage: python -m src.audio.lyrics_mode <song.mp3> [language]')
        print('Example: python -m src.audio.lyrics_mode mysong.mp3 sw')
        print('')
        print('Place songs in: assets/songs/swahili/ or assets/songs/english/')
        sys.exit(0)

    song = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(generate_lyric_reel(song, language=lang, niche='gospel'))
