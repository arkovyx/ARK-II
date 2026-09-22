import subprocess
import time
from datetime import datetime
from pathlib import Path

# ============================================
# CONFIG — EDIT THESE TO MATCH YOUR SETUP
# ============================================
TERMINAL = "foot"
BROWSER = "librewolf"

# Your project directory
REPO_PATH = Path.home() / "dev" / "ark-ii_understanding"

# URLs to open (edit these)
URLS = [
    "https://wiki.archlinux.org/title/Hyprland",
    "https://github.com/arkovyx/ark-ii/",
    "https://docs.python.org/3/",
    "https://mail.proton.me/u/0/inbox?welcome=true",
]

# DND script to run in background
DND_SCRIPT = Path.home() / ".config" / "waybar" / "scripts" / "dnd.sh"


# ============================================
# HELPERS
# ============================================
def _notify(title, message, timeout_ms=4000):
    subprocess.run(
        ["notify-send", "-t", str(timeout_ms), title, message],
        check=False,
    )


def _launch_terminal(command, title="ark-dev"):
    """Launch a foot terminal running a command, then keep shell open."""
    subprocess.Popen(
        [
            TERMINAL,
            "--title", title,
            "-e", "zsh", "-i", "-c", f"{command}; exec zsh",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ============================================
# THE MAIN WORKFLOW
# ============================================
def setup_dev_environment():
    """
    Launch your full dev environment:
      1. Terminal 1: cd into repo
      2. Terminal 2: lazygit
      3. Terminal 3: nvim in repo
      4. Browser with project URLs
      5. Toggle DND on
      6. Notify with timestamp
    """
    if not REPO_PATH.exists():
        return f"❌ Repo not found: {REPO_PATH}"

    # 1. Terminal 1 — cd into repo
    _launch_terminal(f"cd {REPO_PATH} && lf", title="ark-term-1")
    time.sleep(0.4)

    # 2. Terminal 2 — lazygit
    _launch_terminal(f"cd {REPO_PATH} && lazygit", title="ark-lazygit")
    time.sleep(0.4)

    # 3. Terminal 3 — nvim in repo
    _launch_terminal(f"cd {REPO_PATH} && nvim", title="ark-nvim")
    time.sleep(0.6)

    # 4. Browser with all URLs
    try:
        subprocess.Popen(
            [BROWSER] + URLS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    # 5. DND on
    if DND_SCRIPT.exists():
        subprocess.Popen(
            ["bash", str(DND_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # 6. Notification with time
    now = datetime.now().strftime("%I:%M %p")
    _notify("🚀 ARK-II", f"Dev environment ready — started at {now}")

    return f"🚀 Dev environment launched at {now}"


def setup_docs_environment():
    """Lighter version — just browser + DND."""
    try:
        subprocess.Popen([BROWSER] + URLS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    if DND_SCRIPT.exists():
        subprocess.Popen(["bash", str(DND_SCRIPT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    now = datetime.now().strftime("%I:%M %p")
    _notify("📚 ARK-II", f"Docs mode at {now}")
    return f"📚 Docs environment launched at {now}"
