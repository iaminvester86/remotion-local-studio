# Double-click friendly launcher (Windows PowerShell). Runs setup if needed, then opens the UI.
Set-Location -Path $PSScriptRoot
if (-not (Test-Path ".venv")) {
  Write-Host "First run: installing. This can take a few minutes..."
  .\install.ps1
}
& .\.venv\Scripts\Activate.ps1
rls ui
