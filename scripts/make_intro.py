import os
import wave
import base64
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIMARY_KEY = os.getenv("GEMINI_API_KEY_1")
# BACKUP_KEY = os.getenv("GEMINI_API_KEY_BACKUP")

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "ark_intro.wav"

# ============================================
# INTRODUCTION
# ============================================
INTRO_SCRIPT = """
Hi, I am ark — your personal AI assistant.

I live where you work. Not in a browser tab. Not in a cloud.

I remember you. I read what you're looking at. I search the web in real time.

And I don't just chat — I act. I download. I clone. I scaffold projects. I launch your environment.

This is what a personal AI should be. Local-first. Voice-first. Built for developers.

Let's begin.
"""

VOICE = "Charon"     # try "Orus" or "Algenib" for a deeper tone
MODEL = "gemini-2.5-flash-preview-tts"


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
    try:
        _synthesize(INTRO_SCRIPT.strip(), PRIMARY_KEY)
        print(f"Intro saved: {OUTPUT}")
    except Exception as e:
        print(f"Primary failed: {e}")
        if BACKUP_KEY:
            _synthesize(INTRO_SCRIPT.strip(), BACKUP_KEY)
            print(f"Intro saved (backup key): {OUTPUT}")
        else:
            raise
