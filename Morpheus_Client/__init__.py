"""Unified Morpheus client package with API, TTS engine and utilities."""
from __future__ import annotations

from importlib import import_module
import sys
from typing import Any

__all__ = ["start_server", "Client", "app", "orchestrator", "tts_engine", "inference"]


def start_server(host: str = "0.0.0.0", port: int = 5005) -> None:
    """Launch the unified API and admin server via uvicorn."""
    from .server import start_server as _start

    _start(host=host, port=port)


def __getattr__(name: str) -> Any:  # pragma: no cover - simple loader
    if name == "Client":
        from .client import Client

        return Client
    if name == "app":
        from .server import app

        return app
    if name in {"orchestrator", "tts_engine"}:
        module = import_module(f".{name}", __name__)
        setattr(sys.modules[__name__], name, module)
        return module
    if name == "inference":
        module = import_module(".tts_engine.inference", __name__)
        setattr(sys.modules[__name__], name, module)
        return module
    raise AttributeError(f"module {__name__} has no attribute {name}")
