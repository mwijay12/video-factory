from pathlib import Path

# ============================================================
# UPDATE settings.py with new STOCK_PATHS and MUSIC_PATHS
# ============================================================

settings = Path('config/settings.py')
content = settings.read_text(encoding='utf-8')

# Add MUSIC_PATHS if not already there
if 'MUSIC_PATHS' not in content:
    music_paths = '''
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
'''
    content += music_paths
    print('MUSIC_PATHS added!')
else:
    print('MUSIC_PATHS already exists')

# Add extended STOCK_PATHS if not already there
if 'people_worshiping' not in content:
    extra_paths = '''
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
'''
    content += extra_paths
    print('Extended STOCK_PATHS added!')
else:
    print('Extended STOCK_PATHS already exists')

# Add extended NICHE_CONFIG
if 'music_folder' not in content:
    niche_extra = '''
# EXTENDED NICHE CONFIG with music folders
NICHE_CONFIG.update({
    "gospel": {
        "name": "Gospel Reels",
        "folders": [
            "gospel", "nature", "worship",
            "backgrounds", "jesus",
            "people_worshiping", "people_praying",
            "people_grateful", "nature_pics",
        ],
        "music_folder":   "worship",
        "music_fallback": "prayer",
        "moods": ["peaceful", "hopeful", "holy", "emotional"],
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
        "folders": [
            "people_praying", "jesus", "nature",
            "worship", "backgrounds", "nature_pics",
        ],
        "music_folder":   "prayer",
        "music_fallback": "ambient",
        "moods": ["peaceful", "emotional", "holy"],
        "hook_examples": [
            "Pray this before you sleep",
            "This prayer is for you",
            "Speak this out loud right now",
        ]
    },
    "praise": {
        "name": "Praise and Worship Reels",
        "folders": [
            "worship", "gospel",
            "people_worshiping", "people_cheerful",
            "jesus", "backgrounds",
        ],
        "music_folder":   "praise",
        "music_fallback": "worship",
        "moods": ["hopeful", "holy", "peaceful"],
        "hook_examples": [
            "Praise Him in the storm",
            "Worship changes everything",
            "Enter His gates with thanksgiving",
        ]
    },
    "motivational": {
        "name": "Motivational Reels",
        "folders": [
            "nature", "backgrounds",
            "people_cheerful", "nature_pics", "quotes",
        ],
        "music_folder":   "motivational",
        "music_fallback": "cinematic",
        "moods": ["powerful", "hopeful", "emotional"],
        "hook_examples": [
            "Do not quit now",
            "You are closer than you think",
            "One day can change everything",
        ]
    },
    "tech": {
        "name": "Tech and AI Reels",
        "folders": [
            "backgrounds", "quotes", "nature_pics",
        ],
        "music_folder":   "cinematic",
        "music_fallback": "ambient",
        "moods": ["cinematic", "peaceful", "powerful"],
        "hook_examples": [
            "This AI tool saves hours",
            "You need this workflow",
            "This changes everything",
        ]
    },
    "swahili": {
        "name": "Swahili Reels",
        "folders": [
            "africa", "nature", "backgrounds",
            "people_worshiping", "people_grateful", "nature_pics",
        ],
        "music_folder":   "swahili",
        "music_fallback": "worship",
        "moods": ["peaceful", "hopeful", "emotional"],
        "hook_examples": [
            "Usikate tamaa",
            "Sikiliza hii kwa makini",
            "Mungu hajakuacha",
            "Yeye anakupenda",
        ]
    },
})
'''
    content += niche_extra
    print('Extended NICHE_CONFIG added!')
else:
    print('Extended NICHE_CONFIG already exists')

settings.write_text(content, encoding='utf-8')
print('')
print('settings.py update complete!')
