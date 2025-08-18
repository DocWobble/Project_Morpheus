import os
from typing import Dict
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


def ensure_env_file_exists() -> None:
    """Create a .env file from defaults and OS environment variables."""
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        try:
            # Load defaults from .env.example
            default_env: Dict[str, str] = {}
            with open(".env.example", "r") as example_file:
                for line in example_file:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key = line.split("=")[0].strip()
                        default_env[key] = line.split("=", 1)[1].strip()

            # Override defaults with existing environment variables
            final_env = default_env.copy()
            for key in default_env:
                if key in os.environ:
                    final_env[key] = os.environ[key]

            # Write out .env file
            with open(".env", "w") as env_file:
                for key, value in final_env.items():
                    env_file.write(f"{key}={value}\n")
        except Exception as e:  # pragma: no cover - log side effects
            print(f"\u26a0\ufe0f Error creating default .env file: {e}")


def get_current_config() -> Dict[str, str]:
    """Read current configuration from .env.example, .env, and environment."""
    default_config: Dict[str, str] = {}
    if os.path.exists(".env.example"):
        with open(".env.example", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    default_config[key] = value

    current_config: Dict[str, str] = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    current_config[key] = value

    config = {**default_config, **current_config}
    for key in config:
        env_value = os.environ.get(key)
        if env_value is not None:
            config[key] = env_value
    return config


def save_config(data: Dict[str, str]) -> None:
    """Persist configuration data to .env file after type coercion."""
    for key, value in data.items():
        if key in ["ORPHEUS_MAX_TOKENS", "ORPHEUS_API_TIMEOUT", "ORPHEUS_PORT", "ORPHEUS_SAMPLE_RATE"]:
            try:
                data[key] = str(int(value))
            except (ValueError, TypeError):
                pass
        elif key in ["ORPHEUS_TEMPERATURE", "ORPHEUS_TOP_P"]:
            try:
                data[key] = str(float(value))
            except (ValueError, TypeError):
                pass

    with open(".env", "w") as f:
        for key, value in data.items():
            f.write(f"{key}={value}\n")


@router.get("/get_config")
async def get_config_route():
    """Return current configuration as JSON."""
    config = get_current_config()
    return JSONResponse(content=config)


@router.post("/save_config")
async def save_config_route(request: Request):
    """Save provided configuration to .env."""
    data = await request.json()
    save_config(data)
    return JSONResponse(
        content={
            "status": "ok",
            "message": "Configuration saved successfully. Restart server to apply changes.",
        }
    )
