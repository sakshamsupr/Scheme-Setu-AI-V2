Set-Location "$PSScriptRoot\.."
if (-not (Test-Path ".venv\Scripts\python.exe")) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
uvicorn backend.app.main:app --reload --port 8000
