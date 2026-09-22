import os
import re
import json
import subprocess
from pathlib import Path

# ============================================
# CONFIG — EDIT THESE
# ============================================
MEDIA_ROOT = Path.home() / "data" / "media"
PROGRESS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "media_progress.json"
PLAYER = "mpv"

# Aliases — what you say → what folder it maps to
SHOWS = {
    "mr robot": "1.Mr-Robot",
    "mr. robot": "1.Mr-Robot",
    "mister robot": "1.Mr-Robot",
}


# ============================================
# HELPERS
# ============================================
def _notify(title, message, timeout_ms=3000):
    subprocess.run(
        ["notify-send", "-t", str(timeout_ms), title, message],
        check=False,
    )


def _load_progress():
    if not PROGRESS_FILE.exists() or PROGRESS_FILE.stat().st_size == 0:
        return {}
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_progress(data):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _find_episodes(show_folder):
    """Return sorted list of video files in the show folder."""
    show_dir = MEDIA_ROOT / show_folder
    if not show_dir.exists():
        return []

    videos = []
    for season_dir in sorted(show_dir.iterdir()):
        if not season_dir.is_dir():
            continue
        for f in sorted(season_dir.iterdir()):
            if f.suffix.lower() in (".mkv", ".mp4", ".avi", ".webm", ".mov"):
                videos.append(f)
    return videos


def _episode_key(path):
    """Unique key for a video file (show/season/episode)."""
    return str(path.relative_to(MEDIA_ROOT))


# ============================================
# THE MAIN FEATURE
# ============================================
def watch_show(query):
    """
    Find the show, pick the next unwatched episode, and play it.
    """
    query_lower = query.lower().strip()

    # Find which show the user means
    matched_show = None
    for alias, folder in SHOWS.items():
        if alias in query_lower:
            matched_show = folder
            break

    if not matched_show:
        available = ", ".join(SHOWS.keys())
        return f"❌ Don't know that show. Try: {available}"

    # Find episodes
    episodes = _find_episodes(matched_show)
    if not episodes:
        return f"❌ No episodes found in: {MEDIA_ROOT / matched_show}"

    # Load progress
    progress = _load_progress()
    watched = progress.get(matched_show, [])

    # Pick first unwatched
    next_ep = None
    for ep in episodes:
        key = _episode_key(ep)
        if key not in watched:
            next_ep = ep
            break

    # All watched → restart from first? Or say done?
    if not next_ep:
        return f"✅ You've finished all {len(episodes)} episodes of {matched_show}!"

    # Play it
    _notify("▶️ ARK-II", f"Playing: {next_ep.name[:60]}")

    subprocess.Popen(
        [PLAYER, str(next_ep)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Mark as watched immediately (or you can mark on completion — harder)
    watched.append(_episode_key(next_ep))
    progress[matched_show] = watched
    _save_progress(progress)

    ep_num = len(watched)
    total = len(episodes)
    return f"▶️ Playing {matched_show} — episode {ep_num}/{total}\n   {next_ep.name[:70]}"


def mark_watched(show_query):
    """Mark the most recent episode as watched (if you stopped early)."""
    # Not implemented yet — just plays next on next watch call
    return "Use 'watch <show>' to continue"
