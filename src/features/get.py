import time
import subprocess
import json
import sqlite3
import glob
import shutil
from pathlib import Path


def get_active_window():
    try:
        r = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True, text=True, timeout=2
        )
        data = json.loads(r.stdout)
        if not data or "class" not in data:
            return None
        return {
            "class": data.get("class", "").lower(),
            "title": data.get("title", ""),
            "pid": data.get("pid", 0),
        }
    except Exception:
        return None


def _find_firefox_places():
    patterns = [
        # LibreWolf (newer, XDG-compliant)
        str(Path.home() / ".config" / "librewolf" / "librewolf" / "*.default*" / "places.sqlite"),

        # LibreWolf (older path)
        str(Path.home() / ".librewolf" / "*.default*" / "places.sqlite"),

        # LibreWolf Flatpak
        str(Path.home() / ".var" / "app" / "io.gitlab.librewolf-community" / ".librewolf" / "*.default*" / "places.sqlite"),

        # Firefox (XDG)
        str(Path.home() / ".config" / "mozilla" / "firefox" / "*.default*" / "places.sqlite"),

        # Firefox (older)
        str(Path.home() / ".mozilla" / "firefox" / "*.default*" / "places.sqlite"),
    ]
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            return matches[0]
    return None

IGNORED_URL_PARTS = [
    "127.0.0.1", "localhost", "0.0.0.0",
    "about:", "file:", "chrome:", "place:",
    "duckduckgo.com/?q=", "google.com/search",
]


def get_last_browser_url(domain_filter=None, max_age_minutes=30):
    db = _find_firefox_places()
    if not db:
        return None, None

    try:
        # Copy the DB — Firefox locks it while running
        tmp = "/tmp/ark_places.sqlite"
        shutil.copy2(db, tmp)
        for suffix in ("-wal", "-shm"):
            src = db + suffix
            if Path(src).exists():
                try:
                    shutil.copy2(src, tmp + suffix)
                except Exception:
                    pass

        conn = sqlite3.connect(tmp)
        cur = conn.cursor()

        # Look at last 100 visits, most recent first
        cur.execute("""
            SELECT url, title, last_visit_date
            FROM moz_places
            WHERE hidden = 0
              AND last_visit_date IS NOT NULL
              AND url NOT LIKE 'about:%'
              AND url NOT LIKE 'file:%'
              AND url NOT LIKE 'chrome:%'
              AND url NOT LIKE 'place:%'
            ORDER BY last_visit_date DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        conn.close()

        # Filter
        for url, title, visit_us in rows:
            # Skip ignored patterns
            if any(bad in url for bad in IGNORED_URL_PARTS):
                continue

            # Apply domain filter if requested
            if domain_filter and domain_filter not in url:
                continue

            # Age check (visit_us is microseconds since epoch)
            if max_age_minutes:
                age_sec = (time.time() - visit_us / 1_000_000)
                if age_sec > max_age_minutes * 60:
                    continue

            return url, title

        return None, None
    except Exception as e:
        print(f"[get] browser history error: {e}")
        return None, None


def get_active_content():
    window = get_active_window()
    if not window:
        return "none", None

    cls = window["class"]

    # Browser → last URL
    if any(b in cls for b in ["librewolf", "firefox", "chromium", "brave", "chrome"]):
        url, title = get_last_browser_url()
        if url:
            return "url", {"url": url, "title": title}
        return "none", None

    # Editor → file path from title
    if any(e in cls for e in ["nvim", "neovim", "code", "zed", "sublime"]):
        title = window["title"]
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
