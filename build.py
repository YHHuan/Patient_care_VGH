"""Build standalone .exe with PyInstaller — run on a Windows machine with Python installed."""

import subprocess
import sys


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "VGH_AI_Summary",
        "--add-data", ".env.example;.",
        "--hidden-import", "tiktoken_ext.openai_public",
        "--hidden-import", "tiktoken_ext",
        "gui.py",
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("\nDone! Executable is at: dist/VGH_AI_Summary.exe")


if __name__ == "__main__":
    build()
