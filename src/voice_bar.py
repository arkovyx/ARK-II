import os
import sys
import json
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
import sounddevice as sd
import soundfile as sf

load_dotenv()

# --- Config ---
SAMPLE_RATE = 48000
RECORD_SECONDS = 5
TEMP_WAV = Path("/tmp/ark_voice.wav")
LOG_FILE = Path("/tmp/ark_stt_log.txt")
LOCK_FILE = Path("/tmp/ark_voice.lock")
LAST_RUN_FILE = Path("/tmp/ark_voice_last.txt")
COMMANDS_FILE = Path(__file__).resolve().parent.parent / "data" / "commands.json"

# Minimum time between triggers (seconds) — prevents double-fire
MIN_INTERVAL = 2.0


def notify(title, message, timeout_ms=1500):
    subprocess.run(
        ["notify-send", "-t", str(timeout_ms), title, message],
        check=False,
    )


def acquire_lock():
    """Return True if we got the lock, False if another instance is running."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            # Check if process is alive
            os.kill(pid, 0)
            return False   # still running
        except (ValueError, OSError):
            pass           # stale, take over
    LOCK_FILE.write_text(str(os.getpid()))
    return True


def release_lock():
    try:
        LOCK_FILE.unlink()
    except Exception:
        pass


def check_rate_limit():
    """Prevent double-fires within MIN_INTERVAL seconds."""
    now = time.time()
    if LAST_RUN_FILE.exists():
        try:
            last = float(LAST_RUN_FILE.read_text().strip())
            if now - last < MIN_INTERVAL:
                return False   # too soon — exit silently
        except Exception:
            pass
    LAST_RUN_FILE.write_text(str(now))
    return True


def record_audio():
    notify("🎤 ARK", "Recording...", 800)
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    sf.write(str(TEMP_WAV), audio, SAMPLE_RATE)
    notify("✅ ARK", "Recorded", 700)


def transcribe(path):
    notify("🧠 ARK", "Transcribing...", 800)
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    with open(path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(path.name, f.read()),
            model="whisper-large-v3",
            language="en",
            response_format="text",
            temperature=0.0,
            prompt=(
                "Commands for a personal AI assistant. "
                "Common commands: clone this repository, git clone, "
                "download this video, save this YouTube video, "
                "summarize this page, analyze this page, "
                "set a reminder, set an alarm, check the news, "
                "setup my dev environment, let's watch mr robot. "
                "Technical words: GitHub, git, repository, repo, "
                "YouTube, video, browser, terminal, download, clone, "
                "summary, article, webpage. "
                "Ignore silence and background noise — do not transcribe "
                "phrases like 'thanks for watching' or 'please subscribe'."
            ),
        )
    return str(result).strip()


def send_to_ark(text):
    cmds = []
    if COMMANDS_FILE.exists() and COMMANDS_FILE.stat().st_size > 0:
        try:
            with open(COMMANDS_FILE) as f:
                cmds = json.load(f)
        except Exception:
            cmds = []
    cmds.append(text)
    COMMANDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COMMANDS_FILE, "w") as f:
        json.dump(cmds, f, indent=2)


def main():
    # --- Guard 1: rate limit ---
    if not check_rate_limit():
        return

    # --- Guard 2: lock (only one instance) ---
    if not acquire_lock():
        return

    try:
        record_audio()
        text = transcribe(TEMP_WAV)
        print(f"[voice_bar] Whisper heard: {text}")

        try:
            with open(LOG_FILE, "a") as f:
                f.write(text + "\n")
        except Exception:
            pass

        # Filter hallucinations
        hallucinations = {
            "thanks for watching", "thank you for watching",
            "please subscribe", "like and subscribe",
            "subscribe to my channel", "see you next time",
            "bye bye", "you", "thank you", "thanks",
            "thank you.", "thanks.", "bye.", "you.",
            ".",
        }
        cleaned = text.lower().strip().strip(".!?,")
        if cleaned in hallucinations or len(text) < 3:
            notify("🤷 ARK", "Nothing meaningful heard")
            return

        notify("👤 You", text, 2000)
        send_to_ark(text)

    finally:
        release_lock()


if __name__ == "__main__":
    main()
