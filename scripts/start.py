import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import threading
import webbrowser

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    raise SystemExit(
        "Install `python-dotenv` via `pip install python-dotenv` to load configuration."
    )

from Morpheus_Client.config import ensure_env_file_exists
from Morpheus_Client import start_server


def main() -> None:
    """Entry point to launch the Morpheus server and open admin UI.

    Configuration precedence:
    1. existing environment variables
    2. ``~/.morpheus/config``
    3. ``.env`` (generated from ``.env.example``)
    """
    try:
        import orpheus_cpp  # noqa: F401
    except ImportError:  # pragma: no cover - depends on optional dep
        raise SystemExit(
            "Install `orpheus_cpp` via `pip install orpheus-cpp` for local synthesis."
        )
    ensure_env_file_exists()
    # Load config files: OS env > ~/.morpheus/config > .env
    user_config = os.path.expanduser("~/.morpheus/config")
    if os.path.exists(user_config):
        load_dotenv(user_config)
    load_dotenv()
    host = os.getenv("ORPHEUS_HOST", "0.0.0.0")
    port = int(os.getenv("ORPHEUS_PORT", "5005"))
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}/admin")).start()
    start_server(host=host, port=port)

if __name__ == "__main__":
    main()
