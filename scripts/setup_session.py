#!/usr/bin/env python3
"""Preload core libraries for Codex-driven agent sessions.

Running this script once at the start of a session imports the common
dependencies used throughout Project Morpheus. Preloading reduces
per-request latency by allowing Codex to operate with a warm module
cache.
"""

from __future__ import annotations

import importlib
from typing import Iterable

LIBRARIES: Iterable[str] = [
    "dotenv",
    "httpx",
    "numpy",
    "psutil",
    "pytest",
    "websockets",
]


def preload() -> None:
    """Import all libraries defined in :data:`LIBRARIES`."""
    for name in LIBRARIES:
        importlib.import_module(name)
    from dotenv import load_dotenv
    load_dotenv(override=True)


if __name__ == "__main__":
    preload()
