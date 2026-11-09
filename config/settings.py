# ============================================================
# VIDEOFACTORY SETTINGS - REELS / SHORTS FIRST
# ============================================================

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

def load_env():
    p = BASE_DIR / ".env"
    if not p.exists():
        return {}
    d = {}
    try:
        for line in p.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.split('=', 1)
                d[k.strip()] = v.strip()
    except Exception:
        pass
    return d

ENV = load_env()

# API Keys & Credentials
GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")
GEMINI_KEYS = [k.strip() for k in ENV.get("GEMINI_KEYS", "").split(",") if k.strip()]
if GEMINI_API_KEY and GEMINI_API_KEY not in GEMINI_KEYS:
    GEMINI_KEYS.insert(0, GEMINI_API_KEY)

PUTER_TOKEN = ENV.get("PUTER_TOKEN", "")
ELEVENLABS_API_KEY = ENV.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_KEYS = [k.strip() for k in ENV.get("ELEVENLABS_KEYS", "").split(",") if k.strip()]
GROQ_API_KEY = ENV.get("GROQ_API_KEY", "")
GROQ_KEYS = [k.strip() for k in ENV.get("GROQ_KEYS", "").split(",") if k.strip()]

# MODE
# ============================================================
# data_saver = use only local saved videos/images/music
# normal     = can download online later
# hybrid     = online script, local media
MODE = "hybrid"

# ============================================================
# CONTENT FORMAT
# ============================================================
NICHE = "gospel"

# ============================================================
# LANGUAGE + VOICE
# ============================================================
LANGUAGE = "swahili"

VOICE_OPTIONS = {
    "english": {
        "main": "direct-gemini:Aoede",
        "alt1": "direct-gemini:Puck",
        "alt2": "en-US-ChristopherNeural",
        "alt3": "en-US-GuyNeural",
        "alt4": "en-US-JennyNeural"
    },
    "swahili": {
        "main": "direct-gemini:Aoede",
        "alt1": "direct-gemini:Puck",
        "alt2": "direct-gemini:Zephyr",
        "alt3": "direct-gemini:Fenrir",
        "alt4": "direct-gemini:Kore",
        "alt5": "direct-gemini:Charon",
        "alt6": "sw-KE-RafikiNeural"
    }
}

ACTIVE_VOICE = "direct-gemini:Aoede"
TTS_RATE = "+0%"
TTS_VOLUME = "+0%"
TTS_PITCH = "+0Hz"
TTS_PROVIDER = "direct-gemini"
PUTER_TOKEN = ENV.get("PUTER_TOKEN", "")

# ============================================================
# VIDEO PROFILE - REELS / SHORTS
# ============================================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

# ============================================================
# VIDEO QUALITY PRESETS
# ─────────────────────────────────────────────────────────
# draft    → Fast encode, smaller file.  Good for previews.
# standard → Balanced quality & speed.  Good for daily uploads.
# premium  → Near-lossless detail.      Good for viral/archive.
# ============================================================
QUALITY_PRESETS = {
    "draft": {
        "bitrate":       "5000k",
        "crf":           23,
        "encode_preset": "faster",
        "audio_bitrate": "128k",
        "sharpen":       False,
        "threads":       0,          # 0 = auto (all CPUs)
    },
    "standard": {
        "bitrate":       "8000k",
        "crf":           20,
        "encode_preset": "medium",
        "audio_bitrate": "192k",
        "sharpen":       True,
        "threads":       0,
    },
    "premium": {
        "bitrate":       "12000k",
        "crf":           16,
        "encode_preset": "slow",
        "audio_bitrate": "256k",
        "sharpen":       True,
        "threads":       0,
    },
}

# Active preset — change this to switch quality globally
VIDEO_QUALITY_PRESET = "standard"

