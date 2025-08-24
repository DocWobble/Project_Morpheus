#!/usr/bin/env python3
"""One-click environment setup."""
from __future__ import annotations
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


def detect_gpu() -> str | None:
    """Return 'cuda', 'rocm', or None based on available tools."""
    if shutil.which("nvidia-smi"):
        return "cuda"
    if shutil.which("rocm-smi"):
        return "rocm"
    return None


def install_torch(python: Path, gpu: str | None) -> None:
    cmd = [str(python), "-m", "pip", "install", "torch"]
    if gpu == "cuda":
        cmd += ["--extra-index-url", "https://download.pytorch.org/whl/cu124"]
    elif gpu == "rocm":
        cmd += ["--extra-index-url", "https://download.pytorch.org/whl/rocm6.2"]
    subprocess.check_call(cmd)
    if gpu is not None:
        subprocess.check_call(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "bitsandbytes",
                "flash-attn",
            ]
        )


def install_llama_cpp(python: Path, gpu: str | None) -> None:
    cmd = [str(python), "-m", "pip", "install", "llama-cpp-python"]
    if gpu == "cuda":
        cmd += [
            "--extra-index-url",
            "https://abetlen.github.io/llama-cpp-python/whl/cu124",
        ]
    elif gpu == "rocm":
        cmd += [
            "--extra-index-url",
            "https://abetlen.github.io/llama-cpp-python/whl/rocm6.2",
        ]
    subprocess.check_call(cmd)

def ensure_venv() -> Path:
    venv_dir = Path(".venv")
    if not venv_dir.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    if platform.system().lower() == "windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"

def install_requirements(python: Path, req_file: Path) -> None:
    print(f"Installing dependencies from {req_file}")
    pkgs: list[str] = []
    with req_file.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("torch"):
                continue
            pkgs.append(line)
    if pkgs:
        subprocess.check_call([str(python), "-m", "pip", "install", *pkgs])
    gpu = detect_gpu()
    install_torch(python, gpu)
    install_llama_cpp(python, gpu)


def main() -> None:
    if not miniforge_installed():
        os_name, arch = detect_platform()
        install_miniforge(os_name, arch)
    req_file = pick_requirements()
    python = ensure_venv()
    install_requirements(python, req_file)
    print("Setup complete. Run 'source .venv/bin/activate' before launching the server.")

if __name__ == "__main__":
    main()
