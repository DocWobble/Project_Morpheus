#!/usr/bin/env bash
set -euo pipefail
python scripts/one_click.py
python -m uvicorn Orpheus-FastAPI.app:app
