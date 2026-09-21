from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path
import json

app = Flask(__name__, static_folder="web")

DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "state.json"
COMMANDS_FILE = DATA_DIR / "commands.json"

DEFAULT_STATE = {
    "status": "idle",
    "history": [],
    "tts": {"playing": False, "text": "", "started_at": 0},
    "updated_at": "",
}


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/chat")
def chat_page():
    return send_from_directory("web", "chat.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("web", path)


@app.route("/state")
def get_state():
    if not STATE_FILE.exists():
        return jsonify(DEFAULT_STATE)
    try:
        with open(STATE_FILE, "r") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify(DEFAULT_STATE)


@app.route("/command", methods=["POST"])
def post_command():
    data = request.get_json(silent=True) or {}
    cmd = data.get("command", "").strip()
    if not cmd:
        return jsonify({"ok": False, "error": "empty"}), 400

    commands = []
    if COMMANDS_FILE.exists():
        try:
            with open(COMMANDS_FILE, "r") as f:
                commands = json.load(f)
        except Exception:
            commands = []

    commands.append(cmd)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(COMMANDS_FILE, "w") as f:
        json.dump(commands, f, indent=2)

    return jsonify({"ok": True, "queued": cmd})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
