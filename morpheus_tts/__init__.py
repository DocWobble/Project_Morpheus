"""Unified package for Morpheus TTS server and client utilities."""
from __future__ import annotations

from typing import Any

__all__ = ["start_server", "Client", "app"]


def start_server(host: str = "0.0.0.0", port: int = 5005) -> None:
    """Launch the bundled FastAPI server via uvicorn."""
    from .server import start_server as _start

    _start(host=host, port=port)


def __getattr__(name: str) -> Any:  # pragma: no cover - simple loader
    if name == "Client":
        from .client import Client

        return Client
    if name == "app":
        from .server import app

        return app
    raise AttributeError(f"module {__name__} has no attribute {name}")
