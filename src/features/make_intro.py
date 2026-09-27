import os
import wave
import base64
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ============================================
# CONFIG
# ============================================
PRIMARY_KEY = os.getenv("GEMINI_API_KEY_1")
BACKUP_KEY = os.getenv("GEMINI_API_KEY_BACKUP")

# Output file
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "ark_intro.wav"

# Voice — try "Charon", "Orus", or "Algenib"
VOICE = "Charon"

# Model
MODEL = "gemini-2.5-flash-preview-tts"

# ============================================
# INTRO SCRIPT — edit this to change what ARK says
# ============================================
INTRO_SCRIPT = """
I am ark. A voice-controlled AI assistant that automates daily developer tasks for you.

I can retain information across sessions. I can access real-time data. I can read the active window — the browser, the files currently in view.

Furthermore, I am not limited to conversation. I execute actions. I can download videos. I can clone repositories. I can scaffold python projects from scratch. I can launch complete development environments.

All through a single voice command. No context switching required.

Until then — sit back, and relax.
"""

def _save_wav(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def _synthesize(text, api_key):
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=MODEL,
        input=text,
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [{"voice": VOICE}]
        }
    )
    _save_wav(OUTPUT, base64.b64decode(interaction.output_audio.data))


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    text = INTRO_SCRIPT.strip()

    print(f"Generating intro with voice: {VOICE}")
    print(f"Output: {OUTPUT}")
    print()

    try:
        _synthesize(text, PRIMARY_KEY)
        print(f"✅ Intro saved: {OUTPUT}")
        print(f"   Size: {OUTPUT.stat().st_size // 1024} KB")
        print()
        print(f"   Listen with: mpv {OUTPUT}")
    except Exception as e:
        print(f"Primary key failed: {e}")
        if BACKUP_KEY:
            try:
                _synthesize(text, BACKUP_KEY)
                print(f"✅ Intro saved (backup key): {OUTPUT}")
                print(f"   Size: {OUTPUT.stat().st_size // 1024} KB")
            except Exception as e2:
                print(f"❌ Both keys failed: {e2}")
        else:
            print("❌ No backup key available")
            raise
