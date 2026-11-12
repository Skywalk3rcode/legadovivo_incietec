$ErrorActionPreference = "Stop"
$EngineDir = $PSScriptRoot
$Python = Join-Path $EngineDir ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "No existe el entorno de voz. Sigue las instrucciones de voice-engine/README.md para instalarlo con Python 3.11."
}

Set-Location $EngineDir
& $Python -m uvicorn app:app --host 127.0.0.1 --port 5003
