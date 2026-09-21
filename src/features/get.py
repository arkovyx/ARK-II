import subprocess
import json


def get_active_window():
    try:
        result = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        # hyprctl returns empty {} if no window is focused
        if not data or "class" not in data:
            return None

        pid = data.get("pid", 0)

        # Get the working directory of the process
        # /proc/<pid>/cwd is a symlink to the process's current dir
        cwd = None
        if pid:
            try:
                cwd = str(subprocess.check_output(
                    ["readlink", f"/proc/{pid}/cwd"],
                    text=True
                ).strip())
            except Exception:
                cwd = None

        return {
            "class": data.get("class", "").lower(),
            "title": data.get("title", ""),
            "pid": pid,
            "cwd": cwd,
        }

    except Exception:
        return None
