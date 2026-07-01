# install.ps1 — one-shot local setup for Windows (PowerShell).
# Creates a project venv, installs the CLI + CPU-friendly core tools, checks binaries.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "==> remotion-local-studio installer"

function Have($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

$miss = $false
if (-not (Have "python")) { Write-Host "  MISSING python  -> install Python 3.10+ from https://python.org"; $miss = $true }
if (-not (Have "ffmpeg")) { Write-Host "  MISSING ffmpeg  -> winget install Gyan.FFmpeg"; $miss = $true }
if (-not (Have "node"))   { Write-Host "  NOTE: Node.js not found. Needed only for Remotion (https://nodejs.org)." }
if ($miss) { Write-Host "Install the missing required tools above, then re-run .\install.ps1"; exit 1 }

if (-not (Test-Path ".venv")) {
  Write-Host "==> Creating virtualenv at .venv"
  python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel | Out-Null
Write-Host "==> Installing the rls CLI (editable) + CPU-friendly core tools"
pip install -e .
pip install -r requirements.txt

Write-Host ""
Write-Host "==> Done. Activate with:  .\.venv\Scripts\Activate.ps1"
Write-Host "    Then run:             rls doctor"
Write-Host ""
Write-Host "Heavy GPU tools install on demand:  rls install image | music | video"
