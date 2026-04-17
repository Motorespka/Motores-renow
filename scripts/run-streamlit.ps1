# Main site entry (Streamlit Cloud uses this repo root + App.py)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "Streamlit: http://localhost:8501" -ForegroundColor Cyan
streamlit run App.py