# ── Derive individual settings from the active preset ──
_active_preset = QUALITY_PRESETS.get(VIDEO_QUALITY_PRESET, QUALITY_PRESETS["standard"])
BITRATE        = _active_preset["bitrate"]
PRESET         = _active_preset["encode_preset"]
VIDEO_CRF      = _active_preset["crf"]
AUDIO_BITRATE  = _active_preset["audio_bitrate"]
VIDEO_SHARPEN  = _active_preset["sharpen"]
ENCODE_THREADS = _active_preset["threads"]

# ============================================================
# REELS STRUCTURE
# ============================================================
# Main target: 20-30 sec highly engaging
MIN_DURATION = 15
MAX_DURATION = 28
TARGET_DURATION = 24

# Quick cuts
MIN_CLIP_DURATION = 1.8
MAX_CLIP_DURATION = 3.2
IDEAL_CLIP_DURATION = 2.4

# Number of media items per reel
MIN_MEDIA_ITEMS = 6
MAX_MEDIA_ITEMS = 100
TARGET_MEDIA_ITEMS = 30

# Use both images and videos
USE_VIDEOS = True
USE_IMAGES = True
IMAGE_HOLD_TIME = 2.2
TRANSITION_DURATION = 0.20

# ============================================================
# HOOK STYLE & SOUND EFFECTS
# ============================================================
HOOK_AUDIO_ENABLED = False
HOOK_AUDIO_VOLUME = 0.25
AUDIO_NORMALIZE_ENABLED = False

HOOK_CONFIG = {
    "enabled": False,
    "hook_duration": 3.0,
    "hook_text_max_words": 7,
    "hook_text_color": "white",
    "hook_stroke_color": "black",
    "hook_stroke_width": 3,
    "audio_enabled": False,
    "audio_volume": 0.25,
}

# ============================================================
# SUBTITLES
# ============================================================
SUBTITLES_ENABLED = True
SUBTITLE_FONT_SIZE = 40
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "white"
SUBTITLE_STROKE_WIDTH = 1
SUBTITLE_POSITION_Y = 0.62
SUBTITLE_MAX_WORDS_PER_LINE = 3
SUBTITLE_KARAOKE = True
SUBTITLE_ANIMATION_STYLE = "whisper"  # "whisper", "slide_up", "karaoke", "clean"
SUBTITLE_FONT_PATH = ""
SUBTITLE_BG_OPACITY = 148

SUBTITLE_STYLE = {
    "font_size": SUBTITLE_FONT_SIZE,
    "color": SUBTITLE_COLOR,
    "stroke_color": SUBTITLE_STROKE_COLOR,
    "stroke_width": SUBTITLE_STROKE_WIDTH,
    "position_y": SUBTITLE_POSITION_Y,
    "max_words_per_line": SUBTITLE_MAX_WORDS_PER_LINE,
    "karaoke": SUBTITLE_KARAOKE,
    "animation_style": SUBTITLE_ANIMATION_STYLE,
    "font_path": SUBTITLE_FONT_PATH,
    "bg_opacity": SUBTITLE_BG_OPACITY,
}

# ============================================================
# MUSIC
# ============================================================
BACKGROUND_MUSIC_ENABLED = True
BACKGROUND_MUSIC_VOLUME = 0.3
VOICE_VOLUME = 1.0
MUSIC_FADE_IN_MS = 1000
MUSIC_FADE_OUT_MS = 1500

# ============================================================
# PATHS - LOCAL MEDIA
# ============================================================
STOCK_PATHS = {
    "gospel": ASSETS_DIR / "stock" / "gospel",
    "nature": ASSETS_DIR / "stock" / "nature",
    "worship": ASSETS_DIR / "stock" / "worship",
    "africa": ASSETS_DIR / "stock" / "africa",
    "vibe": ASSETS_DIR / "stock" / "vibe",
    "dance": ASSETS_DIR / "stock" / "dance",
    "praise": ASSETS_DIR / "stock" / "praise",
    "uploaded_queue": ASSETS_DIR / "stock" / "uploaded_queue",
    "pinterest": ASSETS_DIR / "stock" / "pinterest",
}

MUSIC_PATH = ASSETS_DIR / "music"

