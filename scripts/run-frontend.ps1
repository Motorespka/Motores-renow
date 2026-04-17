# Next.js dev server (needs Node.js + npm on PATH — install from https://nodejs.org)
$ErrorActionPreference = "Stop"
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Host "npm nao encontrado no PATH. Instale Node.js LTS e abra um novo terminal." -ForegroundColor Yellow
    exit 1
}
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "frontend")
if (-not (Test-Path "node_modules")) { npm install }
Write-Host "Next: http://localhost:3000" -ForegroundColor Cyan
npm run dev
