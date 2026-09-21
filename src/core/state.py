import json
import time
from src.utils.paths import STATE_FILE

_state = {
    "status": "idle",
    "history": [],
    "tts": {"playing": False, "text": "", "started_at": 0},
    "started_at": 0,
    "updated_at": "",
}

MAX_HISTORY = 50


def _write():
    _state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(_state, f, indent=2)
    tmp.replace(STATE_FILE)


def init():
    _state["status"] = "idle"
    _state["tts"]["playing"] = False
    _state["tts"]["text"] = ""
    _state["tts"]["started_at"] = 0
    _state["started_at"] = time.time()
    _write()


def set_status(status):
    _state["status"] = status
    _write()


def append_history(role, content):
    _state["history"].append({
        "role": role,
        "content": content,
        "time": time.strftime("%H:%M"),
    })
    if len(_state["history"]) > MAX_HISTORY:
        _state["history"] = _state["history"][-MAX_HISTORY:]
    _write()


def clear_history():
    _state["history"] = []
    _write()


def set_tts(playing, text=""):
    _state["tts"]["playing"] = playing
    _state["tts"]["text"] = text
    _state["tts"]["started_at"] = time.time() if playing else 0
    _write()
