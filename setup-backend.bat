@echo off
TITLE LegadoVivo - Setup y Arranque del Backend
echo ========================================================
echo          LegadoVivo - Servidor Backend FastAPI
echo ========================================================
echo.

cd /d "%~dp0backend"

echo [1/3] Verificando instalacion de Python...
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :PYTHON_OK

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :PY_LAUNCHER_OK

echo [ERROR] No se encontro Python en tu sistema.
echo Por favor instala Python 3.11 o 3.12 desde https://www.python.org/downloads/
echo Recuerda marcar la casilla: Add python.exe to PATH
pause
exit /b 1

:PY_LAUNCHER_OK
set PY_CMD=py -3
goto :CHECK_VENV

:PYTHON_OK
set PY_CMD=python
goto :CHECK_VENV

:CHECK_VENV
echo Python detectado correctamente.
echo.

if exist "venv\Scripts\activate.bat" goto :START_SERVER

echo [2/3] Creando entorno virtual venv...
%PY_CMD% -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al crear el entorno virtual.
    pause
    exit /b 1
)

echo Entorno virtual creado exitosamente.
echo.
echo [3/3] Instalando dependencias desde requirements.txt...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)

:START_SERVER
echo Entorno virtual listo.
call venv\Scripts\activate.bat
echo.
echo ========================================================
echo       Iniciando FastAPI en http://localhost:8080
echo ========================================================
echo Presiona Ctrl + C para detener el servidor.
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
pause
