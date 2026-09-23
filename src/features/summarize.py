import subprocess
from pathlib import Path
from src.features.get import get_active_window, get_last_browser_url


def get_active_content():
    window = get_active_window()
    if not window:
        return "none", None

    cls = window["class"]

    if any(b in cls for b in ["librewolf", "firefox", "chromium", "brave", "chrome"]):
        url, title = get_last_browser_url()
        if url:
            return "url", {"url": url, "title": title}
        return "none", None

    if any(e in cls for e in ["nvim", "neovim", "code", "zed", "sublime"]):
        title = window["title"]
        # nvim title format: "filename - Neovim"
        # code title format: "filename — project — Code"
        filename = title.split(" - ")[0].split(" — ")[0].strip()
        if filename:
            pid = window["pid"]
            try:
                cwd = subprocess.check_output(
                    ["readlink", f"/proc/{pid}/cwd"], text=True
                ).strip()
                full_path = Path(cwd) / filename
                if full_path.exists():
                    return "file", {"path": str(full_path), "name": filename}
            except Exception:
                pass
            return "file", {"path": filename, "name": filename}

    return "none", None
