# LegadoVivo - Setup y Arranque del Backend (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Yellow
Write-Host "         LegadoVivo - Servidor Backend FastAPI          " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Yellow
Write-Host ""

$BackendDir = Join-Path $PSScriptRoot "backend"
Set-Location $BackendDir

Write-Host "[1/3] Verificando instalacion de Python..." -ForegroundColor Cyan

$PythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonExe = "py"
}

if (-not $PythonExe) {
    Write-Host "[ERROR] No se encontro Python en tu sistema." -ForegroundColor Red
    Write-Host "Por favor instala Python 3.11 o 3.12 desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Recuerda marcar la casilla: 'Add python.exe to PATH'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python detectado ($PythonExe)." -ForegroundColor Green
Write-Host ""

$VenvDir = Join-Path $BackendDir "venv"
$VenvActivate = Join-Path $VenvDir "Scripts\Activate.ps1"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[2/3] Creando entorno virtual venv..." -ForegroundColor Cyan
    & $PythonExe -m venv venv
    Write-Host "Entorno virtual creado." -ForegroundColor Green
    Write-Host ""

    Write-Host "[3/3] Instalando dependencias de requirements.txt..." -ForegroundColor Cyan
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r requirements.txt
    Write-Host "Dependencias instaladas exitosamente." -ForegroundColor Green
}
else {
    Write-Host "Entorno virtual existente encontrado." -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "       Iniciando FastAPI en http://localhost:8080       " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Presiona Ctrl + C para detener el servidor." -ForegroundColor Gray
Write-Host ""

& $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

