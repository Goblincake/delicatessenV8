<#
Install development virtual environment and required tooling on Windows PowerShell.
Run from repository root in an elevated PowerShell (if required):
    .\ci\install_dev.ps1
#>
Set-StrictMode -Version Latest
if (-Not (Test-Path -Path .venv)) {
    Write-Host "Creating virtual environment in .venv..."
    python -m venv .venv
} else {
    Write-Host ".venv already exists"
}

Write-Host "Activating .venv..."
& .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing dev requirements..."
python -m pip install --upgrade pip
pip install -r ci/requirements-dev.txt

Write-Host "Installation complete. To run checks: .\ci\run_checks.sh (use bash) or run the individual tools inside the .venv." 
