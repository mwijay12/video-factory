"""
Run this from the VideoFactory root to archive legacy scripts.
Usage: python archive_scripts.py
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

# Create archive directories
arch_fixes = ROOT / "_archive" / "legacy_fixes_2026"
arch_sync  = ROOT / "_archive" / "sync_experiments"
arch_fixes.mkdir(parents=True, exist_ok=True)
arch_sync.mkdir(parents=True, exist_ok=True)

moved = []
skipped = []

def move(src_name, dest_dir):
    src = ROOT / src_name
    if src.exists():
        shutil.move(str(src), str(dest_dir / src_name))
        moved.append(src_name)
    else:
        skipped.append(src_name)

# --- fix_*.py ---
for f in sorted(ROOT.glob("fix_*.py")):
    move(f.name, arch_fixes)

# --- patch_*.py ---
for f in sorted(ROOT.glob("patch_*.py")):
    move(f.name, arch_fixes)

# --- add_*.py ---
for name in ["add_method.py", "add_sync.py", "add_sync_v2.py"]:
    move(name, arch_sync)

# --- _run_*, _generate_* ---
for f in sorted(ROOT.glob("_run_*.py")):
    move(f.name, arch_fixes)
for f in sorted(ROOT.glob("_generate_*.py")):
    move(f.name, arch_fixes)

# --- Stray TEMP MP4s in root ---
stale_mp4s = list(ROOT.glob("*TEMP_MPY_wvf_snd.mp4"))
if stale_mp4s:
    output_dir = ROOT / "output" / "videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    for mp4 in stale_mp4s:
        shutil.move(str(mp4), str(output_dir / mp4.name))
        moved.append(f"(MP4) {mp4.name}")

# --- Write archive README ---
readme = arch_fixes.parent / "README.md"
readme.write_text(
    "# _archive/\n\n"
    "This directory contains historical scripts used during VideoFactory's\n"
    "development. They are kept for reference but are NOT part of the main application.\n\n"
    "## legacy_fixes_2026/\n"
    "One-off scripts that patched specific bugs during development (fix_*.py, patch_*.py, etc.).\n"
    "Most have been superseded by the proper implementation in src/.\n\n"
    "## sync_experiments/\n"
    "Experimental scripts for syncing MoviePy audio (add_sync.py, add_method.py).\n"
    "Superseded by src/video/video_engine.py.\n\n"
    "---\n"
    "Do not import or run these scripts in production.\n",
    encoding="utf-8"
)

# --- Write _archive/.gitignore ---
gitignore = arch_fixes.parent / ".gitignore"
gitignore.write_text(
    "# Archived legacy scripts - do not re-add to main\n*\n!README.md\n!.gitignore\n",
    encoding="utf-8"
)

print(f"\nMoved {len(moved)} files:")
for m in moved:
    print(f"   -> {m}")

if skipped:
    print(f"\nSkipped (not found): {skipped}")

print("\nCreated _archive/README.md and _archive/.gitignore")
print("\nRoot is now clean!")
