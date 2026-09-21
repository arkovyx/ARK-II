# src/features/git.py
import subprocess

def clone_repo(url, output_dir="~/.ark/git"):
    subprocess.run(["git", "clone", url, output_dir])
