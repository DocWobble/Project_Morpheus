#!/usr/bin/env python3
"""One-click environment setup."""
from __future__ import annotations
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


def miniforge_installed() -> bool:
    """Return True if a Miniforge installation is detected."""
    if shutil.which("conda") is not None:
        return True
    home = Path.home()
    return any((home / name).exists() for name in ("miniforge3", "Miniforge3"))

def detect_platform() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        os_name = "MacOSX"
    elif system == "linux":
        os_name = "Linux"
    elif system == "windows":
        os_name = "Windows"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")
    if machine in {"x86_64", "amd64"}:
        arch = "x86_64"
    elif machine in {"aarch64", "arm64"}:
        arch = "arm64" if os_name == "MacOSX" else "aarch64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")
    return os_name, arch

def install_miniforge(os_name: str, arch: str) -> None:
    ext = "exe" if os_name == "Windows" else "sh"
    target = Path.home() / ("Miniforge3" if os_name == "Windows" else "miniforge3")
    if target.exists():
        print(f"Miniforge already installed at {target}")
        return
    url = (
        "https://github.com/conda-forge/miniforge/releases/latest/download/"
        f"Miniforge3-{os_name}-{arch}.{ext}"
    )
    print(f"Downloading Miniforge from {url}")
    with tempfile.TemporaryDirectory() as tmp:
        installer = Path(tmp) / f"miniforge.{ext}"
        urllib.request.urlretrieve(url, installer)
        if os_name == "Windows":
            subprocess.check_call([str(installer), "/S", f"/D={target}"])
        else:
            installer.chmod(0o755)
            subprocess.check_call(["bash", str(installer), "-b"])
    print("Miniforge installation complete")

def pick_requirements() -> Path:
    return Path(__file__).resolve().parent.parent / "requirements.txt"

def install_requirements(req_file: Path) -> None:
    print(f"Installing dependencies from {req_file}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])

def main() -> None:
    if not miniforge_installed():
        os_name, arch = detect_platform()
        install_miniforge(os_name, arch)
    req_file = pick_requirements()
    install_requirements(req_file)

if __name__ == "__main__":
    main()
