import json
from src.utils.paths import MEMORY_FILE


def load():
    if not MEMORY_FILE.exists() or MEMORY_FILE.stat().st_size == 0:
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def remember(key, value):
    data = load()
    data[key] = value
    save(data)
    return f"Got it! Remembered: {key} = {value}"


def recall(key):
    data = load()
    if key in data:
        return data[key]
    return None


def forget(key):
    data = load()
    if key in data:
        del data[key]
        save(data)
        return f"Forgot: {key}"
    return f"I don't know anything about: {key}"


def list_all():
    data = load()
    if not data:
        return "I don't remember anything yet."

    output = "Memory:\n"
    for key, value in data.items():
        output += f"    • {key}: {value}\n"
    return output