# ============================================================
# NICHE CONFIG
# ============================================================
NICHE_CONFIG = {
    "dance": {
        "name": "Dance / Energetic Reels",
        "folders": ["dance", "gospel", "nature"],
        "moods": ["energetic", "powerful", "joyful"],
        "hook_examples": [
            "Feel the gospel rhythm",
            "Praise with joy today",
            "Dance and be grateful"
        ]
    },
    "gospel": {
        "name": "Gospel Reels",
        "folders": ["gospel", "nature", "worship", "pinterest"],
        "moods": ["peaceful", "hopeful", "holy", "emotional"],
        "hook_examples": [
            "God has not forgotten you",
            "This prayer is for you today",
            "Before you sleep, hear this",
            "If you feel tired, listen",
            "God is still working"
        ]
    },
    "motivational": {
        "name": "Motivational Reels",
        "folders": ["nature", "pinterest"],
        "moods": ["powerful", "bold", "uplifting"],
        "hook_examples": [
            "Do not quit now",
            "You are closer than you think",
            "One day can change everything"
        ]
    },
    "tech": {
        "name": "Tech / AI Reels",
        "folders": ["pinterest"],
        "moods": ["smart", "fast", "modern"],
        "hook_examples": [
            "This AI tool saves hours",
            "You need this workflow",
            "This changes everything"
        ]
    },
    "swahili": {
        "name": "Swahili Reels",
        "folders": ["africa", "nature", "pinterest"],
        "moods": ["warm", "regional", "hopeful"],
        "hook_examples": [
            "Usikate tamaa",
            "Sikiliza hii kwa makini",
            "Mungu hajakuacha"
        ]
    }
}

# ============================================================
# ONLINE MODE CONFIG (for later)
# ============================================================
PEXELS_API_KEY = ENV.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = ENV.get("PIXABAY_API_KEY", "")
GROQ_API_KEY = ENV.get("GROQ_API_KEY", "")
GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = ENV.get("OPENROUTER_API_KEY", "")
ELEVENLABS_API_KEY = ENV.get("ELEVENLABS_API_KEY", "")

# Key pools for rotation
GEMINI_KEYS = [k.strip() for k in ENV.get("GEMINI_KEYS", "").split(",") if k.strip()]
if GEMINI_API_KEY and GEMINI_API_KEY not in GEMINI_KEYS:
    GEMINI_KEYS.insert(0, GEMINI_API_KEY)

GROQ_KEYS = [k.strip() for k in ENV.get("GROQ_KEYS", "").split(",") if k.strip()]
if GROQ_API_KEY and GROQ_API_KEY not in GROQ_KEYS:
    GROQ_KEYS.insert(0, GROQ_API_KEY)

OPENROUTER_KEYS = [k.strip() for k in ENV.get("OPENROUTER_KEYS", "").split(",") if k.strip()]
if OPENROUTER_API_KEY and OPENROUTER_API_KEY not in OPENROUTER_KEYS:
    OPENROUTER_KEYS.insert(0, OPENROUTER_API_KEY)

ELEVENLABS_KEYS = [k.strip() for k in ENV.get("ELEVENLABS_KEYS", "").split(",") if k.strip()]
if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY not in ELEVENLABS_KEYS:
    ELEVENLABS_KEYS.insert(0, ELEVENLABS_API_KEY)

OLLAMA_KEYS = [k.strip() for k in ENV.get("OLLAMA_KEYS", "").split(",") if k.strip()]

# Ollama & Telegram Configs
OLLAMA_API_BASE = ENV.get("OLLAMA_API_BASE", "http://localhost:11434/v1")
OLLAMA_MODEL = ENV.get("OLLAMA_MODEL", "llama3.2")
TELEGRAM_BOT_TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")

# ============================================================
# DATA SAVER RULES
# ============================================================
DATA_SAVER = {
    "allow_online_script_generation": True,
    "allow_online_tts": True,
    "allow_stock_download": False,
    "prefer_local_videos": True,
    "prefer_local_images": True,
    "cache_everything": True,
}

