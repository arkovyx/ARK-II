import re
import subprocess
from pathlib import Path

DEV_DIR = Path.home() / "dev"

# Common packages we might hear
PACKAGE_KEYWORDS = {
    "requests": "requests",
    "flask": "flask",
    "fastapi": "fastapi",
    "numpy": "numpy",
    "pandas": "pandas",
    "groq": "groq",
    "beautifulsoup": "beautifulsoup4",
    "beautiful soup": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "python dotenv": "python-dotenv",
    "httpx": "httpx",
    "rich": "rich",
}


def _notify(title, message, timeout_ms=3000):
    subprocess.run(
        ["notify-send", "-t", str(timeout_ms), title, message],
        check=False,
    )


def _extract_project_name(command):
    """
    Extract project name from phrases like:
      'make a folder named new project'
      'create a project called my app'
      'new project called test'
    """
    patterns = [
        r"named\s+([a-zA-Z0-9_\- ]+?)(?:\s+in|\s+and|\s+then|$)",
        r"called\s+([a-zA-Z0-9_\- ]+?)(?:\s+in|\s+and|\s+then|$)",
        r"project\s+([a-zA-Z0-9_\-]+)",
    ]
    for p in patterns:
        m = re.search(p, command.lower())
        if m:
            name = m.group(1).strip()
            # Clean it
            name = re.sub(r"\s+", "-", name)
            name = re.sub(r"[^a-zA-Z0-9_\-]", "", name)
            if name and name not in ("in", "and", "then"):
                return name
    return None


def _extract_packages(command):
    """
    Find packages mentioned in the command.
    Returns list of pip package names.
    """
    lower = command.lower()
    packages = []
    for keyword, pip_name in PACKAGE_KEYWORDS.items():
        if keyword in lower:
            packages.append(pip_name)
    return packages


def scaffold_project(command):
    """
    Build a new Python project:
      1. Create folder in ~/dev/<name>/
      2. Create venv inside
      3. pip install detected packages
      4. Create main.py with imports at top
    """
    name = _extract_project_name(command)
    if not name:
        return "❌ Couldn't figure out the project name. Try: 'make a folder named myproject in my dev directory'"

    project_dir = DEV_DIR / name
    if project_dir.exists():
        return f"❌ Folder already exists: {project_dir}"

    packages = _extract_packages(command)

    try:
        # 1. Create folder
        project_dir.mkdir(parents=True, exist_ok=False)

        # 2. Create venv
        subprocess.run(
            ["python", "-m", "venv", "venv"],
            cwd=str(project_dir),
            check=True,
            capture_output=True,
            timeout=120,
        )

        # 3. Install packages (if any)
        installed = []
        if packages:
            pip_path = project_dir / "venv" / "bin" / "pip"
            result = subprocess.run(
                [str(pip_path), "install"] + packages,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                installed = packages

        # 4. Create main.py with imports
        import_lines = []
        for pkg in installed:
            # Normalize import name
            mod = pkg.replace("-", "_")
            if pkg == "beautifulsoup4":
                mod = "bs4"
            elif pkg == "python-dotenv":
                mod = "dotenv"
            import_lines.append(f"import {mod}")

        main_content = ""
        if import_lines:
            main_content += "\n".join(import_lines) + "\n\n\n"
        main_content += (
            "def main():\n"
            '    print("Hello from ' + name + '!")\n'
            "\n\n"
            'if __name__ == "__main__":\n'
            "    main()\n"
        )

        (project_dir / "main.py").write_text(main_content)

        # Notify
        _notify("🚀 ARK-II", f"Project created: {name}")

        summary = [
            f"✅ Created: {project_dir}",
            f"📦 Venv: {project_dir / 'venv'}",
        ]
        if installed:
            summary.append(f"📥 Installed: {', '.join(installed)}")
        else:
            summary.append("📥 No packages detected")
        summary.append(f"📄 main.py created with imports")

        return "\n".join(summary)

    except subprocess.CalledProcessError as e:
        return f"❌ Setup failed: {e.stderr[:200] if e.stderr else e}"
    except subprocess.TimeoutExpired:
        return "❌ Timed out (network slow or big package?)"
    except Exception as e:
        return f"❌ Error: {e}"
