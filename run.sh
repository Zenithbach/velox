#!/bin/bash
# 🦋 Velox development launcher
# Activates the venv and runs the app. Use this instead of
# remembering to source .venv/bin/activate every time.
#
# Usage: ./run.sh

source "$(dirname "$0")/.venv/bin/activate"
python "$(dirname "$0")/main.py" "$@"
