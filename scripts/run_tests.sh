#!/usr/bin/env bash
# Fire-and-forget test runner
set -e
export PYTHONPATH="$(pwd):$PYTHONPATH"
pytest -q
