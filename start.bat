@echo off
TITLE LegadoVivo - Launcher del MVP
echo ========================================================
echo               LegadoVivo - Sistema de Inicio
echo ========================================================
echo.
echo Seleccione una opcion:
echo [1] Iniciar Sistema Completo (Backend + Frontend)
echo [2] Iniciar Backend FastAPI (http://localhost:8080)
echo [3] Iniciar Frontend Web (http://localhost:5173)
echo [4] Iniciar Infraestructura con Docker Compose
echo [5] Salir
echo.
set /p opt="Opcion [1-5]: "

if "%opt%"=="1" (
    echo.
    echo Levantando Backend FastAPI en una ventana independiente...
    start "LegadoVivo - Backend" cmd /k ""%~dp0start-backend.bat""
    timeout /t 3 /nobreak >nul
    echo.
    echo Iniciando Frontend en http://localhost:5173 ...
    cd /d "%~dp0frontend"
    if not exist "node_modules" (
        echo Instalando dependencias de frontend (npm install)...
        call npm install
    )
    npm run dev
    pause
    exit /b 0
)

if "%opt%"=="2" (
    call "%~dp0start-backend.bat"
    exit /b 0
)

if "%opt%"=="3" (
    echo.
    echo Iniciando Frontend en http://localhost:5173 ...
    cd /d "%~dp0frontend"
    if not exist "node_modules" (
        echo Instalando dependencias de frontend (npm install)...
        call npm install
    )
    npm run dev
    pause
    exit /b 0
)

if "%opt%"=="4" (
    echo.
    echo Levantando PostgreSQL, MongoDB, ChromaDB, Ollama y Backend...
    where docker >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Docker no esta instalado o no se encuentra en el PATH.
        pause
        exit /b 1
    )
    docker compose up -d
    echo.
    echo Servicios levantados exitosamente.
    pause
    exit /b 0
)

if "%opt%"=="5" exit /b 0
