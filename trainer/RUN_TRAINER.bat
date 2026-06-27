@echo off
title NTA Trainer Portal - Port 8006
cd /d "%~dp0"

echo ================================================
echo  NTA Trainer Portal  (port 8006)
echo ================================================
echo.

REM Check venv exists
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at trainer\backend\venv
    echo Please run: python -m venv trainer\backend\venv
    echo Then: trainer\backend\venv\Scripts\pip install -r trainer\backend\requirements.txt
    pause
    exit /b 1
)

echo [OK] Starting Trainer Portal backend on http://127.0.0.1:8006
echo      Press CTRL+C to stop.
echo.

start "" http://127.0.0.1:8006/

backend\venv\Scripts\python.exe -m uvicorn backend.main:app ^
    --host 127.0.0.1 ^
    --port 8006 ^
    --reload

pause
