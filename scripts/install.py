import platform
import subprocess
import sys
from pathlib import Path

try:
    import torch
except ImportError:  # torch may not be installed yet
    torch = None

REQ_DIR = Path(__file__).resolve().parent.parent / "requirements" / "full"

def select_requirements_file() -> Path:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        if "arm" in machine:
            return REQ_DIR / "requirements_apple_silicon.txt"
        return REQ_DIR / "requirements_apple_intel.txt"

    if torch is not None and torch.cuda.is_available():
        if getattr(torch.version, "hip", None):
            return REQ_DIR / "requirements_rocm.txt"
        return REQ_DIR / "requirements_cuda.txt"

    return REQ_DIR / "requirements_cpu.txt"

def main() -> None:
    req_file = select_requirements_file()
    print(f"Installing dependencies from {req_file}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])

if __name__ == "__main__":
    main()
