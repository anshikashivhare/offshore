$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location -Path "$root\backend"
$env:PYTHONPATH = "$root;$root\backend"
& "$root\.venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000
