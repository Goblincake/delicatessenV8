CI configs and helper scripts
Everything in this `ci/` folder is designed to run locally (or on your own CI runners) — there are no GitHub Actions workflows in this repository.
Included:
- `requirements-dev.txt` — pip packages used by the local checks
- `run_checks.sh` — script that runs `ruff`, `mypy` and `pytest` (will activate `.venv` if present)
- `install_dev.sh` — convenience script to create a local `.venv` and install dev tools (Unix)
- `install_dev.ps1` — PowerShell equivalent for Windows
Local setup
1. Unix / WSL / macOS:
	- `bash ci/install_dev.sh` (creates `.venv` and installs `ci/requirements-dev.txt`).
	- `./ci/run_checks.sh` (will activate `.venv` automatically and run the checks).
2. Windows PowerShell:
	- `.
	ci\install_dev.ps1` (creates `.venv`, installs dev deps).
	- Activate the venv: `.
	.venv\Scripts\Activate.ps1` and run the tools, or use Git Bash to run `./ci/run_checks.sh`.
Notes
- The `run_checks.sh` script activates `.venv` if present; otherwise it will install the tools into the active Python environment.
- To remove local tooling, delete the `.venv` directory.
CI configs and helper scripts

Files in this folder are used by the GitHub Actions workflow at `.github/workflows/ci.yml`.
If you want to disable or remove CI, delete both `.github/workflows/ci.yml` and this `ci/` folder.

Included:
- `requirements-dev.txt` — pip packages used by CI
- `run_checks.sh` — script that runs ruff, mypy and pytest
- `install_dev.sh` — convenience script to create a local `.venv` and install dev tools (Unix)
- `install_dev.ps1` — PowerShell equivalent for Windows

Local setup
1. Unix / WSL / macOS:
	- `bash ci/install_dev.sh` (creates `.venv`, installs dev deps)
	- `./ci/run_checks.sh` (will activate `.venv` automatically)

2. Windows PowerShell:
	- `.
	ci\install_dev.ps1` (creates `.venv`, installs dev deps)
	- Run the checks from PowerShell by activating the venv: `.
	  .venv\Scripts\Activate.ps1` and then run the individual tools, or use Git Bash to run `./ci/run_checks.sh`.

Notes
- The `run_checks.sh` script will activate `.venv` if present; otherwise it installs tools into the active environment.
- Delete the `.venv` directory to remove local tooling; delete `.github/workflows/ci.yml` and the `ci/` folder to remove CI.
