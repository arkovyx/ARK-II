import subprocess
import yt_dlp
from pathlib import Path
import threading

YT_DIR = Path.home() / ".ark" / "yt"
YT_DIR.mkdir(parents=True, exist_ok=True)


def _notify(title, message):
    subprocess.run(["notify-send", title, message], check=False)


def _do_download(url):
    try:
        ydl_opts = {
            "outtmpl": str(YT_DIR / "%(title)s.%(ext)s"),
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "quiet": True,
            "noprogress": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
        _notify("✅ ARK", f"Downloaded: {title[:50]}")
    except Exception as e:
        _notify("❌ ARK", f"Download failed: {str(e)[:60]}")


def download_video(url):
    """Start download in background, return immediately."""
    if not url:
        return "No URL provided"
    _notify("📥 ARK", "Download started...")
    t = threading.Thread(target=_do_download, args=(url,), daemon=True)
    t.start()
    return "📥 Downloading in background"
