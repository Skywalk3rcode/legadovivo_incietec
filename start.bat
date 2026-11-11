@echo off
TITLE LegadoVivo - Launcher del MVP
echo ========================================================
echo               LegadoVivo - Sistema de Inicio
echo ========================================================
echo.
echo Seleccione una opcion:
echo [1] Iniciar Frontend Web (React + Vite + Tailwind)
echo [2] Iniciar Infraestructura Completa con Docker Compose
echo [3] Ejecutar Backend FastAPI con Python local
echo [4] Salir
echo.
set /p opt="Opcion [1-4]: "

if "%opt%"=="1" (
    echo.
    echo Iniciando Frontend en http://localhost:5173 ...
    cd frontend
    npm run dev
)

if "%opt%"=="2" (
    echo.
    echo Levantando PostgreSQL, MongoDB, ChromaDB, Ollama y Backend...
    docker compose up -d
    echo.
    echo Servicios levantados exitosamente.
    pause
)

if "%opt%"=="3" (
    echo.
    echo Iniciando Backend FastAPI en http://localhost:8080 ...
    cd backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
)

if "%opt%"=="4" exit

