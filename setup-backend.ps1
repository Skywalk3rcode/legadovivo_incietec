# LegadoVivo - Setup y Arranque del Backend (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Yellow
Write-Host "         LegadoVivo - Servidor Backend FastAPI          " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Yellow
Write-Host ""

$BackendDir = Join-Path $PSScriptRoot "backend"
$RootDir = $PSScriptRoot

Write-Host "[1/4] Verificando instalacion de Python..." -ForegroundColor Cyan

$PythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonExe = "py"
}

if (-not $PythonExe) {
    Write-Host "[ERROR] No se encontro Python en tu sistema." -ForegroundColor Red
    Write-Host "Por favor instala Python 3.11, 3.12 o 3.13 desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Recuerda marcar la casilla: 'Add python.exe to PATH'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python detectado ($PythonExe)." -ForegroundColor Green
Write-Host ""

# Detectar venv existente en raiz o en backend
$VenvPython = $null
$VenvDir = $null
if (Test-Path (Join-Path $RootDir "venv\Scripts\python.exe")) {
    $VenvDir = Join-Path $RootDir "venv"
    $VenvPython = Join-Path $RootDir "venv\Scripts\python.exe"
}
elseif (Test-Path (Join-Path $BackendDir "venv\Scripts\python.exe")) {
    $VenvDir = Join-Path $BackendDir "venv"
    $VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
}

if (-not $VenvPython) {
    Write-Host "[2/4] Creando entorno virtual venv en $RootDir\venv..." -ForegroundColor Cyan
    Set-Location $RootDir
    & $PythonExe -m venv venv
    $VenvDir = Join-Path $RootDir "venv"
    $VenvPython = Join-Path $RootDir "venv\Scripts\python.exe"
    Write-Host "Entorno virtual creado." -ForegroundColor Green
}
else {
    Write-Host "Entorno virtual existente encontrado en $VenvDir." -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/4] Instalando / actualizando dependencias de requirements.txt..." -ForegroundColor Cyan
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
Write-Host "Dependencias verificadas e instaladas." -ForegroundColor Green

Write-Host ""
Write-Host "[4/4] Verificando bases de datos..." -ForegroundColor Cyan
Set-Location $BackendDir
& $VenvPython "app\scripts\init_databases.py"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "       Iniciando FastAPI en http://localhost:8080       " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Presiona Ctrl + C para detener el servidor." -ForegroundColor Gray
Write-Host ""

& $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
