import os
from dotenv import load_dotenv


def ensure_env_file_exists() -> None:
    """Create a .env from .env.example if needed, merging environment variables."""
    if os.path.exists(".env") or not os.path.exists(".env.example"):
        return
    default_env = {}
    with open(".env.example", "r") as example_file:
        for line in example_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                default_env[key] = value
    final_env = {**default_env}
    for key in default_env:
        if key in os.environ:
            final_env[key] = os.environ[key]
    with open(".env", "w") as env_file:
        for key, value in final_env.items():
            env_file.write(f"{key}={value}\n")


ensure_env_file_exists()
load_dotenv(override=True)


if __name__ == "__main__":
    from morpheus_tts import start_server

    host = os.getenv("ORPHEUS_HOST", "0.0.0.0")
    port = int(os.getenv("ORPHEUS_PORT", "5005"))
    start_server(host=host, port=port)
