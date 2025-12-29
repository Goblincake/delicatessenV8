CI configs and helper scripts

Everything in this `ci/` folder is designed to run locally — there are no GitHub Actions workflows in this repository.

Purpose
- Provide easy, local checks (lint, types, tests) without requiring a virtualenv.

Included
- `requirements-dev.txt` — pip packages used by the local checks (one-per-line: `ruff`, `mypy`, `pytest`)
- `run_checks.sh` — runs `ruff`, `mypy` and `pytest` without creating a `.venv`.
- `install_dev.sh` — installs dev tools using `pipx` or falls back to `python -m pip install --user` (Unix)
- `install_dev.ps1` — PowerShell equivalent for Windows (prefers `pipx` or `pip --user`)
 - `install_dev.sh` — installs dev tools using `pipx` or falls back to `python -m pip install --user` (Unix)
 - `install_dev.ps1` — PowerShell equivalent for Windows (prefers `pipx` or `pip --user`)

Reports
- The `ci/run_checks.sh` script now writes tool outputs into `ci/reports/` as text files (one per tool).
   This makes it easy to inspect results or pipe them into other tooling.

Quick start (no virtualenv)
1. Preferred — install tools via `pipx` (recommended):

   - Install `pipx` if you don't have it: `python -m pip install --user pipx` and follow pipx's post-install steps.
   - Run the helper to install tools: `bash ci/install_dev.sh` (on Windows, run `.\
i\install_dev.ps1` in PowerShell).

2. Fallback — install tools to your user Python environment:

   - `python -m pip install --user -r ci/requirements-dev.txt`

3. Run checks:

   - `./ci/run_checks.sh`

After running, check `ci/reports/` for detailed outputs from each tool.

Notes
- Scripts now prefer `pipx` for isolated, user-level installs; if `pipx` is missing the helpers use `python -m pip install --user`.
- These scripts do NOT create or activate a `.venv` anymore.
- Ensure your user-level bin directory (e.g. `~/.local/bin` on Unix) is on your `PATH` so tools installed with `--user` are discoverable.

If you want a strict virtualenv-based setup, the previous behavior used `.venv` and can be reintroduced by editing these scripts.
