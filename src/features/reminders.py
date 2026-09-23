import json
import time
import uuid
import threading
import subprocess
from pathlib import Path
from src.utils.paths import DATA_DIR

REMINDERS_FILE = DATA_DIR / "reminders.json"
_checker_thread = None
_stop_event = threading.Event()


def _load():
    if not REMINDERS_FILE.exists() or REMINDERS_FILE.stat().st_size == 0:
        return []
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = REMINDERS_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(REMINDERS_FILE)


def _notify(title, message):
    try:
        subprocess.run(["notify-send", title, message], check=False, timeout=3)
    except Exception:
        pass


def _speak(text):
    try:
        from src.features.tts import speak
        speak(text)
    except Exception:
        pass


def add_reminder(message, seconds_from_now):
    data = _load()
    item = {
        "id": str(uuid.uuid4())[:8],
        "type": "reminder",
        "message": message,
        "trigger_at": time.time() + seconds_from_now,
        "created_at": time.time(),
        "fired": False,
    }
    data.append(item)
    _save(data)
    return item


def add_alarm(message, target_timestamp):
    data = _load()
    item = {
        "id": str(uuid.uuid4())[:8],
        "type": "alarm",
        "message": message,
        "trigger_at": target_timestamp,
        "created_at": time.time(),
        "fired": False,
    }
    data.append(item)
    _save(data)
    return item


def list_pending():
    data = _load()
    return [r for r in data if not r.get("fired")]


def delete_reminder(reminder_id):
    data = _load()
    new_data = [r for r in data if r.get("id") != reminder_id]
    if len(new_data) == len(data):
        return False
    _save(new_data)
    return True


def clear_all():
    _save([])


def _checker_loop():
    while not _stop_event.is_set():
        try:
            now = time.time()
            data = _load()
            changed = False

            for item in data:
                if item.get("fired"):
                    continue
                if item["trigger_at"] <= now:
                    # Fire!
                    item["fired"] = True
                    changed = True
                    label = "⏰ Reminder" if item["type"] == "reminder" else "⏱️ Alarm"
                    _notify(f"{label}: {item['message']}", "")
                    _speak(item["message"])

            if changed:
                _save(data)

        except Exception as e:
            print(f"reminder checker error: {e}")

        # Check every 2 seconds
        _stop_event.wait(2)


def start_checker():
    global _checker_thread
    if _checker_thread and _checker_thread.is_alive():
        return
    _stop_event.clear()
    _checker_thread = threading.Thread(target=_checker_loop, daemon=True)
    _checker_thread.start()


def stop_checker():
    _stop_event.set()
