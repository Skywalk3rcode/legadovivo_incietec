@echo off
TITLE LegadoVivo - Setup y Servidor Backend FastAPI
echo ========================================================
echo       LegadoVivo - Setup Backend FastAPI
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "ROOT_DIR=%SCRIPT_DIR%"

echo [1/4] Verificando instalacion de Python...
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
    goto PYTHON_DETECTED
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=py -3
    goto PYTHON_DETECTED
)

echo [ERROR] No se encontro Python en tu sistema.
echo Por favor instala Python 3.11, 3.12 o 3.13 desde https://www.python.org/downloads/
echo Recuerda marcar la casilla: Add python.exe to PATH
pause
exit /b 1

:PYTHON_DETECTED
echo Python detectado: %PY_CMD%
echo.

:: Detectar o crear entorno virtual
set "VENV_DIR="
if exist "%ROOT_DIR%venv\Scripts\activate.bat" (
    set "VENV_DIR=%ROOT_DIR%venv"
) else if exist "%BACKEND_DIR%venv\Scripts\activate.bat" (
    set "VENV_DIR=%BACKEND_DIR%venv"
)

if not "%VENV_DIR%"=="" goto VENV_EXISTS

echo [2/4] Creando entorno virtual venv en %ROOT_DIR%venv...
%PY_CMD% -m venv "%ROOT_DIR%venv"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al crear el entorno virtual.
    pause
    exit /b 1
)
set "VENV_DIR=%ROOT_DIR%venv"
echo Entorno virtual creado exitosamente.

:VENV_EXISTS
echo Usando entorno virtual: %VENV_DIR%
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo [3/4] Instalando / verificando dependencias en Python...
python -m pip install --upgrade pip
pip install -r "%BACKEND_DIR%\requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al instalar dependencias con pip.
    pause
    exit /b 1
)

echo.
echo [4/4] Verificando bases de datos...
cd /d "%BACKEND_DIR%"
python app\scripts\init_databases.py

echo.
echo ========================================================
echo       Iniciando FastAPI en http://localhost:8080
echo ========================================================
echo Presiona Ctrl + C para detener el servidor.
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] El servidor backend se detuvo.
    pause
)
