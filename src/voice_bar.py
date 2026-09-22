import os
import json
import subprocess
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
COMMANDS_FILE = Path(__file__).resolve().parent.parent / "data" / "commands.json"


def notify(title, message, timeout_ms=1500):
    subprocess.run(
        ["notify-send", "-t", str(timeout_ms), title, message],
        check=False,
    )


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
                "Common actions: clone this repository, git clone, "
                "download this video, save this YouTube video, "
                "summarize this page, summarize this file, "
                "set a reminder, set an alarm, check the news. "
                "Technical words: GitHub, git, repository, repo, "
                "YouTube, video, browser, terminal, download, clone, "
                "summary, article, webpage, url, link."
            ),
        )
    return str(result).strip()


def send_to_ark(text):
    """Write to commands.json — ARK's web_poll_loop picks it up."""
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
    # 1. Record
    record_audio()

    # 2. Transcribe
    text = transcribe(TEMP_WAV)
    print(f"[voice_bar] Whisper heard: {text}")

    from pathlib import Path
    log = Path("/tmp/ark_stt_log.txt")
    with open(log, "a") as f:
        f.write(f"{text}\n")

    if not text or len(text) < 3:
        notify("ARK", "Nothing heard")
        return
    notify("YOU", text, 2000)
    send_to_ark(text)

    # 3. Validate
    if not text or len(text) < 3:
        notify("🤷 ARK", "Nothing heard")
        return

    # 4. Send
    notify("👤 You", text, 2000)
    send_to_ark(text)


if __name__ == "__main__":
    main()
