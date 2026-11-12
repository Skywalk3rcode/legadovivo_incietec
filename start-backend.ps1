# LegadoVivo - Servidor Backend con PostgreSQL & MongoDB en tu PC (Sin Docker)
$ErrorActionPreference = "Continue"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  LegadoVivo - PostgreSQL & MongoDB Nativos en tu PC    " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$BackendDir = Join-Path $PSScriptRoot "backend"
Set-Location $BackendDir

# 1. Instalar dependencias si faltan
Write-Host "[1/3] Verificando dependencias en Python (psycopg2, motor, etc.)..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

# 2. Inicializar bases de datos en PostgreSQL y MongoDB
Write-Host ""
Write-Host "[2/3] Verificando bases de datos 'legadovivo_db' y 'legadovivo_nosql'..." -ForegroundColor Cyan
python app\scripts\init_databases.py

# 3. Arrancar servidor FastAPI
Write-Host ""
Write-Host "[3/3] Iniciando FastAPI en http://localhost:8080..." -ForegroundColor Cyan
Write-Host "  - PostgreSQL: localhost:5432 (Base: legadovivo_db)" -ForegroundColor Green
Write-Host "  - MongoDB:    localhost:27017 (Base: legadovivo_nosql)" -ForegroundColor Green
Write-Host "  - ChromaDB:   ./chroma_storage (Persistencia en disco)" -ForegroundColor Green
Write-Host "  - Ollama:     http://localhost:11434" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona Ctrl + C para detener el servidor." -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
