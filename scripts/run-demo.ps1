# Demo local: indice + Streamlit
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host ">> Indexando acervo OFICIAL..." -ForegroundColor Cyan
python scripts/index_for_search.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ">> Abrindo demo Streamlit..." -ForegroundColor Cyan
streamlit run app/demo.py
