#!/usr/bin/env bash
set -euo pipefail

# Notes API Backend startup helper.
# Ensures Python dependencies are installed in environments where the container
# image/venv hasn't preinstalled requirements yet, then runs uvicorn.
#
# Usage:
#   ./start.sh
#
# Notes:
# - Non-interactive and safe to run multiple times.
# - Installs to user site-packages when global site-packages are not writable.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

python -m pip install --user -r requirements.txt

exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 3001
