import subprocess
from pathlib import Path

INTRO_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "ark_intro.wav"


def play_intro():
    if not INTRO_FILE.exists():
        return f"❌ Intro not found: {INTRO_FILE}. Run scripts/make_intro.py first."

    try:
        subprocess.Popen(
            ["mpv", "--no-video", "--really-quiet", str(INTRO_FILE)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "intro..."
    except FileNotFoundError:
        return "❌ an error occured"
    except Exception as e:
        return f"❌ error: {e}"
