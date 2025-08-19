"""Utilities for reading and writing Morpheus configuration files."""

from __future__ import annotations

import os
from typing import Dict


def ensure_env_file_exists() -> None:
    """Create a ``.env`` file from defaults and environment variables."""

    if not os.path.exists(".env") and os.path.exists(".env.example"):
        try:
            # Load defaults from .env.example
            default_env: Dict[str, str] = {}
            with open(".env.example", "r") as example_file:
                for line in example_file:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        default_env[key.strip()] = value.strip()

            # Override defaults with existing environment variables
            final_env = default_env.copy()
            for key in default_env:
                if key in os.environ:
                    final_env[key] = os.environ[key]

            # Write out .env file
            with open(".env", "w") as env_file:
                for key, value in final_env.items():
                    env_file.write(f"{key}={value}\n")
        except Exception as exc:  # pragma: no cover - log side effects
            print(f"⚠️ Error creating default .env file: {exc}")


def get_current_config() -> Dict[str, str]:
    """Read configuration from ``.env.example``, ``.env`` and environment."""

    default_config: Dict[str, str] = {}
    if os.path.exists(".env.example"):
        with open(".env.example", "r") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    default_config[key] = value

    current_config: Dict[str, str] = {}
    if os.path.exists(".env"):
        with open(".env", "r") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    current_config[key] = value

    config = {**default_config, **current_config}
    for key in list(config.keys()):
        env_value = os.environ.get(key)
        if env_value is not None:
            config[key] = env_value
    return config


def save_config(data: Dict[str, str]) -> None:
    """Persist configuration data to ``.env`` after type coercion."""

    for key, value in data.items():
        if key in {
            "ORPHEUS_MAX_TOKENS",
            "ORPHEUS_API_TIMEOUT",
            "ORPHEUS_PORT",
            "ORPHEUS_SAMPLE_RATE",
        }:
            try:
                data[key] = str(int(value))
            except (ValueError, TypeError):
                pass
        elif key in {"ORPHEUS_TEMPERATURE", "ORPHEUS_TOP_P"}:
            try:
                data[key] = str(float(value))
            except (ValueError, TypeError):
                pass

    with open(".env", "w") as fh:
        for key, value in data.items():
            fh.write(f"{key}={value}\n")

