# -*- coding: utf-8 -*-
"""
src/utils/cleanup.py — VideoFactory Output Cleanup Utility

Manages disk space by archiving old videos and deleting temp files.
Provides CLI, FastAPI endpoints, and can run as a scheduled task.

Usage (CLI):
    python -m src.utils.cleanup --dry-run --days 30
    python -m src.utils.cleanup --temp-only
    python -m src.utils.cleanup --all
"""

import os
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# ─── Config Defaults ──────────────────────────────────────────────────────────
_ENV_CACHE: dict = {}

def _get_env(key: str, default: str = "") -> str:
    if not _ENV_CACHE:
        p = Path(".env")
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    _ENV_CACHE[k.strip()] = v.strip()
    return _ENV_CACHE.get(key, default)

OUTPUT_BASE  = Path(_get_env("OUTPUT_DIR", "output"))
VIDEOS_DIR   = OUTPUT_BASE / "videos"
TEMP_DIR     = OUTPUT_BASE / "temp"
ARCHIVE_DIR  = OUTPUT_BASE / "archive"

MAX_VIDEO_AGE_DAYS  = int(_get_env("MAX_VIDEO_AGE_DAYS", "30"))
TEMP_MAX_AGE_DAYS   = int(_get_env("TEMP_FILE_MAX_AGE_DAYS", "7"))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _age_days(path: Path) -> float:
    """Returns the age of a file in days (float)."""
    mtime = path.stat().st_mtime
    return (time.time() - mtime) / 86400


