#!/usr/bin/env bash
set -euo pipefail

echo "Creating virtual environment in .venv (if missing)..."
if [ ! -d ".venv" ]; then
  python -m venv .venv
  echo "Created .venv"
else
  echo ".venv already exists"
fi

echo "Activating .venv..."
# shellcheck source=/dev/null
source .venv/bin/activate

echo "Upgrading pip and installing dev requirements..."
python -m pip install --upgrade pip
pip install -r ci/requirements-dev.txt

echo "Installation complete. To run checks: ./ci/run_checks.sh"
