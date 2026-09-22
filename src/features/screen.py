import subprocess
from pathlib import Path

TEMP_PNG = Path("/tmp/ark_screen.png")


def capture_screen():
    """
    Capture the full screen. Returns Path or None.
    Tries grim first (fast, wayland-native), falls back to hyprshot.
    """
    TEMP_PNG.unlink(missing_ok=True)

    # Try grim
    try:
        r = subprocess.run(
            ["grim", str(TEMP_PNG)],
            capture_output=True, timeout=5,
        )
        if r.returncode == 0 and TEMP_PNG.exists():
            return TEMP_PNG
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # Fallback: hyprshot
    try:
        subprocess.run(
            ["hyprshot", "-m", "output", "-o", "/tmp", "-f", "ark_screen.png"],
            capture_output=True, timeout=10,
        )
        if TEMP_PNG.exists():
            return TEMP_PNG
    except Exception:
        pass

    return None
