import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.features.screen import capture_screen

load_dotenv()


def _notify(title, message):
    import subprocess
    subprocess.run(["notify-send", title, message], check=False)


def read_and_fix_error():
    """Capture screen, send to Gemini Vision, return the fix."""
    _notify("📸 ARK-II", "Capturing screen...")

    png = capture_screen()
    if not png:
        return "❌ Couldn't take screenshot. Is grim installed?"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "❌ GEMINI_API_KEY missing in .env"

    _notify("🧠 ARK-II", "Analyzing...")

    try:
        client = genai.Client(api_key=api_key)
        image_bytes = png.read_bytes()

        prompt = (
            "Look at this screenshot and find any error, exception, or stack trace. "
            "Then respond in this exact format:\n\n"
            "**Error:** <one-line description>\n\n"
            "**Cause:** <one-line explanation>\n\n"
            "**Fix:**\n<concrete steps or code>\n\n"
            "Be concise and specific. If there's no error visible, "
            "say exactly: 'No error detected on screen.'"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt,
            ],
        )

        text = response.text.strip() if response.text else "No response from AI."
        _notify("✅ ARK-II", "Analysis done")
        return text

    except Exception as e:
        return f"❌ AI error: {e}"
