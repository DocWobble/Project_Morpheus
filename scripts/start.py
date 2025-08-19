import os
import threading
import webbrowser
from dotenv import load_dotenv
from Morpheus_Client.config import ensure_env_file_exists
from Morpheus_Client import start_server

def main() -> None:
    """Entry point to launch the Morpheus server and open admin UI."""
    ensure_env_file_exists()
    # Load default .env if present
    load_dotenv(override=True)
    # Load persistent user config from ~/.morpheus/config
    user_config = os.path.expanduser("~/.morpheus/config")
    if os.path.exists(user_config):
        load_dotenv(user_config, override=True)
    host = os.getenv("ORPHEUS_HOST", "0.0.0.0")
    port = int(os.getenv("ORPHEUS_PORT", "5005"))
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}/admin")).start()
    start_server(host=host, port=port)

if __name__ == "__main__":
    main()
