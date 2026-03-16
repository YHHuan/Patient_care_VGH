"""Build standalone .exe with PyInstaller — run on a Windows machine with Python installed.

Usage:
    python build.py          # installs deps + builds .exe
    python build.py --skip   # skip pip install, just build
"""

import subprocess
import sys


def install_deps():
    print("Installing dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        check=True,
    )
    print()


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "VGH_AI_Summary",
        "--add-data", ".env.example;.",
        "--hidden-import", "pydantic",
        "--hidden-import", "pydantic_settings",
        "--hidden-import", "httpx",
        "--hidden-import", "bs4",
        "--hidden-import", "lxml",
        "--hidden-import", "pandas",
        "--hidden-import", "docx",
        "--hidden-import", "rich",
        "--hidden-import", "typer",
        "--collect-submodules", "pydantic",
        "--collect-submodules", "pydantic_settings",
        "gui.py",
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("\nDone! Executable is at: dist/VGH_AI_Summary.exe")


if __name__ == "__main__":
    if "--skip" not in sys.argv:
        install_deps()
    build()
