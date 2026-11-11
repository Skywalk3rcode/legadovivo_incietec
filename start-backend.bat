@echo off
TITLE LegadoVivo - Servidor Backend (PostgreSQL & MongoDB en PC)
echo ========================================================
echo   LegadoVivo - PostgreSQL y MongoDB Nativos en tu PC
echo ========================================================
echo.

cd /d "%~dp0backend"

echo [1/3] Verificando dependencias en Python...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 goto ERROR_PIP

echo.
echo [2/3] Verificando bases de datos en PostgreSQL y MongoDB...
python app\scripts\init_databases.py

echo.
echo [3/3] Iniciando FastAPI en http://localhost:8080...
echo   - PostgreSQL: localhost:5432 (legadovivo_db)
echo   - MongoDB:    localhost:27017 (legadovivo_nosql)
echo   - ChromaDB:   ./chroma_storage
echo   - Ollama:     http://localhost:11434
echo.
echo Presiona Ctrl + C para detener el servidor.
echo ========================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
pause
exit /b 0

:ERROR_PIP
echo.
echo [ERROR] Hubo un problema instalando dependencias con pip.
pause
exit /b 1
