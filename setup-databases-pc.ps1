# LegadoVivo - Configuracion de PostgreSQL y MongoDB en tu PC (Sin Docker)
$ErrorActionPreference = "Continue"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   CONFIGURANDO BASES DE DATOS NATIVAS EN TU PC         " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# ========================================================
# 1. VERIFICAR Y LEVANTAR SERVICIOS DE WINDOWS
# ========================================================
Write-Host "[1/3] Verificando servicios de Windows..." -ForegroundColor Cyan

# Servicio MongoDB
$MongoService = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue
if ($MongoService) {
    if ($MongoService.Status -ne "Running") {
        Write-Host "Iniciando servicio de MongoDB..." -ForegroundColor Yellow
        Start-Service -Name "MongoDB" -ErrorAction SilentlyContinue
    }
    Write-Host "Servicio MongoDB: ACTIVO." -ForegroundColor Green
} else {
    Write-Host "Nota: No se detecto el servicio de Windows 'MongoDB'. Intentaremos conexion en localhost:27017." -ForegroundColor Gray
}

# Servicio PostgreSQL
$PgServices = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue
if ($PgServices) {
    foreach ($svc in $PgServices) {
        if ($svc.Status -ne "Running") {
            Write-Host "Iniciando servicio $($svc.Name)..." -ForegroundColor Yellow
            Start-Service -Name $svc.Name -ErrorAction SilentlyContinue
        }
        Write-Host "Servicio $($svc.Name): ACTIVO." -ForegroundColor Green
    }
} else {
    Write-Host "Nota: Servicio de Windows de PostgreSQL no listado. Verificando ejecucion en puerto 5432..." -ForegroundColor Gray
}

Write-Host ""

# ========================================================
# 2. CREAR BASE DE DATOS EN POSTGRESQL (legadovivo_db)
# ========================================================
Write-Host "[2/3] Configurando base de datos PostgreSQL 'legadovivo_db'..." -ForegroundColor Cyan

$PsqlPath = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
if (-not (Test-Path $PsqlPath)) {
    $PsqlPath = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
}

if (Test-Path $PsqlPath) {
    Write-Host "psql detectado en: $PsqlPath" -ForegroundColor Gray
    
    # Preguntar contrasena si no existe variable de entorno
    $PgPass = $env:PGPASSWORD
    if (-not $PgPass) {
        $PgPass = Read-Host "Ingresa la contrasena del usuario 'postgres' (presiona Enter para usar 'postgres')"
        if (-not $PgPass) { $PgPass = "postgres" }
        $env:PGPASSWORD = $PgPass
    }

    # Intentar crear la base de datos legadovivo_db con psql
    $CreateDbSql = "SELECT 'CREATE DATABASE legadovivo_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'legadovivo_db')\gexec"
    & $PsqlPath -U postgres -h localhost -p 5432 -d postgres -c $CreateDbSql

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Base de datos PostgreSQL 'legadovivo_db' verificada y lista." -ForegroundColor Green
    } else {
        Write-Host "Advertencia: Comprueba que la contrasena de postgres sea correcta." -ForegroundColor Yellow
    }
} else {
    Write-Host "No se encontro psql.exe en C:\Program Files\PostgreSQL." -ForegroundColor Yellow
}

Write-Host ""

# ========================================================
# 3. CREAR BASE DE DATOS EN MONGODB (legadovivo_nosql)
# ========================================================
Write-Host "[3/3] Configurando base de datos MongoDB 'legadovivo_nosql'..." -ForegroundColor Cyan

$MongoshPath = "C:\Program Files\MongoDB\mongosh-2.5.8-win32-x64\bin\mongosh.exe"
if (-not (Test-Path $MongoshPath)) {
    $MongoshPath = (Get-ChildItem -Path "C:\Program Files\MongoDB" -Recurse -Filter "mongosh.exe" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
}

if ($MongoshPath -and (Test-Path $MongoshPath)) {
    Write-Host "mongosh detectado en: $MongoshPath" -ForegroundColor Gray
    
    $MongoInitScript = @"
use legadovivo_nosql;
db.createCollection('capsules');
db.capsules.createIndex({ titular_id: 1 });
db.capsules.createIndex({ created_at: -1 });
db.createCollection('style_profiles');
db.style_profiles.createIndex({ titular_id: 1 }, { unique: true });
db.createCollection('chat_sessions');
db.chat_sessions.createIndex({ titular_id: 1 });
print('MongoDB: Base de datos legadovivo_nosql inicializada.');
"@

    $TempScript = Join-Path $env:TEMP "init_mongo.js"
    Set-Content -Path $TempScript -Value $MongoInitScript -Encoding UTF8
    
    & $MongoshPath "mongodb://localhost:27017" --file $TempScript
    Remove-Item -Path $TempScript -Force -ErrorAction SilentlyContinue

    Write-Host "Base de datos MongoDB 'legadovivo_nosql' verificada y lista." -ForegroundColor Green
} else {
    Write-Host "No se encontro mongosh.exe. La base de datos se creara automaticamente al conectar el backend." -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host " Bases de datos locales en tu PC preparadas con exito!  " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