# ============================================================
# FILE TYPES
# ============================================================
VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".webm"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]

# ============================================================
# HELPERS
# ============================================================
def get_active_niche():
    return NICHE_CONFIG.get(NICHE, NICHE_CONFIG["gospel"])

def get_niche_folders():
    niche = get_active_niche()
    return [STOCK_PATHS[name] for name in niche["folders"] if name in STOCK_PATHS]

def print_status():
    print("")
    print("=" * 60)
    print("VIDEOFACTORY - REELS MODE")
    print("=" * 60)
    print(f"Mode:              {MODE}")
    print(f"Niche:             {NICHE}")
    print(f"Language:          {LANGUAGE}")
    print(f"Voice:             {ACTIVE_VOICE}")
    print(f"Format:            {VIDEO_WIDTH}x{VIDEO_HEIGHT}")
    print(f"FPS:               {FPS}")
    print(f"Target Duration:   {TARGET_DURATION}s")
    print(f"Clip Duration:     {MIN_CLIP_DURATION}-{MAX_CLIP_DURATION}s")
    print(f"Media Items:       {MIN_MEDIA_ITEMS}-{MAX_MEDIA_ITEMS}")
    print(f"Subtitles:         {SUBTITLES_ENABLED}")
    print(f"Music:             {BACKGROUND_MUSIC_ENABLED}")
    print(f"Data Saver:        {MODE == 'data_saver'}")
    print("=" * 60)
    print("")

if __name__ == "__main__":
    print_status()

# MUSIC PATHS - organized by mood
MUSIC_PATHS = {
    "worship":      ASSETS_DIR / "music" / "worship",
    "praise":       ASSETS_DIR / "music" / "praise",
    "prayer":       ASSETS_DIR / "music" / "prayer",
    "cheerful":     ASSETS_DIR / "music" / "cheerful",
    "cinematic":    ASSETS_DIR / "music" / "cinematic",
    "motivational": ASSETS_DIR / "music" / "motivational",
    "swahili":      ASSETS_DIR / "music" / "swahili",
    "ambient":      ASSETS_DIR / "music" / "ambient",
    "general":      ASSETS_DIR / "music",
}

# EXTENDED STOCK PATHS - Pinterest subfolders
STOCK_PATHS.update({
    "backgrounds":       ASSETS_DIR / "stock" / "pinterest" / "backgrounds",
    "jesus":             ASSETS_DIR / "stock" / "pinterest" / "jesus",
    "people":            ASSETS_DIR / "stock" / "pinterest" / "people",
    "people_worshiping": ASSETS_DIR / "stock" / "pinterest" / "people" / "worshiping",
    "people_cheerful":   ASSETS_DIR / "stock" / "pinterest" / "people" / "cheerful",
    "people_praying":    ASSETS_DIR / "stock" / "pinterest" / "people" / "praying",
    "people_grateful":   ASSETS_DIR / "stock" / "pinterest" / "people" / "grateful",
    "nature_pics":       ASSETS_DIR / "stock" / "pinterest" / "nature_pics",
    "quotes":            ASSETS_DIR / "stock" / "pinterest" / "quotes",
})

# ============================================================
# TOPIC POOLS — AI Script Generation Seeds
# Each niche has English and Swahili topic lists
# ============================================================

