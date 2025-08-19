import subprocess
import sys
from pathlib import Path

REQ_FILE = Path(__file__).resolve().parent.parent / "requirements.txt"

def main() -> None:
    print(f"Installing dependencies from {REQ_FILE}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQ_FILE)])

if __name__ == "__main__":
    main()
