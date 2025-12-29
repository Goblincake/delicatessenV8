<#
Install development virtual environment and required tooling on Windows PowerShell.
Run from repository root in an elevated PowerShell (if required):
    .\ci\install_dev.ps1
#>
Set-StrictMode -Version Latest
Write-Host "Installing dev tools without creating a virtualenv (prefers pipx then pip --user)."
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    Write-Host "Using pipx to install dev tools from ci/requirements-dev.txt"
    Get-Content -Path ci/requirements-dev.txt | ForEach-Object {
        $pkg = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($pkg)) { return }
        if (Get-Command $pkg -ErrorAction SilentlyContinue) {
            Write-Host "$pkg already available"
        } else {
            Write-Host "pipx installing $pkg"
            pipx install $pkg
        }
    }
} else {
    Write-Host "pipx not found. Installing user-level packages via pip."
    python -m pip install --user -r ci/requirements-dev.txt
    Write-Host "Ensure your user-level bin path is on PATH (e.g. %USERPROFILE%\\.local\\bin or where pip installs user scripts)."
}

Write-Host "Installation complete. Run .\ci\run_checks.sh (in Git Bash) or run tools directly from PATH." 