TOPIC_POOLS = {
    # --- GOSPEL (English) ---
    "gospel": [
        "God has not forgotten you",
        "His grace is sufficient for you",
        "Trust God in the waiting season",
        "The peace that surpasses understanding",
        "God's timing is always perfect",
        "You are chosen and loved by God",
        "Faith the size of a mustard seed",
        "God turns your mourning into dancing",
        "He who began a good work will finish it",
        "Cast all your anxiety on Him",
        "The Lord is my shepherd I shall not want",
        "Walk by faith not by sight",
        "God fights battles you cannot see",
        "His mercies are new every morning",
        "You are the light of the world",
        "God's plans are to prosper you",
        "The armor of God protects you daily",
        "Be still and know that He is God",
        "Samson's strength came from surrender",
        "David defeated Goliath with one stone",
        "Joseph's pit was part of his purpose",
        "Esther was born for such a time as this",
        "Ruth's loyalty was rewarded beyond measure",
        "Moses parted the sea with one staff",
        "Elijah heard God in the still small voice",
        "Daniel's faith survived the lion's den",
        "The prodigal son always had a father waiting",
        "God restored Job double what he lost",
        "Mary said yes and changed everything",
        "The resurrection means death has no final word",
    ],

    # --- PRAYER (English) ---
    "prayer": [
        "Pray this if you feel God has abandoned you tonight",
        "A dangerous prayer for breakthrough that the enemy hates",
        "Pray this before any decision you regret making",
        "The 60 second prayer that broke my anxiety",
        "Pray this when you cannot sleep at 3am",
        "A warfare prayer for your children today",
        "The prayer that healed my broken relationship",
        "Pray this when nothing seems to work",
        "A prayer for the one who is about to give up",
        "Pray this over your finances right now",
    ],

    # --- PRAISE (English) ---
    "praise": [
        "Why praise is the weapon the enemy fears most",
        "What happens in the spirit when you worship in pain",
        "The breakthrough that comes from praising before the answer",
        "How Paul and Silas praise broke prison chains",
        "Why God inhabits the praise of His people",
    ],

    # --- MOTIVATIONAL (English) ---
    "motivational": [
        "Stop waiting for the perfect moment",
        "Discipline beats motivation every single day",
        "You are one decision away from a different life",
        "The grind you hate is building the life you want",
        "Small steps daily beat big steps occasionally",
        "Your comfort zone is your prison",
        "Success leaves clues if you pay attention",
        "The person you want to be is built today",
        "Stop explaining yourself to people who don't matter",
        "Every master was once a disaster",
        "The secret to getting ahead is getting started",
        "Your future self is watching every decision you make",
        "Pain is temporary quitting lasts forever",
        "You don't rise to the level of your goals",
        "You fall to the level of your systems",
        "Nobody is coming to save you build yourself",
        "Consistency is the most underrated superpower",
        "Start before you are ready or never start",
        "The only bad workout is the one that didn't happen",
        "Soft life is built by hard work first",
    ],

    # --- TECH (English) ---
    "tech": [
        "This AI tool saves hours",
        "You need this workflow",
        "This changes everything",
    ],

    # --- SWAHILI GOSPEL ---
    "swahili_gospel": [
        "Mungu hakusahau ndoto zako",
        "Neema yake inatosha kabisa",
        "Subiri Mungu ana mpango mzuri",
        "Imani ndogo inaweza kusogeza milima",
        "Amani ya Mungu inazidi akili zote",
        "Wewe ni mtoto wa Mfalme wa wafalme",
        "Mungu anafanya mambo mapya leo",
        "Maumivu yako yana lengo la mbinguni",
        "Asubuhi mpya inaleta rehema mpya",
        "Mungu anapigana vita vyako usijali",
        "Yesu alikufa ili upate uzima wa kweli",
        "Ombi lako limesikika mbinguni",
        "Nguvu zako zinatoka kwa Bwana",
        "Usiogope Mungu yuko nawe daima",
        "Samson alionyesha nguvu kutoka kwa Mungu",
        "Daudi alimshinda Goliati kwa imani",
        "Yosefu alitoka shimoni kwenda kasri",
        "Ester alizaliwa kwa wakati huu huu",
        "Mungu atarudisha mara mbili ulichopoteza",
        "Ufufuo wa Yesu unabadilisha kila kitu",
        "Mama Maria alisema ndiyo akabadilisha historia",
        "Danieli aliishi ndani ya simba hakuumizwa",
        "Mungu wako ni mkubwa kuliko tatizo lako",
        "Roho Mtakatifu anakuongoza kila siku",
        "Baraka zako zinakuja haraka sasa",
        "Sala yako inabadilisha mambo usikate tamaa",
        "Mwisho wa machozi ni furaha ya Mungu",
        "Kiburi chake hakiishi nguvu zake hazikomi",
        "Yesu ni jibu la kila swali la maisha",
        "Upendo wa Mungu hauna mwisho wala kikomo",
    ],

    # --- SWAHILI MOTIVATIONAL ---
    "swahili_motivational": [
        "Acha kusubiri wakati mzuri anza sasa",
        "Nidhamu ndiyo siri ya mafanikio ya kweli",
        "Uamuzi mmoja unaweza kubadilisha maisha yako",
        "Kazi ngumu leo italeta maisha mazuri kesho",
        "Hatua ndogo kila siku zinafanya safari ndefu",
        "Eneo la starehe ni gereza la maendeleo",
        "Mafanikio yana alama fuata na ujifunze",
        "Wewe wa kesho anaangalia unavyofanya leo",
        "Maumivu ya sasa yanatengeneza nguvu za kesho",
        "Usifanye kazi ngumu fanya kazi kwa akili",
        "Siri ya kuendelea ni kuanza kabla ya kuwa tayari",
        "Hakuna anayekuja kukuokoa jiokoe mwenyewe",
        "Uthabiti ndiyo nguvu kubwa zaidi duniani",
        "Ndoto bila kazi ni ndito tu usidanganywe",
        "Ujuzi unaonunua kwa jasho unabaki milele",
        "Watu wanaokufanya uelewe ni hazina yako",
        "Usijaribu kupendeza kila mtu utajipoteza",
        "Kila mzigo mkubwa unafunza nguvu mpya",
        "Mtu anayekujua vizuri ni wewe mwenyewe",
        "Chagua ngumu leo uchague rahisi kesho",
    ],

    # --- SWAHILI LIFE LESSONS (East African context) ---
    "swahili_life": [
        "Familia ndiyo utajiri wa kweli wa maisha",
        "Heshima inajengwa kwa matendo si maneno",
        "Mama alifanya mengi bila kupata shukrani",
        "Elimu ni silaha dhidi ya umaskini wote",
        "Rafiki wa kweli anabaki wakati wa shida",
        "Fedha inakuja na kwenda lakini tabia inabaki",
        "Mzee wa mtaa ana hekima zaidi ya kitabu",
        "Subira huvuta heri kama asali ya mwitu",
        "Umoja wa ndugu ni nguvu ya kabila zima",
        "Kenya inahitaji vijana wenye maarifa na roho",
        "Maisha ya jiji yanafundisha lakini mji wa nyumbani una amani",
        "Usiangalie nyuma safari yako ni mbele yako",
        "Kila mtu ana saa yake ya kuvuna subiri yako",
        "Mtoto wa maskini anaweza kuwa rais wa kesho",
        "Usisahau asili yako ukifika juu ya maisha",
    ],
}

