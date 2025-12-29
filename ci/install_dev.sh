#!/usr/bin/env bash
set -euo pipefail

echo "Installing dev tools without creating a virtualenv (prefers pipx then pip --user)."
if command -v pipx >/dev/null 2>&1; then
  echo "Using pipx to install dev tools listed in ci/requirements-dev.txt"
  while IFS= read -r pkg || [ -n "$pkg" ]; do
    pkg_trimmed="$(echo "$pkg" | tr -d '\r')"
    [ -z "$pkg_trimmed" ] && continue
    if command -v "$pkg_trimmed" >/dev/null 2>&1; then
      echo "$pkg_trimmed already installed"
    else
      echo "pipx installing $pkg_trimmed"
      pipx install "$pkg_trimmed" || true
    fi
  done < ci/requirements-dev.txt
else
  echo "pipx not found. Falling back to 'python -m pip install --user -r ci/requirements-dev.txt'"
  python -m pip install --user -r ci/requirements-dev.txt
  echo "Make sure your user-level bin directory (e.g. ~/.local/bin) is on PATH so tools are discoverable." 
fi

echo "Installation complete. Run ./ci/run_checks.sh to run checks."
