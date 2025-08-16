#!/usr/bin/env bash
# Fire-and-forget test runner

set -euo pipefail
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
uv pip install --system -r Orpheus-TTS/orpheus_tts_pypi/pyproject.toml
python -m pytest -q "$@"