# EXTENDED NICHE CONFIG with music folders
NICHE_CONFIG.update({
    "gospel": {
        "name": "Gospel Reels",
        "topic_pool_key": "gospel",
        "language": "english",
        "folders": [
            "gospel", "nature", "worship",
            "backgrounds", "jesus",
            "people_worshiping", "people_praying",
            "people_grateful", "nature_pics",
        ],
        "music_folder":   "worship",
        "music_fallback": "prayer",
        "moods": ["peaceful", "hopeful", "holy", "emotional"],
        "default_mood": "hopeful",
        "hook_examples": [
            "God has not forgotten you",
            "This prayer is for you today",
            "Before you sleep, hear this",
            "If you feel tired, listen",
            "God is still working",
            "You are not alone",
            "His grace is enough",
        ]
    },
    "prayer": {
        "name": "Prayer Reels",
        "topic_pool_key": "prayer",
        "language": "english",
        "folders": [
            "people_praying", "jesus", "nature",
            "worship", "backgrounds", "nature_pics",
        ],
        "music_folder":   "prayer",
        "music_fallback": "ambient",
        "moods": ["peaceful", "emotional", "holy"],
        "default_mood": "peaceful",
        "hook_examples": [
            "Pray this before you sleep",
            "This prayer is for you",
            "Speak this out loud right now",
        ]
    },
    "praise": {
        "name": "Praise and Worship Reels",
        "topic_pool_key": "praise",
        "language": "english",
        "folders": [
            "worship", "gospel",
            "people_worshiping", "people_cheerful",
            "jesus", "backgrounds",
        ],
        "music_folder":   "praise",
        "music_fallback": "worship",
        "moods": ["hopeful", "holy", "peaceful"],
        "default_mood": "hopeful",
        "hook_examples": [
            "Praise Him in the storm",
            "Worship changes everything",
            "Enter His gates with thanksgiving",
        ]
    },
    "motivational": {
        "name": "Motivational Reels",
        "topic_pool_key": "motivational",
        "language": "english",
        "folders": [
            "nature", "backgrounds",
            "people_cheerful", "nature_pics", "quotes",
        ],
        "music_folder":   "motivational",
        "music_fallback": "cinematic",
        "moods": ["powerful", "hopeful", "emotional", "cinematic", "energetic"],
        "default_mood": "powerful",
        "hook_examples": [
            "Stop waiting for the perfect moment",
            "Nobody is coming to save you",
            "The grind you hate is building your future",
        ]
    },
    "tech": {
        "name": "Tech and AI Reels",
        "topic_pool_key": "tech",
        "language": "english",
        "folders": [
            "backgrounds", "quotes", "nature_pics",
        ],
        "music_folder":   "cinematic",
        "music_fallback": "ambient",
        "moods": ["cinematic", "peaceful", "powerful"],
        "default_mood": "cinematic",
        "hook_examples": [
            "This AI tool saves hours",
            "You need this workflow",
            "This changes everything",
        ]
    },
    "swahili": {
        "name": "Swahili Gospel & Life Reels",
        "topic_pool_key": "swahili_gospel",
        "language": "swahili",
        "folders": ["gospel", "nature", "nature_pics", "swahili", "africa", "backgrounds", "people_worshiping", "people_grateful"],
        "music_folder": "worship",
        "music_fallback": "ambient",
        "moods": ["hopeful", "peaceful", "powerful"],
        "default_mood": "hopeful",
        "hook_examples": [
            "Mungu hakusahau ndoto zako",
            "Wakati wako umefika sasa hivi",
            "Usikate tamaa Mungu yuko nawe",
        ],
    },
    "swahili_motivational": {
        "name": "Swahili Motivational Reels",
        "topic_pool_key": "swahili_motivational",
        "language": "swahili",
        "folders": ["nature", "backgrounds", "people_cheerful", "nature_pics", "quotes"],
        "music_folder": "cinematic",
        "music_fallback": "ambient",
        "moods": ["powerful", "energetic", "cinematic"],
        "default_mood": "powerful",
        "hook_examples": [
            "Acha kusubiri wakati mzuri anza sasa",
            "Uamuzi mmoja unaweza kubadilisha maisha",
            "Wewe wa kesho anaangalia unavyofanya leo",
        ],
    },
    "swahili_life": {
        "name": "Swahili Life Lessons",
        "topic_pool_key": "swahili_life",
        "language": "swahili",
        "folders": ["nature", "nature_pics", "gospel", "africa", "backgrounds", "people_grateful"],
        "music_folder": "ambient",
        "music_fallback": "worship",
        "moods": ["peaceful", "hopeful", "cinematic"],
        "default_mood": "peaceful",
        "hook_examples": [
            "Familia ndiyo utajiri wa kweli",
            "Mama alifanya mengi bila kupata shukrani",
            "Heshima inajengwa kwa matendo si maneno",
        ],
    },
})

# ============================================================
# BRANDING & WATERMARK CONFIGURATION
# ============================================================
WATERMARK_ENABLED = False
WATERMARK_PATH = str(ASSETS_DIR / "watermark.png")
WATERMARK_POSITION = "right,top"
WATERMARK_OPACITY = 0.45
WATERMARK_HEIGHT = 65
WATERMARK_MARGIN = 35

