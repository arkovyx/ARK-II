from pathlib import Path

# ============================================
# PATHS
# ============================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data folder
DATA_DIR       = PROJECT_ROOT / "data"
MEMORY_FILE    = DATA_DIR / "memory.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"
STATE_FILE     = DATA_DIR / "state.json"

# Downloads
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
YT_DIR        = DOWNLOADS_DIR / "yt"
GIT_DIR       = DOWNLOADS_DIR / "git"

# Ensure folders exist
for d in [DATA_DIR, YT_DIR, GIT_DIR]:
    d.mkdir(parents=True, exist_ok=True)
