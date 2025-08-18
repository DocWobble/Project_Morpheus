import os
from dotenv import load_dotenv
from Morpheus_Client.config import ensure_env_file_exists

ensure_env_file_exists()
load_dotenv(override=True)


if __name__ == "__main__":
    from morpheus_tts import start_server

    host = os.getenv("ORPHEUS_HOST", "0.0.0.0")
    port = int(os.getenv("ORPHEUS_PORT", "5005"))
    start_server(host=host, port=port)
