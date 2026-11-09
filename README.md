# 🎬 VideoFactory: Automated Short-Form Video Engine

VideoFactory is a premium, enterprise-grade automated creative suite designed to dynamically generate and publish highly-engaging vertical videos (YouTube Shorts, TikToks, and Instagram Reels) at scale. It combines AI-driven scriptwriting, synthesized vocal narration, semantic stock B-roll auto-matching, kinetic subtitle styling, and browser automation publishing into a unified, high-performance pipeline.

🟢 **Status**: Beta / Active Development | **Version**: 2.0.0

---

## 🌟 Table of Contents
- [SECTION 1: PROJECT IDENTITY](#-section-1-project-identity)
- [SECTION 2: LIVE SYSTEM SNAPSHOT](#-section-2-live-system-snapshot)
- [SECTION 3: SYSTEM ARCHITECTURE](#-section-3-system-architecture)
- [SECTION 4: COMPLETE FILE STRUCTURE](#-section-4-complete-file-structure)
- [SECTION 5: INSTALLATION & SETUP](#-section-5-installation--setup)
- [SECTION 6: HOW TO USE IT](#-section-6-how-to-use-it)
- [SECTION 7: DATABASE SCHEMA](#-section-7-database-schema)
- [SECTION 8: AI INTEGRATION DETAILS](#-section-8-ai-integration-details)
- [SECTION 9: CURRENT LIMITATIONS & KNOWN BUGS](#-section-9-current-limitations--known-bugs)
- [SECTION 10: MODIFICATION & ADDON GUIDE](#-section-10-modification--addon-guide)
- [SECTION 11: DEPLOYMENT GUIDE](#-section-11-deployment-guide)
- [SECTION 12: COST CALCULATOR](#-section-12-cost-calculator)
- [SECTION 13: ROADMAP](#-section-13-roadmap)
- [SECTION 14: LESSONS LEARNED](#-section-14-lessons-learned)
- [SECTION 15: QUICK REFERENCE CARD](#-section-15-quick-reference-card)

---

## 🚀 SECTION 1: PROJECT IDENTITY

### Product Launch Announcement
Announcing **VideoFactory**, the ultimate automated short-form video compositor and publisher. VideoFactory takes raw ideas, current internet trends, or gospel passages and transforms them into viral, high-production-value vertical reels ready for TikTok, Instagram, and YouTube Shorts—fully automated, with zero human intervention required.

### VideoFactory for a 10-Year-Old
Imagine a magic robot box where you type in a topic like "Samson's strength," and it instantly searches the internet for awesome videos, writes a cool story, speaks it out loud with a movie-narrator voice, colors it like a real film, adds cool word-by-word karaoke subtitles, and posts it to your TikTok page while you sleep!

### VideoFactory for a Developer
VideoFactory is an asynchronous Python-based media composition engine that coordinates large language models (via Groq, Gemini, and OpenRouter), speech synthesis systems (Edge-TTS, ElevenLabs, Puter AI), and media retrieval scraper workers (Pexels, Pinterest RSS, and YouTube-DL) into a localized render stack. The core render engine is powered by `moviepy`, utilizing custom image processing filters (`Pillow`, `numpy`) to perform Ken Burns animations, color grading, and audio ducking. The web client is built on FastAPI and Vanilla JS with a tailorable server-sent event mechanism, and publishing runs utilize Chromium contexts managed by Playwright to navigate social studio uploads, saving persistent browser profiles to bypass 2FA check walls on subsequent runs.

### The Business Value Proposition
In the attention economy, short-form vertical content is the single most efficient organic acquisition channel. However, maintaining a daily posting cadence across multiple niches and platforms requires hours of scripting, B-roll sourcing, editing, and manual uploading—amounting to thousands of dollars in monthly creator overhead. VideoFactory solves this bottleneck by establishing an automated, zero-marginal-cost content engine. It continuously tracks search trends, compiles customized cinematic clips, and publishes them natively to multiple accounts. This allows agencies, digital marketers, and solo creators to scale digital footprints from 1 to 100 channels instantly, capturing millions of organic impressions for a fraction of the cost of a junior editor.

### What Makes VideoFactory Different?
Unlike generic cloud-based video generators that charge high monthly subscriptions, render low-quality templates, and require manual posting, VideoFactory is designed for maximum visual quality and absolute automation:
* **True Automation**: It doesn't just create videos; it publishes them natively to TikTok, YouTube, and Instagram.
* **Semantic Timing**: It synchronizes B-roll video clips with script keywords on a line-by-line level on the fly.
* **Organic Anti-Bot Simulation**: Upload schedules incorporate random offsets and human-like cursor movements to avoid platform detection.
* **Dual-Language Native Support**: Dynamic translation and localized voice settings make it fully native in both English and Swahili.
* **Biblical Figure Character Prioritization**: The asset compiler scans scripts for biblical names and pulls matching actor/model clips from character-specific folders before falling back to general stock folders.

---

## 📊 SECTION 2: LIVE SYSTEM SNAPSHOT

| Component | Status | What It Does | Tech Used |
| :--- | :--- | :--- | :--- |
| **CLI Generator** | 🟢 Fully Working | Orchestrates the command-line inputs and parameters to generate reels. | Python, argparse |
| **AI Script Engine** | 🟢 Fully Working | Writes structured scripts with hooks, bodies, CTAs, and semantic keywords. | Groq, Gemini 2.5, OpenRouter |
| **Groq Cloud STT Engine** | 🟢 Fully Working | High-speed cloud speech-to-text with word-level timestamps in ~1.5s. | Groq `whisper-large-v3-turbo` API |
| **SQLite State Manager** | 🟢 Fully Working | Persistent workflow tracking, key rotation logging, and topic deduplication. | SQLite3 `videofactory.db` |
| **TTS Synthesis Engine** | 🟢 Fully Working | Synthesizes script lines into speech with safety voice paddings and failover logic. | edge-tts, ElevenLabs, Puter AI |
| **Media Downloader Hub** | 🟢 Fully Working | Downloads images/videos from Pexels and Pinterest, and music from YouTube. | Pexels API, Pinterest RSS, yt-dlp |
| **Local Media Manager** | 🟢 Fully Working | Scans local B-roll directories, character folders, and music tracks. | Python pathlib, random |
| **Cinematic Video Compositor** | 🟢 Fully Working | Trims, crops, color-grades, zooms, and overlays subtitles on media clips. | MoviePy, Pillow, NumPy |
| **Audio Ducking Mixer** | 🟢 Fully Working | Fades background music down when narrator speaks using RMS signal monitoring. | PyDub, audioop-lts |
| **Glassmorphic Web Dashboard** | 🟢 Fully Working | Admin panel to configure settings, generate scripts, preview audio, and render. | FastAPI, Vanilla JS, Lucide |
| **Longform Clipper** | 🟢 Fully Working | Transcribes sermons/podcasts, scores hook-worthy moments, and renders 1080x1920 captioned shorts with social kits. | faster-whisper, FFmpeg, MoviePy |

### Features Status Breakdown

#### 🟢 Fully Functional Features
* **Zero-Hardware Cloud STT**: Offloads Whisper speech recognition to Groq's cloud infrastructure (`whisper-large-v3-turbo`), producing millisecond word timestamps in 1.5 seconds with 0% CPU/RAM load on host machine.
* **SQLite Topic Deduplication & Resiliency**: Stores every generated script topic in `output/videofactory.db` so VideoFactory never generates repeated or duplicate topics across runs.
* **Puter.js & OpenRouter Fallback Chains**: Seamless multi-provider script and speech synthesis fallback covering Groq, Gemini, OpenRouter, and Puter AI.
* **100% Stock Video Pacing (Max 2.5s Cuts)**: Song to Reel engine breaks long segments into fast 1.5s - 2.5s video sub-cuts with random start offsets.
* **PyDub Dynamic RMS Audio Ducking**: Monitors vocal track RMS amplitude in 100ms chunks and attenuates background music by -15dB during active speech.
* **Longform → Vertical Shorts Clipper**: Drops a sermon/podcast into `assets/longform/` (or uploads from the dashboard), then analyzes it with word-level Whisper timestamps, scores natural clip windows (EN/SW hook keywords, questions, numbers, word-density, energy), and renders reframed 9:16 shorts with grouped captions plus a copy-paste caption/hashtag kit. Works from the **Longform Clipper** dashboard tab or `python main.py --clip-longform`.

#### 🟡 Partially Functional Features
* **Puter AI TTS Integration**: Works, but since the system's default voice configurations are Edge-TTS neural names, calling Puter TTS without selecting an OpenAI voice results in a silent fallback to the generic `alloy` voice.
* **Pinterest Video Extraction**: Pinterest RSS parsing and yt-dlp scraping works but is highly volatile due to Pinterest changing CDN endpoints and blocking anonymous scrapers.
* **Playwright Session Persistence**: Works, but requires headful browser interaction on the first run to pass 2FA and capture session cookies.

#### 🔴 Planned But Not Started
* **Automated Sound Effect Overlay**: Adding sound transitions (swooshes, typing sounds) automatically on word transitions.
* **Voice Cloning Integration**: Allowing creators to upload a 10-second audio clip to clone their voice for narration.
* **Web-Based Analytics Dashboard**: Scrapes social studio views, likes, and shares to plot performance charts.

#### ❌ Tried and Abandoned Features
* **Local Whisper Lyrics Extraction**: Attempted to use local `faster-whisper` models to transcribe song lyrics on the developer's computer. It was **abandoned** because loading the AI models consumed too much RAM (over 4GB) and crashed systems without dedicated NVIDIA GPUs. The project transitioned to remote API options or pre-aligned SRT templates.

---

## 📐 SECTION 3: SYSTEM ARCHITECTURE

```
                                  +-----------------------+
                                  |   Web Dashboard UI    |
                                  |   (Vanilla JS / CSS)  |
                                  +-----------+-----------+
                                              | HTTP / SSE
                                              v
+-------------------+             +-----------+-----------+
|   Trend Scrapers  |             |      FastAPI App      | <-----+ Environment
|  (Google, Reddit) +------------>|   (src/web/server.py) |       | Variables (.env)
+-------------------+             +-----+-----+-----------+       +-----+-----------+
                                        |     |                         |
               +------------------------+     +------------+            |
               |                                           |            |
               v                                           v            |
    +----------+----------+                     +----------+----------+ |
    |      main.py        |                     |   render_worker.py  | |
    |  (CLI Entry Point)  |                     |  (Subprocess Render)| |
    +----+-----------+----+                     +----+-----------+----+ |
         |           |                               |           |      |
         |           |       +-----------------------+           |      |
         v           v       v                                   v      v
   +-----+---+   +---+-------+--+                          +-----+------+
   | AI Gen  |   |  TTS Engine  |                          |  Video     |
   | (Groq,  |   |  (Edge-TTS,  |                          |  Compositor|
   | Gemini) |   |  ElevenLabs, |                          |  (MoviePy, |
   +---------+   |  Puter)      |                          |  Pillow)   |
                 +-------+------+                          +-----+------+
                         |                                       ^
                         v                                       |
                   +-----+------+       +------------------+     |
                   | Pydub Audio|------>|  Matched Media   +-----+
                   | Ducks/Mix  |       |  & Music Assets  |
                   +------------+       +--------^---------+
                                                 |
                                        +--------+---------+
                                        | Media Downloader |
                                        | (Pexels, yt-dlp) |
                                        +--------^---------+
                                                 |
                                        +--------+---------+
                                        |   Social Sites   |
                                        |  (YT, IG, TikTok)|
                                        +------------------+
```

### Detailed Script Execution Flow (Gospel Reel Generation)

When a user triggers a Gospel Reel generation run (e.g., choosing Option `[1]` in [RUN.bat](RUN.bat) or clicking "Render" on the web dashboard), the following step-by-step code path executes:

1. **Instantiation and Config Load**:
   * The process starts in [main.py](main.py) which loads the current configurations from [config/settings.py](config/settings.py).
   * Settings load the environment variables from the `.env` file via `load_env()` to retrieve API keys.
2. **AI Script Construction**:
   * If `--ai` is passed, [main.py](main.py) calls `AIScriptGenerator().generate()` in [src/scripts/ai_generator.py](src/scripts/ai_generator.py).
   * The generator picks a topic from `TOPIC_POOLS['gospel']`, checking `output/.topic_history.json` to prevent duplicates.
   * It builds a prompt incorporating formatting rules (6 to 8 lines, 4 to 8 words per line) and requests a JSON-like plain text structure.
   * It executes async HTTP requests to Groq, falling back to Gemini if rate-limited.
   * The raw response is cleaned by `clean_ai_output()`, yielding a dictionary with keys: `title`, `hook`, `body` (list of lines), and `cta`.
3. **Narration Synthesis & Timings Sync**:
   * The script lines are compiled into a flat list in [main.py](main.py) and passed to `TTSEngine().generate_per_line_synced()` in [src/audio/tts_engine.py](src/audio/tts_engine.py).
   * For each line, the engine calls the selected provider (e.g., `edge-tts`). The audio is saved as an individual temporary file inside `output/audio/_temp/`.
   * The engine loads the temporary line file into `pydub.AudioSegment`, checks the length, and trims leading and trailing silences using a custom dBFS threshold window (`trim_silence()`). Crucially, a 40ms start padding and 80ms end padding are added to prevent clipping of voice breaths or word endings.
   * The engine concatenates these segments with a `220ms` gap between lines.
   * It calculates the exact start and end time of each line relative to the timeline, writing a sync map to `output/subtitles/{filename}_subtitles.json`.
4. **B-Roll and Music Matching**:
   * The engine initializes [src/utils/media_manager.py](src/utils/media_manager.py) which scans the stock directories defined in `STOCK_PATHS` (e.g., `assets/stock/gospel`, `assets/stock/nature`).
   * It calls `pick_media_for_reel()`. If character names (e.g., "Samson") are found in the script, it scans `assets/stock/pinterest/characters/samson/` first. If B-roll keywords are present in the script and online mode is active, it runs `run_pexels_download()` to grab fresh clips.
   * It maps one media item to each subtitle line.
   * It fetches a background music track via `get_smart_music()`, scanning `assets/music/worship/` and falling back to a root folder search.
5. **Cinematic Compositing (MoviePy)**:
   * The assets are passed to `ReelVideoEngine().build_reel()` in [src/video/video_engine.py](src/video/video_engine.py).
   * For each media item, the engine creates a clip. If it is an image, it applies the `_apply_ken_burns()` scale transformer. If it is a video, it fits it to the vertical aspect ratio, crops the center, and trims it to match the vocal line's duration.
   * Clips are concatenated with a `0.2s` crossfade transition overlay.
   * Subtitle frames are rendered into transparent PNG numpy arrays using `PIL.ImageDraw` and superimposed onto the video coordinates.
   * The voice track is layered, and the background music is mixed in with a custom ducking filter applied (music volume ducks to 15% during voice peaks, rising to 35% during silence gaps).
   * MoviePy outputs the final video using `ffmpeg` with `libx264` codec.

---

## 📂 SECTION 4: COMPLETE FILE STRUCTURE

```
VideoFactory/
│
├── RUN.bat                   # CLI interactive operations launcher
├── main.py                   # CLI engine entry point (direct generation runs)
├── requirements.txt          # Python dependency library manifests
├── .env                      # Holds API credentials and platform configs (never commit)
├── firebase-debug.log        # Logging file outputted by firebase emulator runs
│
├── config/
│   ├── settings.py           # Core settings, profiles, stock paths, and niche configs
│   └── __pycache__/          # Compiled python setting cache files
│
├── src/                      # Source Code Directory
│   │
│   ├── audio/                # Narration, Music, and Transcription modules
│   │   ├── audio_mixer.py    # PyDub audio blending and volume ducking logic
│   │   ├── lyrics_mode.py    # Whisper-based lyrics transcription and subtitle aligner
│   │   ├── song_analyzer.py  # Audio frequency analyzer to detect music beats
│   │   ├── song_picker.py    # Console song selector helper
│   │   ├── tts_engine.py     # Main speech generator (Edge-TTS, ElevenLabs, Puter AI)
│   │   └── tts_engine_backup.py # Legacy backup of the TTS generator
│   │
│   ├── scraper/              # Directory reserved for future crawler integrations (empty)
│   │
│   ├── scripts/              # Workflow automation and background workers
│   │   ├── ai_generator.py   # AI prompt builder and API request handler
│   │   ├── gospel_script.py  # Static local script templates manager (Fallback database)
│   │   ├── render_worker.py  # Subprocess wrapper that executes headless rendering runs
│   │   ├── scheduler.py      # Automated daily generator and posting orchestrator
│   │   └── trending_topics.py# RSS feed parsers and trend-to-spiritual script writers
│   │
│   ├── utils/                # Network operations, downloaders, and automation APIs
│   │   ├── media_downloader.py # Pexels API, Pinterest RSS feed crawler, and music downloader
│   │   ├── media_manager.py  # Local media scanner, character prioritizer, and smart music picker
│   │   └── uploader.py       # Playwright browser automation uploader for social platforms
│   │
│   ├── video/                # Media rendering and compositing engine
│   │   └── video_engine.py   # MoviePy compositor, subtitle renderer, Ken Burns animator
│   │
│   └── web/                  # FastAPI web server and UI files
│       ├── index.html        # Glassmorphic admin control panel frontend
│       ├── server.py         # Backend router API endpoints and subprocess controller
│       ├── css/
│       │   └── style.css     # Glassmorphic styles and animations
│       └── js/
│           └── app.js        # Frontend reactivity, API fetches, and log stream handlers
│
├── assets/                   # Project Static Assets (User Sourced)
│   ├── hooks/                # Swoosh sound effects used in hook transitions
│   ├── music/                # Background soundtracks categorized by niche subfolders
│   ├── stock/                # B-roll photos/videos categorized by niche subfolders
│   │   └── pinterest/
│   │       ├── characters/   # Character specific B-roll subfolders (e.g., samson)
│   │       └── autobroll/    # Dynamically downloaded semantic stock items
│   └── browser_profiles/     # Persistent Chromium cookies/login sessions
│
└── output/                   # Compiler Output Targets
    ├── audio/                # Compiled voice mp3 tracks
    ├── subtitles/            # Output subtitle JSON timing tracks
    ├── videos/               # Final rendered 1080x1920 MP4 videos
    ├── .topic_history.json   # History database tracking processed script topics
    ├── .series_progress.json # Persistent tracker indicating next part of series
    ├── publication_log.json  # Log of published clips, preventing double uploads
    └── upload_queue.json     # Local upload database queue
```

---

## 🛠️ SECTION 5: INSTALLATION & SETUP

### Prerequisites
Before setting up VideoFactory, ensure you have downloaded and installed the following on your Windows system:
1. **Python 3.10+**: Download the official installer from [Python.org](https://www.python.org/downloads/release/python-31011/). Make sure to check **"Add Python to PATH"** during installation.
2. **Git**: Download and install from [Git-SCM](https://git-scm.com/download/win).
3. **FFmpeg**: Required by MoviePy and PyDub for audio/video transcoding:
   * Download from [Gyan.dev FFmpeg Build](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).
   * Extract the files to `C:\ffmpeg`.
   * Add `C:\ffmpeg\bin` to your system environment variables `PATH`.

### Step-by-Step Installation
1. **Clone the Repository**:
   Open Command Prompt (cmd) or PowerShell, navigate to your desired projects directory, and clone:
   ```cmd
   git clone https://github.com/mwijay12/video-factory.git
   cd VideoFactory
   ```
2. **Create and Activate Virtual Environment**:
   ```cmd
   python -m venv venv
   call venv\Scripts\activate
   ```
3. **Install Dependencies**:
   Install the libraries listed in [requirements.txt](requirements.txt):
   ```cmd
   pip install -r requirements.txt
   ```
   *Expected Output*: Successful downloads and installation of `fastapi`, `uvicorn`, `playwright`, `pydub`, `moviepy`, `numpy`, and `httpx`.
4. **Install Playwright Browsers**:
   Initialize the automated browser binaries:
   ```cmd
   playwright install chrome
   ```
5. **Verify Installation**:
   Verify everything is configured correctly by listing the local script templates database:
   ```cmd
   python main.py --list
   ```

### Environment Configurations (`.env`)
Create a file named `.env` in the root folder of the project. Copy and paste the following template, replacing placeholders with your API keys:

```env
# ============================================================
# VIDEOFACTORY ENVIRONMENT VARIABLES
# ============================================================

# --- AI Script Generation API Keys ---
# Get Groq key at: https://console.groq.com/
GROQ_API_KEY=gsk_your_groq_api_key_here

# Get Gemini key at: https://aistudio.google.com/
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here

# Get OpenRouter key at: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key_here

# --- Stock API Keys ---
# Get Pexels key at: https://www.pexels.com/api/
PEXELS_API_KEY=your_pexels_api_key_here

# Get Pixabay key at: https://pixabay.com/api/docs/
PIXABAY_API_KEY=your_pixabay_api_key_here

# --- TTS API Keys (Optional) ---
# ElevenLabs API Key: https://elevenlabs.io/
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Puter.com Auth Token (copy from puter dashboard console)
PUTER_TOKEN=your_puter_auth_token_here

# --- Posting Configuration ---
# Options: youtube, instagram, tiktok (comma-separated)
PUBLISH_PLATFORMS=youtube,instagram,tiktok
```

### Common Installation Issues & Fixes

#### 1. `FileNotFoundError: [WinError 2] The system cannot find the file specified` during rendering
* **Cause**: MoviePy cannot find the FFmpeg binary executable.
* **Fix**: Ensure FFmpeg is added to your Windows system PATH variables. Alternatively, force MoviePy to recognize it by setting the environment path inside your terminal before running:
  ```cmd
  set FFMPEG_BINARY=C:\ffmpeg\bin\ffmpeg.exe
  ```

#### 2. `Playwright Executable not found`
* **Cause**: Playwright's browser binaries are missing from the local AppData directory.
* **Fix**: Run `playwright install` in your active virtual environment.

#### 3. `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`
* **Cause**: Windows file locks on temp audio or video segments while moviepy is rendering.
* **Fix**: Close any open video players (e.g. VLC, Windows Media Player) that have files in `output/` open. Restart the FastAPI server to release active Python file handles.

---

## 📲 SECTION 6: HOW TO USE IT

### 🖥️ 1. The Web Dashboard Interface

The web dashboard is the most user-friendly way to manage settings and render videos.

* **To Start**: Double-click [RUN.bat](RUN.bat) and choose option **`35`** (`Open Web Control Dashboard`). Or run:
  ```cmd
  python src/web/server.py
  ```
* **Access**: Open your browser and navigate to `http://localhost:8000`.
* **Actions**: You can generate AI scripts, preview TTS voices, trigger manual stock downloads, configure settings, and watch rendering log outputs in real-time.

---

### 💻 2. Command Line Interface (CLI)

For power users, [main.py](main.py) provides a direct interface to trigger generation runs.

#### Example A: Generate a Standard Gospel Reel
* **Action**: Generates a gospel reel using a random script from local templates, using local media assets.
* **Command**:
  ```cmd
  python main.py --niche gospel --lang english
  ```
* **Output Log**:
  ```text
  [1/5] Loading script...
    Title:  Faith in the Valley
    Hook:   God has not forgotten you
  [2/5] Generating voice narration...
    Audio:  gospel_reel_20260621_043000.mp3
  [3/5] Loading media...
    gospel          -> 8 files found
    Total Media:    8
  [4/5] Selecting music...
    Music:  worship_piano.mp3
  [5/5] Rendering reel...
    Reel:    output\videos\gospel_reel_20260621_043000.mp4
  ```

#### Example B: Generate an AI-Driven Swahili Reel with Viral Hook
* **Action**: Calls Groq/Gemini to write a fresh Swahili script, uses the Swahili neural voice, downloads matching portrait B-roll on the fly, and applies a warm golden hour color tint.
* **Command**:
  ```cmd
  python main.py --ai --niche swahili --lang swahili --viral --mood hopeful
  ```
* **Output Video file**: `output/videos/ai_swahili_123045_20260621.mp4`

#### Example C: Batch Generate 5 Motivational Reels
* **Command**:
  ```cmd
  python main.py --batch 5 --niche motivational --ai --viral
  ```

#### Example D: Clip a Sermon/Podcast into Vertical Shorts
* **Action**: Analyzes a longform video (from `assets/longform/`), scores the best hook-worthy moments, and renders the top clips as captioned 1080x1920 shorts with a social caption kit.
* **Commands**:
  ```cmd
  python main.py --clip-list                       :: list available longform sources
  python main.py --clip-longform                   :: clip the newest source → 3 shorts
  python main.py --clip-longform sermon.mp4 --clips 5 --clip-crop top
  ```
* **Output**: `output/videos/clip_<title>_<stamp>.mp4` plus `*_social_kit.txt` / `*_social_kit.json` companions.

---

### 📡 3. FastAPI REST Endpoints

The web interface communicates with FastAPI via REST endpoints:

#### A. Generate AI Script
* **Endpoint**: `POST http://localhost:8000/api/script/generate`
* **Request Payload**:
  ```json
  {
    "niche": "motivational",
    "language": "english",
    "topic": "discipline vs motivation",
    "viral": true
  }
  ```
* **Response Output**:
  ```json
  {
    "id": "ai_motivational_051230",
    "title": "Discipline Beats Motivation",
    "hook": "Stop waiting for the perfect feeling.",
    "body": [
      "Motivation gets you started today.",
      "But discipline keeps you going tomorrow.",
      "When the passion fades, work remains.",
      "Commit to the process, not the feeling."
    ],
    "cta": "Follow for daily reminders.",
    "mood": "powerful",
    "voice": "en-US-GuyNeural",
    "rate": "+10%",
    "pitch": "+0Hz",
    "style": "normal"
  }
  ```

#### B. Trigger B-Roll Stock Download
* **Endpoint**: `POST http://localhost:8000/api/download`
* **Request Payload**:
  ```json
  {
    "source": "epic ocean sunset waves",
    "folder": "nature",
    "limit": 3,
    "media_type": "video",
    "engine": "pexels"
  }
  ```
* **Response Output**:
  ```json
  {
    "message": "Download started in the background"
  }
  ```

#### C. Longform Clipper (sermons/podcasts → vertical shorts)
* **Endpoints**:
  * `GET  /api/clipper/sources` — list videos in `assets/longform/` (+ transcript status)
  * `POST /api/clipper/upload` — upload a long video (multipart `file`)
  * `POST /api/clipper/analyze` — `{"source","language","model","min_dur","max_dur"}` → Whisper analysis + scored candidates
  * `POST /api/clipper/render` — same params plus `{"count","crop","niche","mood","words_per_line","selected":[{"start","end"}]}` → renders clips
  * `GET  /api/clipper/status` — `{status, progress, step, log, candidates, outputs}` (poll every ~1s while running)
* **Response Output** (`/api/clipper/render`):
  ```json
  {
    "message": "Clipper render started",
    "job": "render"
  }
  ```

---

## 🗄️ SECTION 7: DATABASE SCHEMA

VideoFactory utilizes **local JSON flat-file databases** for its data storage layer. This architecture provides low-latency local reads and writes, requires zero cloud configuration, and functions offline in Data Saver mode.

### 1. Topic History Database
* **Path**: `output/.topic_history.json`
* **Purpose**: Tracks previously generated script topics per niche to ensure variety and prevent duplicate scripts in auto-scheduling runs.
* **Fields**:
  * Key: `string` (Niche name, e.g., `"gospel"`, `"motivational"`)
  * Value: `array of strings` (A list of the 20 most recently processed topics)
* **Example Schema**:
  ```json
  {
    "gospel": [
      "God has not forgotten you",
      "His grace is sufficient",
      "Trust God in hard times"
    ],
    "motivational": [
      "Stop waiting start now",
      "You are one decision away"
    ]
  }
  ```

### 2. Series Progress Database
* **Path**: `output/.series_progress.json`
* **Purpose**: Persistently tracks the current episode counter of active multi-part series runs.
* **Fields**:
  * Key: `string` (Series ID, e.g., `"armor_of_god"`, `"fruits_of_spirit"`)
  * Value: `integer` (The last generated episode part number)
* **Example Schema**:
  ```json
  {
    "armor_of_god": 3,
    "fruits_of_spirit": 1,
    "names_of_god": 7
  }
  ```

### 3. Publication Log Database
* **Path**: `output/publication_log.json`
* **Purpose**: Records daily publications to enforce strict limits, preventing spamming social channels.
* **Fields**:
  * Key: `string` (ISO date stamp, e.g., `"2026-06-21"`)
  * Value: `object`
    * `timestamp`: `string` (datetime format)
    * `video`: `string` (compiled video filename)
    * `platforms`: `array of strings` (social networks published to)
* **Example Schema**:
  ```json
  {
    "2026-06-21": {
      "timestamp": "2026-06-21 07:15:30",
      "video": "auto_gospel_20260621_071200.mp4",
      "platforms": ["youtube", "instagram"]
    }
  }
  ```

### 4. Upload Queue Database
* **Path**: `output/upload_queue.json`
* **Purpose**: Queue database that manages scheduled publications, tracking execution status.
* **Fields**:
  * `id`: `string` (auto-generated timestamp slug)
  * `video_path`: `string` (absolute local path to MP4 file)
  * `title`: `string` (upload title metadata)
  * `description`: `string` (upload caption string)
  * `platforms`: `array of strings` (target upload platforms)
  * `status`: `string` (one of: `"pending"`, `"processing"`, `"completed"`, `"failed"`)
  * `publish_log`: `string` (terminal execution logs from Playwright run)
* **Example Schema**:
  ```json
  [
    {
      "id": "q_1718942400",
      "video_path": "C:/Users/MWIJAY TECH/VideoFactory/output/videos/web_gospel_20260621.mp4",
      "title": "His Timing is Perfect",
      "description": "Trust the process. #faith #gospel",
      "platforms": ["youtube", "tiktok"],
      "status": "pending",
      "publish_log": ""
    }
  ]
  ```

### ☁️ Future Firestore Database Migration Map

For developers planning to scale VideoFactory to a SaaS multi-tenant platform, the local JSON structure maps directly to Firestore as follows:

```
[Collection: users]
  ├── id: string (Auth UID)
  ├── email: string
  └── subscription_tier: string ("free", "premium")

[Collection: jobs]
  ├── id: string (Auto ID)
  ├── userId: string (Link to users)
  ├── niche: string ("gospel", "tech")
  ├── language: string ("english", "swahili")
  ├── status: string ("queued", "rendering", "completed", "failed")
  ├── video_url: string (Link to Firebase Storage)
  └── createdAt: timestamp

[Collection: templates]
  ├── id: string
  ├── niche: string
  ├── title: string
  ├── hook: string
  ├── body: array
  └── cta: string
```

---

## 🤖 SECTION 8: AI INTEGRATION DETAILS

### 1. Provider Stack & Models
VideoFactory connects to three API provider endpoints to guarantee uptime:
1. **Groq (Primary)**: Uses `llama-3.3-70b-versatile` (fast responses, high-quality reasoning) or `llama-3.1-8b-instant` (low latency, backup).
2. **Google Gemini (Secondary)**: Uses `gemini-2.0-flash` via Google AI Studio. Selected for Swahili semantic accuracy.
3. **OpenRouter (Tertiary)**: Uses `meta-llama/llama-3.2-3b-instruct:free` or `mistralai/mistral-7b-instruct:free` as a cost-effective final fallback.

### 2. Prompt Engineering
The prompts are constructed dynamically inside `build_prompt()` based on language and niche:

#### English prompt generation:
```text
Write a gospel reel script about: [topic]

Tone: [mood_flavor]

Rules:
- Write EXACTLY 6 to 8 lines total
- Each line must be 4 to 8 words max
- Total spoken time 20 to 28 seconds
- No stage directions, no narrator labels
- Just the spoken words directly
- No numbering, no bullets, no asterisks
- Plain text lines only
```

#### Swahili prompt generation (highly optimized for Swahili syntax):
```text
Andika script fupi ya reel ya injili kuhusu: [topic]

Sheria:
- Mistari 6 hadi 8 mifupi
- Maneno 4 hadi 8 kila mstari
- Mstari wa kwanza ni hook
- Mstari wa mwisho ni CTA

Tone: [mood_flavor]

Rudisha MISTARI TU.
```

### 3. Failover & Local Template Recovery
If the system detects API key failures or network timeouts, it logs the warning and calls [gospel_script.py](src/scripts/gospel_script.py). The `ScriptManager` picks a random hand-written script from its hardcoded local template database. This ensures that the daily scheduler **never fails** even if the internet goes down or API limits are hit.

---

## ⚠️ SECTION 9: CURRENT LIMITATIONS & KNOWN BUGS

### 1. Known Bugs & Anomalies
* **Puter TTS Voice Mismatch**:
  * *Bug*: When Puter TTS is selected as the active provider, any voice options that are not in OpenAI's native list (like Microsoft's `en-US-ChristopherNeural` or `sw-KE-RafikiNeural`) are rejected by the Puter API wrapper. The system defaults to the `"alloy"` voice, making all videos sound the same.
  * *Steps to reproduce*: Save settings with `TTS_PROVIDER="puter"` and try to generate a Swahili reel. The voice generated will be English-accented `"alloy"`.
* **PowerShell FileSystem Provider Lock**:
  * *Bug*: Running scripts via PowerShell command shells can occasionally crash with `Cannot find drive. A drive with the name 'Microsoft.PowerShell.Core\FileSystem' does not exist.`
  * *Fix*: Execute commands using Command Prompt (`cmd.exe`).
* **Pinterest RSS Truncation**:
  * *Bug*: Downloader is restricted to 15 items because Pinterest RSS feeds truncate historical content.

### 2. Performance Bottlenecks
* **MoviePy Single-Core CPU Rendering**:
  * *Issue*: MoviePy operates synchronously. During final composition, rendering a 24-second vertical video with crossfades and karaoke subtitles takes approximately **60 to 90 seconds** on a modern multi-core CPU. Scaling to concurrent render runs on a single server will lock CPU resources.
  * *Mitigation*: Move rendering runs to background workers (like Celery) or run them in Docker containers on serverless platforms (e.g., Cloud Run).

### 3. Security Vulnerabilities
* **Cleartext Browser Profile Storage**:
  * *Issue*: Playwright persistent cookies and sessions are stored in raw JSON files under `assets/browser_profiles/`. Anyone with system read permissions can copy these folders and hijack the creator's social accounts.
  * *Mitigation*: Restrict system read access to the `assets/browser_profiles/` folder or encrypt cookie profiles at rest.

---

## 🛠️ SECTION 10: MODIFICATION & ADDON GUIDE

### 🔄 MOD 1: Swapping from Gemini to OpenAI GPT-4o
* **Difficulty**: ⭐ (Easy)
* **Time to implement**: 1 Hour
* **Files to modify**: 
  * [src/scripts/ai_generator.py](src/scripts/ai_generator.py)
* **Step-by-step**:
  1. Add `openai` to requirements.txt:
     ```bash
     pip install openai
     ```
  2. Add `OPENAI_API_KEY` to your `.env` file.
  3. Inside [ai_generator.py](src/scripts/ai_generator.py), import the client:
     ```python
     from openai import OpenAI
     ```
  4. Create a function to generate scripts using GPT-4o:
     ```python
     async def generate_with_openai(prompt):
         client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
         response = client.chat.completions.create(
             model="gpt-4o",
             messages=[{"role": "user", "content": prompt}],
             max_tokens=300
         )
         return response.choices[0].message.content
     ```
  5. Add this method to the fallback chain inside `generate()`.

---

### 💳 MOD 2: Integrating Stripe Payment & User Subscriptions
* **Difficulty**: ⭐⭐⭐⭐ (Hard)
* **Time to implement**: 4 Days
* **Files to modify**:
  * Create `src/web/stripe_router.py`
  * Modify [src/web/server.py](src/web/server.py)
* **Dependencies**:
  ```bash
  pip install stripe
  ```
* **Step-by-step**:
  1. Set up a Stripe account and retrieve your API Keys.
  2. Implement webhook handlers to listen for `customer.subscription.created` and `customer.subscription.deleted`.
  3. Add credit balance checks to the `/api/render` endpoint. Reject render requests if the user has 0 generation credits remaining.

---

### 🚀 MOD 3: Adding Support for a New Niches (e.g., Business/Finance)
* **Difficulty**: ⭐ (Easy)
* **Time to implement**: 30 Minutes
* **Files to modify**:
  * [config/settings.py](config/settings.py)
* **Step-by-step**:
  1. Open [settings.py](config/settings.py) and navigate to `STOCK_PATHS` and `NICHE_CONFIG`.
  2. Add a new stock path for the niche:
     ```python
     "business": ASSETS_DIR / "stock" / "business"
     ```
  3. Update `NICHE_CONFIG` with your new folder paths, default music styles, and hook examples:
     ```python
     "business": {
         "name": "Business & Finance Reels",
         "folders": ["business", "nature_pics"],
         "music_folder": "cinematic",
         "music_fallback": "ambient",
         "moods": ["powerful", "cinematic"],
         "hook_examples": [
             "The secret to wealth is simple",
             "Stop saving your money in banks",
             "This asset pays you every month"
         ]
     }
     ```
  4. Create the folder `assets/stock/business/` and add vertical B-roll files.
  5. Select Niche: `business` on the dashboard to test rendering.

---

## 🚢 SECTION 11: DEPLOYMENT GUIDE

### 1. Dockerizing the Render Stack
Because VideoFactory requires system binaries like FFmpeg and Google Chrome (via Playwright), the most reliable way to deploy it to staging or production is using **Docker**.

Create a `Dockerfile` in the project root:
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app
COPY . /app

# Install Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser dependencies
RUN playwright install chromium
RUN playwright install-deps

EXPOSE 8000
CMD ["uvicorn", "src.web.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Deploying Staging to GCP Cloud Run
1. Build the Docker image:
   ```bash
   gcloud builds submit --tag gcr.io/your-project-id/videofactory
   ```
2. Deploy to Cloud Run, allocating at least **2GB RAM** and **2 CPUs** to handle MoviePy rendering loads:
   ```bash
   gcloud run deploy videofactory \
     --image gcr.io/your-project-id/videofactory \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2
   ```

---

## 💸 SECTION 12: COST CALCULATOR

| Service | Free Tier Limits | Paid Tier Cost | Cost at 100 Users | Cost at 1000 Users |
| :--- | :--- | :--- | :--- | :--- |
| **GCP Cloud Run** | 2M requests/mo free | $0.00001667/vCPU-sec | ~$45.00/month | ~$450.00/month |
| **Gemini AI API** | 15 RPM / 1M TPM free | $0.075 / 1M input tokens | ~$1.50/month (10k runs) | ~$15.00/month |
| **Groq API** | Free limits active | Pay-as-you-go | ~$2.00/month | ~$20.00/month |
| **Edge-TTS** | Unlimited free | $0.00 | $0.00 | $0.00 |
| **ElevenLabs** | 10k chars/mo free | $5.00 / 30k chars | ~$120.00/month | ~$1,200.00/month |
| **Pexels API** | 20k requests/mo free | $0.00 | $0.00 | $0.00 |
| **Hosting Domain** | N/A | $12.00/year | $1.00/month | $1.00/month |
| **Total Est. Cost**| **$0.00 (Self-Hosted)** | **Minimal** | **...169.50/month**| **...1,686.00/month**|

---

## 🗺️ SECTION 13: ROADMAP

### Short-Term (Next 2 Weeks)
- [ ] Fix Puter AI TTS voice mapping to automatically translate Microsoft Neural voices to valid OpenAI speech models (`alloy`, `onyx`, etc.).
- [ ] Implement a headless Playwright scraper to replace Pinterest RSS feed queries, improving B-roll image resolution.
- [ ] Add support for custom SRT font files, allowing users to upload `.ttf` branding styles to the `assets/` folder.
- [ ] Build a database-level cleaning worker to automatically delete temporary audio files from `output/audio/_temp/` older than 48 hours.
- [ ] Integrate a Discord webhook notification channel that sends compiled videos to a server channel once rendering succeeds.

### Medium-Term (Next 3 Months)
- [ ] Implement multi-tenant authentication (OAuth2 with JWT tokens) to support commercial SaaS setups.
- [ ] Add visual canvas overlay options, enabling watermarks, visual stamps, and custom brand logos.
- [ ] Build a cloud-based video rendering agent using Celery workers to scale rendering processes horizontally.
- [ ] Transition the storage layer from local JSON databases to PostgreSQL hosted on GCP Cloud SQL.

### Long-Term (6-12 Months)
- [ ] **VideoFactory 2.0 Web SaaS Platform**: Release a drag-and-drop video generator SaaS platform where users connect their social media accounts and queue posts from a web console.
- [ ] **AI-Driven Video Layout Optimization**: Train a small vision model that checks crop margins, ensuring human faces or critical objects are never cropped out during vertical reframing.

---

## 💡 SECTION 14: LESSONS LEARNED

* **Silence Padding is Crucial for Narration**:
  During early iterations of VideoFactory, vocal phrases sounded choppy and robotic. We learned that trimming 100% of silence segments cuts off the natural trailing sounds of words and breaths. Adding a **vocal margin** (40ms start padding, 80ms end padding) instantly made narration sound fluid and human.
* **Playwright Sessions Avoid Account Bans**:
  Attempting to automate logging into social platforms using fully headless browsers triggers automated bot-detection checkpoints. Using **persistent, headful browser profiles** on the first run, allowing manual login, and saving session cookies locally successfully bypasses security walls without triggering account suspensions.
* **Local Fallback Strategies Save Deployments**:
  In production, remote APIs will occasionally fail due to rate limits or billing issues. Building local template fallbacks (like [gospel_script.py](src/scripts/gospel_script.py)) ensures the automation engine keeps publishing content without crashing.

---

## 🎴 SECTION 15: QUICK REFERENCE CARD

### Core Commands
* **Start FastAPI Server**:
  ```bash
  python src/web/server.py
  ```
* **Generate Gospel Reel (CLI)**:
  ```bash
  python main.py --ai --niche gospel
  ```
* **Force Run Daily Auto-Publishing Scheduler**:
  ```bash
  python src/scripts/scheduler.py --force
  ```
* **Download Pinterest B-Roll Assets**:
  ```bash
  python main.py --download-pinterest "gospel" --download-limit 15
  ```

### Critical API Endpoints
* `GET  /api/config` - Fetches active niches, voices, and moods.
* `POST /api/render` - Launches the rendering subprocess wrapper.
* `GET  /api/render/status` - Returns rendering log stream.
* `POST /api/pipeline/run` - Runs the auto-publishing schedule.

### Essential Env Keys
* `GROQ_API_KEY` - Groq Llama scripts.
* `GEMINI_API_KEY` - Google AI Studio.
* `PEXELS_API_KEY` - Vertical stock videos.
* `PUBLISH_PLATFORMS` - Target networks (youtube, instagram, tiktok).

### Fast-Fix Checklist

#### 1. Audio and Speech out of sync?
Open [settings.py](config/settings.py) and verify `TRANSITION_DURATION = 0.20`. Check that your background audio file is not corrupted.

#### 2. Uploader fails with selector error?
Social media platforms frequently update their upload HTML structures. Take a look at the debug screenshot saved in `output/debug_screenshot_yt.png` to find which button locator failed, and edit [src/utils/uploader.py](src/utils/uploader.py) to match the new selector.

#### 3. Playwright login loop?
Delete the cache directory `assets/browser_profiles/{platform}` and run [RUN.bat](RUN.bat) Option **`36`** to restart the interactive session.
