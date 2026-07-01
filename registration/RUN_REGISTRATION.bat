@echo off
TITLE NTA Registration Site
SETLOCAL EnableDelayedExpansion
cd /d "%~dp0"
echo [PRE-FLIGHT] Checking for existing processes on port 7775...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :7775') do ( taskkill /F /T /PID %%a 2>nul )
where python >nul 2>&1 || ( echo [ERROR] Python not in PATH. & pause & exit /b 1 )
if not exist "backend\venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment...
    python -m venv backend\venv || ( echo [ERROR] venv failed. & pause & exit /b 1 )
    "backend\venv\Scripts\python.exe" -m pip install --upgrade pip
    "backend\venv\Scripts\python.exe" -m pip install --default-timeout=100 -r backend\requirements.txt
)
"backend\venv\Scripts\python.exe" -m pip install --default-timeout=100 -r backend\requirements.txt >nul 2>&1
echo [STARTING] Registration Site (Port 7775)...
echo [INFO] Open http://127.0.0.1:7775/index.html in your browser.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:7775/index.html'"
"backend\venv\Scripts\python.exe" -m uvicorn main:app --app-dir backend --port 7775 --host 127.0.0.1
if %errorlevel% neq 0 ( echo. & echo [CRASH] Server exited with an error. See output above. )
pause
exit /b 0
