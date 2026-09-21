import json
import time
from pathlib import Path
from src.utils.paths import DATA_DIR

COMMAND_FILE = DATA_DIR / "commands.json"


def _ensure_file():
    if not COMMAND_FILE.exists():
        with open(COMMAND_FILE, "w") as f:
            json.dump([], f)


def read_new_commands():
    """
    Return list of unprocessed commands from web.
    Clears the file after reading.
    """
    _ensure_file()
    try:
        with open(COMMAND_FILE, "r") as f:
            commands = json.load(f)
    except Exception:
        return []

    if not commands:
        return []

    # Clear file after reading
    with open(COMMAND_FILE, "w") as f:
        json.dump([], f)

    return commands


def get_last_read():
    return time.time()
