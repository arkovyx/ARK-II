"""
Simple live STT test.
Records for N seconds, sends to Groq Whisper, prints result.
Run repeatedly to compare.
"""
import os
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SAMPLE_RATE = 16000
RECORD_SECONDS = 5
TEMP_WAV = Path("/tmp/stt_test.wav")


def record():
    print(f"🎤 Recording for {RECORD_SECONDS}s — speak now...")
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    sf.write(str(TEMP_WAV), audio, SAMPLE_RATE)
    print("✅ Recorded")


def transcribe(model="whisper-large-v3"):
    with open(TEMP_WAV, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(TEMP_WAV.name, f.read()),
            model=model,
            language="en",
            response_format="text",
            temperature=0.0,
        )
    return str(result).strip()


def main():
    print("=== ARK STT Live Test ===")
    print("Press Ctrl+C to quit\n")

    while True:
        try:
            input("Press Enter to record > ")
            record()
            t0 = time.time()
            text = transcribe()
            elapsed = time.time() - t0
            print(f"📝 Whisper ({elapsed:.2f}s): {text}\n")

            # Optional: play back what was recorded
            # Uncomment to hear it
            # os.system("mpv --really-quiet /tmp/stt_test.wav")
        except KeyboardInterrupt:
            print("\n👋 Done")
            break


if __name__ == "__main__":
    main()
