#!/usr/bin/env python3
"""Validate that requirements.txt installs in a clean environment."""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    req_file = repo_root / "requirements.txt"
    with tempfile.TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        if os.name == "nt":
            python = venv_dir / "Scripts" / "python.exe"
        else:
            python = venv_dir / "bin" / "python"
        try:
            subprocess.check_call([str(python), "-m", "pip", "install", "--upgrade", "pip"])
            subprocess.check_call([str(python), "-m", "pip", "install", "-r", str(req_file)])
        except subprocess.CalledProcessError:
            print("Dependency installation failed", file=sys.stderr)
            return 1
    print("Dependency installation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
