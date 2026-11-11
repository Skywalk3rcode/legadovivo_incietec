# Script para crear la base de datos legadovivo_db en PostgreSQL
$env:PGPASSWORD = "1040572521"
Write-Host "Conectando a PostgreSQL en localhost:5432 con usuario 'postgres'..." -ForegroundColor Cyan

$Psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
if (-not (Test-Path $Psql)) {
    $Psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
}

if (Test-Path $Psql) {
    Write-Host "Ejecutando creacion de base de datos 'legadovivo_db'..." -ForegroundColor Yellow
    $SqlCmd = "SELECT 'CREATE DATABASE legadovivo_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'legadovivo_db')\gexec"
    & $Psql -U postgres -h localhost -p 5432 -d postgres -c $SqlCmd
    
    Write-Host ""
    Write-Host "Verificando bases de datos en PostgreSQL:" -ForegroundColor Cyan
    & $Psql -U postgres -h localhost -p 5432 -d postgres -c "\l"
    Write-Host ""
    Write-Host "¡Base de datos 'legadovivo_db' lista en PostgreSQL!" -ForegroundColor Green
} else {
    Write-Host "No se encontro psql.exe en C:\Program Files\PostgreSQL" -ForegroundColor Red
}

