import asyncio
import sounddevice as sd
import numpy as np
from groq import AsyncGroq
import queue

# 1. Async Queue for audio chunks
audio_queue = asyncio.Queue()

def audio_callback(indata, frames, time, status):
    """Called by sounddevice for every audio block."""
    if status:
        print(status)
    # Put a copy of the audio data into the async queue
    asyncio.run_coroutine_threadsafe(audio_queue.put(indata.copy()), loop)

async def capture_audio():
    """Start the mic stream and fill the queue."""
    with sd.InputStream(samplerate=16000, channels=1, dtype='int16',
                        callback=audio_callback, blocksize=1024):
        while True:
            await asyncio.sleep(0.01) # Keep the stream alive

async def transcribe_stream():
    """Pull chunks from the queue and send to Groq."""
    client = AsyncGroq(api_key="YOUR_GROQ_API_KEY")

    buffer = []
    while True:
        # Wait for a new audio chunk
        chunk = await audio_queue.get()
        buffer.append(chunk)

        # Accumulate ~500ms of audio before sending
        # 16000 Hz * 0.5s = 8000 samples
        if sum(len(c) for c in buffer) >= 8000:
            audio_data = np.concatenate(buffer)
            buffer = [] # Reset buffer

            # Convert to bytes (WAV-like header not needed if we tell Groq the format)
            audio_bytes = audio_data.tobytes()

            # Send to Groq (file-like object from bytes)
            transcription = await client.audio.transcriptions.create(
                file=("chunk.wav", audio_bytes, "audio/wav"),
                model="whisper-large-v3-turbo",
                response_format="text"
            )
            print(f"Partial: {transcription}") # Update your UI here

async def main():
    # Run both tasks concurrently
    await asyncio.gather(capture_audio(), transcribe_stream())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
