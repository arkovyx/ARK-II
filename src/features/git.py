import subprocess
import threading
from pathlib import Path

GIT_DIR = Path.home() / ".ark" / "git"
GIT_DIR.mkdir(parents=True, exist_ok=True)


def _notify(title, message):
    subprocess.run(["notify-send", title, message], check=False)


def _do_clone(url):
    try:
        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
        target = GIT_DIR / repo_name
        if target.exists():
            _notify("⚠️ ARK", f"{repo_name} already exists")
            return
        subprocess.run(
            ["git", "clone", url, str(target)],
            check=True, capture_output=True, timeout=300
        )
        _notify("✅ ARK", f"Cloned: {repo_name}")
    except subprocess.CalledProcessError as e:
        _notify("❌ ARK", f"Clone failed: {e.stderr.decode()[:60]}")
    except Exception as e:
        _notify("❌ ARK", f"Clone failed: {str(e)[:60]}")


def clone_repo(url):
    """Clone in background, return immediately."""
    if not url:
        return "No repo URL"
    _notify("📦 ARK", "Cloning repo...")
    t = threading.Thread(target=_do_clone, args=(url,), daemon=True)
    t.start()
    return "📦 Cloning in background"
