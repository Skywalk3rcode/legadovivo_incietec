@echo off
TITLE LegadoVivo - Servidor Backend FastAPI
echo ========================================================
echo        LegadoVivo - Servidor Backend FastAPI
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "ROOT_DIR=%SCRIPT_DIR%"

:: 1. Detectar entorno virtual (en raiz o en backend)
set "VENV_DIR="
if exist "%ROOT_DIR%venv\Scripts\activate.bat" (
    set "VENV_DIR=%ROOT_DIR%venv"
) else if exist "%BACKEND_DIR%venv\Scripts\activate.bat" (
    set "VENV_DIR=%BACKEND_DIR%venv"
)

if "%VENV_DIR%"=="" (
    echo [AVISO] No se detecto un entorno virtual configurado.
    echo Ejecutando configuracion inicial con setup-backend.bat...
    call "%SCRIPT_DIR%setup-backend.bat"
    exit /b %ERRORLEVEL%
)

echo Usando entorno virtual: %VENV_DIR%
call "%VENV_DIR%\Scripts\activate.bat"

cd /d "%BACKEND_DIR%"

echo.
echo [1/2] Verificando bases de datos en PostgreSQL...
python app\scripts\init_databases.py

echo.
echo [2/2] Iniciando FastAPI en http://localhost:8080...
echo   - PostgreSQL: localhost:5432 (legadovivo_db)
echo   - ChromaDB:   ./chroma_storage
echo   - Ollama:     http://localhost:11434
echo.
echo Presiona Ctrl + C para detener el servidor.
echo ========================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] El servidor backend se detuvo con codigo de error %ERRORLEVEL%.
    pause
)
