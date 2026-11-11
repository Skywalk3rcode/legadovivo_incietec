@echo off
setlocal enabledelayedexpansion
TITLE LegadoVivo - Launcher del MVP
echo ========================================================
echo               LegadoVivo - Sistema de Inicio
echo ========================================================
echo.
echo Seleccione una opcion:
echo [1] Iniciar Frontend Web (React + Vite + Tailwind)
echo [2] Iniciar Infraestructura Completa con Docker Compose
echo [3] Ejecutar Backend FastAPI con Python local
echo [4] Verificar Diagnostico de Salud (API y Dependencias)
echo [5] Salir
echo.
set /p opt="Opcion [1-5]: "

if "%opt%"=="1" (
    echo.
    echo [Frontend] Verificando instalacion de Node.js...
    where npm >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] No se encontro 'npm' en el PATH.
        echo Por favor instala Node.js 18 o superior desde: https://nodejs.org/
        pause
        exit /b 1
    )
    cd /d "%~dp0frontend"
    if not exist "node_modules\" (
        echo Instalando dependencias de Node.js por primera vez...
        call npm install
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Fallo npm install.
            pause
            exit /b 1
        )
    )
    echo Iniciando Frontend en http://localhost:5173 ...
    call npm run dev
    pause
)

if "%opt%"=="2" (
    echo.
    echo [Docker] Verificando que Docker este instalado y activo...
    where docker >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Docker no esta en el PATH del sistema.
        echo Instala Docker Desktop para Windows desde: https://www.docker.com/products/docker-desktop/
        echo Asegurate de que Docker Desktop este abierto y ejecutandose.
        pause
        exit /b 1
    )

    docker info >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] El demonio de Docker Desktop no esta respondiendo.
        echo Por favor inicia Docker Desktop en Windows y espera a que este en verde ('Engine running').
        pause
        exit /b 1
    )

    echo.
    echo Levantando PostgreSQL, MongoDB, ChromaDB, Ollama y Backend con Docker Compose...
    cd /d "%~dp0"
    docker compose up -d --build
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Ocurrio un error al ejecutar 'docker compose up'.
        pause
        exit /b 1
    )

    echo.
    echo ========================================================
    echo  Servicios levantados en segundo plano:
    echo  - Backend API:   http://localhost:8080/docs
    echo  - Salud API:     http://localhost:8080/api/health
    echo  - Ollama LLM:    http://localhost:11434
    echo ========================================================
    echo El servicio 'ollama_pull' descargara o verificara 'llama3:8b' automaticamente.
    echo Para iniciar el frontend, abre otra terminal y ejecuta la opcion [1] o:
    echo   cd frontend ^&^& npm run dev
    echo ========================================================
    docker compose ps
    pause
)

if "%opt%"=="3" (
    echo.
    echo [Backend] Iniciando preparacion de entorno local Python...
    cd /d "%~dp0"
    call setup-backend.bat
)

if "%opt%"=="4" (
    echo.
    echo Consultando endpoint de diagnostico: http://localhost:8080/api/health ...
    powershell -NoProfile -Command "try { $res = Invoke-RestMethod -Uri 'http://localhost:8080/api/health' -TimeoutSec 5; $res | ConvertTo-Json -Depth 5 } catch { Write-Host '[ALERTA] Backend no responde en http://localhost:8080. Verifique si los contenedores estan activos con docker compose ps' -ForegroundColor Red }"
    echo.
    pause
)

if "%opt%"=="5" exit