def _human_size(total_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if total_bytes < 1024:
            return f"{total_bytes:.1f} {unit}"
        total_bytes /= 1024
    return f"{total_bytes:.1f} TB"


def _folder_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


# ─── Core Functions ───────────────────────────────────────────────────────────

def cleanup_temp_older_than(days: int = TEMP_MAX_AGE_DAYS, dry_run: bool = False) -> dict:
    """
    Deletes files in output/temp/ older than `days` days.

    Returns:
        dict with keys: deleted_count, freed_bytes, skipped_count
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    deleted, freed, skipped = 0, 0, 0
    cutoff = days

    for f in TEMP_DIR.rglob("*"):
        if not f.is_file():
            continue
        age = _age_days(f)
        if age > cutoff:
            size = f.stat().st_size
            if not dry_run:
                try:
                    f.unlink()
                    deleted += 1
                    freed += size
                except Exception as e:
                    print(f"  Warning: could not delete {f.name}: {e}")
                    skipped += 1
            else:
                print(f"  [DRY-RUN] Would delete: {f.name} ({_human_size(size)}, {age:.0f}d old)")
                deleted += 1
                freed += size
        else:
            skipped += 1

    return {"deleted_count": deleted, "freed_bytes": freed, "skipped_count": skipped, "dry_run": dry_run}


def archive_old_videos(days: int = MAX_VIDEO_AGE_DAYS, dry_run: bool = False) -> dict:
    """
    Moves videos older than `days` days from output/videos/ to output/archive/.

    Returns:
        dict with keys: archived_count, freed_bytes, skipped_count
    """
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archived, freed, skipped = 0, 0, 0

    for f in VIDEOS_DIR.glob("*.mp4"):
        age = _age_days(f)
        if age > days:
            size = f.stat().st_size
            dest = ARCHIVE_DIR / f.name
            if not dry_run:
                try:
                    shutil.move(str(f), str(dest))
                    archived += 1
                    freed += size
                except Exception as e:
                    print(f"  Warning: could not archive {f.name}: {e}")
                    skipped += 1
            else:
                print(f"  [DRY-RUN] Would archive: {f.name} ({_human_size(size)}, {age:.0f}d old)")
                archived += 1
                freed += size
        else:
            skipped += 1

    return {"archived_count": archived, "freed_bytes": freed, "skipped_count": skipped, "dry_run": dry_run}


def cleanup_failed_renders(dry_run: bool = False) -> dict:
    """
    Deletes .FAILED, .tmp, and broken partial renders from output/.

    Returns:
        dict with keys: deleted_count, freed_bytes
    """
    FAIL_PATTERNS = ["*.FAILED", "*.tmp", "*TEMP_MPY_wvf_snd.mp4", "*.partial"]
    deleted, freed = 0, 0

    for pattern in FAIL_PATTERNS:
        for f in OUTPUT_BASE.rglob(pattern):
            if not f.is_file():
                continue
            size = f.stat().st_size
            if not dry_run:
                try:
                    f.unlink()
                    deleted += 1
                    freed += size
                except Exception as e:
                    print(f"  Warning: could not delete {f.name}: {e}")
            else:
                print(f"  [DRY-RUN] Would delete failed render: {f.name} ({_human_size(size)})")
                deleted += 1
                freed += size

    return {"deleted_count": deleted, "freed_bytes": freed, "dry_run": dry_run}


def get_disk_usage_summary() -> dict:
    """
    Returns a dict mapping folder names to human-readable sizes.

    Example:
        {"videos": "145.3 MB", "temp": "12.1 MB", "archive": "890.0 MB", ...}
    """
    subdirs = {
        "videos":     VIDEOS_DIR,
        "temp":       TEMP_DIR,
        "archive":    ARCHIVE_DIR,
        "audio":      OUTPUT_BASE / "audio",
        "subtitles":  OUTPUT_BASE / "subtitles",
        "thumbnails": OUTPUT_BASE / "thumbnails",
        "lyrics":     OUTPUT_BASE / "lyrics",
    }
    summary = {}
    total = 0
    for name, path in subdirs.items():
        size = _folder_size(path)
        total += size
        summary[name] = _human_size(size)

    summary["__total__"] = _human_size(total)
    return summary


def run_full_cleanup(days: int = MAX_VIDEO_AGE_DAYS, temp_days: int = TEMP_MAX_AGE_DAYS, dry_run: bool = False) -> dict:
    """
    Runs all cleanup operations and returns a combined report.
    """
    print("\n=== VideoFactory Cleanup ===")
    print(f"  Archive videos older than: {days}d")
    print(f"  Delete temp older than:    {temp_days}d")
    print(f"  Dry run: {dry_run}\n")

    temp_result    = cleanup_temp_older_than(days=temp_days, dry_run=dry_run)
    archive_result = archive_old_videos(days=days, dry_run=dry_run)
    failed_result  = cleanup_failed_renders(dry_run=dry_run)
    disk_summary   = get_disk_usage_summary()

    total_freed = temp_result["freed_bytes"] + archive_result["freed_bytes"] + failed_result["freed_bytes"]

    report = {
        "temp_files":       temp_result,
        "archived_videos":  archive_result,
        "failed_renders":   failed_result,
        "disk_usage":       disk_summary,
        "total_freed":      _human_size(total_freed),
        "dry_run":          dry_run,
    }

    print(f"\n=== Results ===")
    print(f"  Temp files deleted:   {temp_result['deleted_count']} ({_human_size(temp_result['freed_bytes'])})")
    print(f"  Videos archived:      {archive_result['archived_count']} ({_human_size(archive_result['freed_bytes'])})")
    print(f"  Failed renders found: {failed_result['deleted_count']} ({_human_size(failed_result['freed_bytes'])})")
    print(f"  Total freed:          {_human_size(total_freed)}")

    return report


# ─── CLI Entrypoint ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VideoFactory Disk Cleanup Utility")
    parser.add_argument("--dry-run",    action="store_true", help="Preview what would be deleted/archived")
    parser.add_argument("--days",       type=int, default=MAX_VIDEO_AGE_DAYS, help="Archive videos older than N days")
    parser.add_argument("--temp-days",  type=int, default=TEMP_MAX_AGE_DAYS,  help="Delete temp files older than N days")
    parser.add_argument("--temp-only",  action="store_true", help="Only clean temp files, don't touch videos")
    parser.add_argument("--stats",      action="store_true", help="Just show disk usage, no cleanup")
    args = parser.parse_args()

    if args.stats:
        summary = get_disk_usage_summary()
        print("\n=== Disk Usage Summary ===")
        for k, v in summary.items():
            label = k.replace("__", "").capitalize() if k.startswith("__") else f"  {k}"
            print(f"  {label:12s}: {v}")
    elif args.temp_only:
        result = cleanup_temp_older_than(days=args.temp_days, dry_run=args.dry_run)
        print(f"Temp cleanup: {result['deleted_count']} files, {_human_size(result['freed_bytes'])} freed")
    else:
        run_full_cleanup(days=args.days, temp_days=args.temp_days, dry_run=args.dry_run)
