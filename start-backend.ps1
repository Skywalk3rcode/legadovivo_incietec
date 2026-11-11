# LegadoVivo - Servidor Backend con PostgreSQL & MongoDB en tu PC (Sin Docker)
$ErrorActionPreference = "Continue"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  LegadoVivo - Servidor Backend FastAPI                " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$BackendDir = Join-Path $PSScriptRoot "backend"
$RootDir = $PSScriptRoot

# 1. Detectar entorno virtual
$VenvPython = $null
if (Test-Path (Join-Path $RootDir "venv\Scripts\python.exe")) {
    $VenvPython = Join-Path $RootDir "venv\Scripts\python.exe"
}
elseif (Test-Path (Join-Path $BackendDir "venv\Scripts\python.exe")) {
    $VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
}

if (-not $VenvPython) {
    Write-Host "[AVISO] No se encontro entorno virtual. Ejecutando setup-backend.ps1..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "setup-backend.ps1")
    exit $LASTEXITCODE
}

Write-Host "Entorno virtual detectado: $VenvPython" -ForegroundColor Green
Set-Location $BackendDir

# 2. Inicializar bases de datos en PostgreSQL
Write-Host ""
Write-Host "[1/2] Verificando base de datos 'legadovivo_db' en PostgreSQL..." -ForegroundColor Cyan
& $VenvPython "app\scripts\init_databases.py"

# 3. Arrancar servidor FastAPI
Write-Host ""
Write-Host "[2/2] Iniciando FastAPI en http://localhost:8080..." -ForegroundColor Cyan
Write-Host "  - PostgreSQL: localhost:5432 (Base: legadovivo_db)" -ForegroundColor Green
Write-Host "  - ChromaDB:   ./chroma_storage (Persistencia en disco)" -ForegroundColor Green
Write-Host "  - Ollama:     http://localhost:11434" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona Ctrl + C para detener el servidor." -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

& $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
