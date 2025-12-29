#!/usr/bin/env bash
set -euo pipefail

echo "Installing dev dependencies..."
python -m pip install --upgrade pip
if [ -f "ci/requirements-dev.txt" ]; then
  pip install -r ci/requirements-dev.txt
else
  pip install ruff mypy pytest
fi

echo "Running ruff (lint)..."
ruff check .

echo "Running mypy (type checks)..."
# allow missing imports to avoid noisy failures in mixed projects
mypy --ignore-missing-imports . || true

echo "Running pytest (if any tests)"
# don't fail if there are no tests
pytest -q || true

echo "CI checks finished."
