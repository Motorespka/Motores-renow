# Run FastAPI from backend/ (PYTHONPATH = app package root)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "backend")
Write-Host "API: http://127.0.0.1:8000  |  health: /api/health" -ForegroundColor Cyan
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
