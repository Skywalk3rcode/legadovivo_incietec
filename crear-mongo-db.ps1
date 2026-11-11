# Script directo para crear y poblar legadovivo_nosql en MongoDB
Write-Host "Conectando a MongoDB local en localhost:27017..." -ForegroundColor Cyan

$Mongosh = "C:\Program Files\MongoDB\mongosh-2.5.8-win32-x64\bin\mongosh.exe"
if (-not (Test-Path $Mongosh)) {
    $Mongosh = (Get-ChildItem -Path "C:\Program Files\MongoDB" -Recurse -Filter "mongosh.exe" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
}

if ($Mongosh) {
    Write-Host "Ejecutando script de inicializacion con mongosh..." -ForegroundColor Yellow
    $ScriptPath = Join-Path $PSScriptRoot "backend\app\scripts\init_mongo_data.js"
    & $Mongosh "mongodb://localhost:27017" --file $ScriptPath
    Write-Host ""
    Write-Host "Verificando bases de datos en MongoDB:" -ForegroundColor Cyan
    & $Mongosh "mongodb://localhost:27017" --eval "show dbs"
} else {
    Write-Host "No se encontro mongosh.exe. Ejecutando con Python..." -ForegroundColor Yellow
    python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['legadovivo_nosql']
db.capsules.insert_one({'title': 'Bienvenida', 'content': 'Recuerdo inicial'})
print('Bases de datos en MongoDB:', client.list_database_names())
"
}

