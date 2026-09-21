import os, json, subprocess, time
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
TEMP_WAV = Path("/tmp/ark_voice.wav")
COMMANDS_FILE = Path(__file__).resolve().parent.parent / "data" / "commands.json"
SAMPLE_RATE = 16000
RECORD_SECONDS = 5


def notify(t, m, ms=1500):
    subprocess.run(["notify-send", "-t", str(ms), t, m], check=False)


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
    notify("🎤 ARK", "Listening...", 800)

    # Record 5 seconds — same as the working test
    audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE),
                   samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    sf.write(str(TEMP_WAV), audio, SAMPLE_RATE)

    notify("🧠 ARK", "Transcribing...", 800)

    # Same STT call as the working test
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    with open(TEMP_WAV, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(TEMP_WAV.name, f.read()),
            model="whisper-large-v3-turbo",
            language="en",
            response_format="text",
            temperature=0.0,
        )
    text = str(result).strip()

    if not text or len(text) < 3:
        notify("🤷 ARK", "Nothing heard")
        return

    notify("👤 You", text, 2000)
    send_to_ark(text)


if __name__ == "__main__":
    main()
