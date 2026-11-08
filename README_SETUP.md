# VideoFactory — Quick Setup Reference

## First Time Setup (Windows)

1. Install Python 3.10+ from python.org (check "Add to PATH")
2. Install Git from git-scm.com
3. Install FFmpeg — extract to C:\ffmpeg, add C:\ffmpeg\bin to PATH
4. Clone repo: `git clone <your-repo-url>`
5. Create venv: `python -m venv venv`
6. Activate: `call venv\Scripts\activate`
7. Install deps: `pip install -r requirements.txt`
8. Install Playwright: `playwright install chrome`
9. Copy `.env.example` to `.env` and fill in your API keys
10. Create your asset folders (they are gitignored):
    - assets/music/worship/
    - assets/stock/gospel/
    - assets/stock/nature/
    - etc.
11. Verify setup: `python main.py --list`
12. Start dashboard: `python src/web/server.py`
13. Open browser: http://localhost:8000

## Daily Git Workflow

```cmd
git add .
git commit -m "what you changed today"
git push origin main
```

## IMPORTANT: What Is NOT in Git
- assets/ folders (music, stock images/videos) — too large
- output/ folder (generated videos, audio) — too large
- .env file (contains your API keys — never commit)
- venv/ folder (install fresh with pip install -r requirements.txt)

## If Starting on a New PC or VPS
- Clone the repo
- Re-download your asset packs manually to assets/
- Copy your .env file manually (never commit it)
- Run through First Time Setup steps above

## Common Fixes
- Audio/video out of sync: Check TRANSITION_DURATION = 0.20 in config/settings.py
- FFmpeg not found: set FFMPEG_BINARY=C:\ffmpeg\bin\ffmpeg.exe
- Playwright login loop: Delete assets/browser_profiles/{platform} and re-login
- Always use cmd.exe not PowerShell
