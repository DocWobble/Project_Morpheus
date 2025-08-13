#!/usr/bin/env bash
# Fire-and-forget test runner

set -euo pipefail
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
python -m pytest -q "$@"

