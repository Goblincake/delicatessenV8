CI configs and helper scripts

Files in this folder are used by the GitHub Actions workflow at `.github/workflows/ci.yml`.
If you want to disable or remove CI, delete both `.github/workflows/ci.yml` and this `ci/` folder.

Included:
- `requirements-dev.txt` — pip packages used by CI
- `run_checks.sh` — script that runs ruff, mypy and pytest
