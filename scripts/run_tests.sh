#!/usr/bin/env bash
# Fire-and-forget test runner

set -euo pipefail

ARCHIVE_ROOT=${ARCHIVE_ROOT:-archive}
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
uv pip install --system -r "${ARCHIVE_ROOT}/Orpheus-TTS/orpheus_tts_pypi/pyproject.toml"
python -m pytest -q "$@"

