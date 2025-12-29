#!/usr/bin/env bash
set -euo pipefail

echo "Running extended checks (resilient mode)."
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

REPORT_DIR="$ROOT_DIR/ci/reports"
mkdir -p "$REPORT_DIR"

# Directories to exclude from checks (centralized)
EXCLUDE_DIRS=(tests ci)
# build a regex like '^(tests|ci)/' for tools that accept regex excludes
EXCLUDE_PATTERN="^($(IFS='|'; echo "${EXCLUDE_DIRS[*]}"))/"
# comma-separated for bandit -x
EXCLUDE_CSV="$(IFS=,; echo "${EXCLUDE_DIRS[*]}")"
# build isort skip args
ISORT_SKIP_ARGS=()
for d in "${EXCLUDE_DIRS[@]}"; do
  ISORT_SKIP_ARGS+=("--skip" "$d")
done

# Detect a usable python binary
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
elif command -v py >/dev/null 2>&1; then
  PY=py
fi

# Prepend common user-level script locations to PATH (helps Bash/WSL find Windows installs)
if [ -n "${APPDATA:-}" ]; then
  for p in "$APPDATA/Python/Python310/Scripts" "$APPDATA/Python/Scripts" "$HOME/AppData/Roaming/Python/Python310/Scripts"; do
    if [ -d "$p" ]; then
      PATH="$p:$PATH"
    fi
  done
fi
if [ -d "$HOME/.local/bin" ]; then
  PATH="$HOME/.local/bin:$PATH"
fi
export PATH

run_or_warn() {
  # $1 = report path, $2 = primary command name, rest = args
  local report="$1"; shift
  local cmd="$1"; shift
  if command -v "$cmd" >/dev/null 2>&1; then
    "$cmd" "$@" >"$report" 2>&1 || true
  elif [ -n "$PY" ]; then
    $PY -m "$cmd" "$@" >"$report" 2>&1 || true
  else
    echo "$cmd not found and no python available" >"$report"
  fi
}

echo "Running ruff..."
run_or_warn "$REPORT_DIR/ruff.txt" ruff check . --extend-exclude "$EXCLUDE_PATTERN"

echo "Running black (check)..."
run_or_warn "$REPORT_DIR/black.txt" black --check . --exclude "$EXCLUDE_PATTERN"

echo "Running isort (check)..."
run_or_warn "$REPORT_DIR/isort.txt" isort --check-only . "${ISORT_SKIP_ARGS[@]}"

echo "Running mypy..."
run_or_warn "$REPORT_DIR/mypy.txt" mypy --ignore-missing-imports --exclude "$EXCLUDE_PATTERN" .

echo "Running pip-audit..."
if [ -n "$PY" ]; then
  $PY -m pip_audit >"$REPORT_DIR/pip-audit.txt" 2>&1 || true
else
  echo "pip-audit not run (no python)" >"$REPORT_DIR/pip-audit.txt"
fi

echo "Running bandit (excluding ${EXCLUDE_CSV})..."
if command -v bandit >/dev/null 2>&1; then
  bandit -r . -f txt -n 5 -x "$EXCLUDE_CSV" >"$REPORT_DIR/bandit.txt" 2>&1 || true
elif [ -n "$PY" ]; then
  $PY -m bandit -r . -f txt -n 5 -x "$EXCLUDE_CSV" >"$REPORT_DIR/bandit.txt" 2>&1 || true
else
  echo "bandit not run (no bandit/python)" >"$REPORT_DIR/bandit.txt"
fi

echo "Running vulture..."
run_or_warn "$REPORT_DIR/vulture.txt" vulture . --min-confidence 50 --exclude "$EXCLUDE_PATTERN"

echo "Running safety..."
if [ -n "$PY" ]; then
  $PY -m safety check >"$REPORT_DIR/safety.txt" 2>&1 || true
else
  echo "safety not run (no python)" >"$REPORT_DIR/safety.txt"
fi

echo "Running pytest with coverage..."
if [ -n "$PY" ]; then
  $PY -m pytest -q --cov=. --cov-report=term-missing >"$REPORT_DIR/pytest.txt" 2>&1 || true
else
  echo "pytest not run (no python)" >"$REPORT_DIR/pytest.txt"
fi

echo "Reports written to $REPORT_DIR"
echo "Summary (first lines of each report):"
for f in "$REPORT_DIR"/*.txt; do
  echo "--- $f ---"
  head -n 6 "$f" || true
done

echo "Extended checks finished."

