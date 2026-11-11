# Script para crear la base de datos legadovivo_db en PostgreSQL
$ErrorActionPreference = "Continue"

if (-not $env:PGPASSWORD) {
    $env:PGPASSWORD = "12345"
}

Write-Host "Conectando a PostgreSQL en localhost:5432 con usuario 'postgres'..." -ForegroundColor Cyan

# Buscar psql.exe en rutas tipicas
$PsqlCandidates = @(
    "C:\Users\$env:USERNAME\Documents\PostgreSQL\18\bin\psql.exe",
    "C:\Users\$env:USERNAME\Documents\PostgreSQL\17\bin\psql.exe",
    "C:\Program Files\PostgreSQL\18\bin\psql.exe",
    "C:\Program Files\PostgreSQL\17\bin\psql.exe",
    "C:\Program Files\PostgreSQL\16\bin\psql.exe"
)

$Psql = $null
foreach ($cand in $PsqlCandidates) {
    if (Test-Path $cand) {
        $Psql = $cand
        break
    }
}

if (-not $Psql) {
    $found = Get-Command psql -ErrorAction SilentlyContinue
    if ($found) { $Psql = $found.Source }
}

if ($Psql) {
    Write-Host "psql.exe encontrado en: $Psql" -ForegroundColor Green
    Write-Host "Ejecutando creacion de base de datos 'legadovivo_db'..." -ForegroundColor Yellow
    $Exists = & $Psql -U postgres -h localhost -p 5432 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'legadovivo_db'"
    if ($Exists.Trim() -ne "1") {
        & $Psql -U postgres -h localhost -p 5432 -d postgres -c "CREATE DATABASE legadovivo_db ENCODING 'UTF8';"
    } else {
        Write-Host "La base de datos 'legadovivo_db' ya existe." -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Verificando bases de datos en PostgreSQL:" -ForegroundColor Cyan
    & $Psql -U postgres -h localhost -p 5432 -d postgres -c "\l"
    Write-Host ""
    Write-Host "¡Base de datos 'legadovivo_db' lista en PostgreSQL!" -ForegroundColor Green
} else {
    Write-Host "No se encontro psql.exe en las rutas estandar de PostgreSQL." -ForegroundColor Red
}
