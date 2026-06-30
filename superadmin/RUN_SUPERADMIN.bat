@echo off
TITLE NTA Super Admin Portal
SETLOCAL EnableDelayedExpansion

REM Change to the directory of this batch file
cd /d "%~dp0"

REM 1. Kill any process on port 8003
echo [PRE-FLIGHT] Checking for existing processes on port 8003...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8003') do (
    echo [CLEANUP] Killing PID %%a...
    taskkill /F /T /PID %%a 2>nul
)

REM 2. Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM 3. Create the virtual environment if it does not exist yet
if not exist "backend\venv\Scripts\python.exe" (
    echo [SETUP] Virtual environment not found. Creating it now...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SETUP] Installing dependencies ^(first run may take a minute^)...
    "backend\venv\Scripts\python.exe" -m pip install --upgrade pip
    "backend\venv\Scripts\python.exe" -m pip install --default-timeout=100 -r backend\requirements.txt
)

REM 4. Verify venv can actually run
"backend\venv\Scripts\python.exe" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Broken virtual environment. Delete 'backend\venv' and run this again.
    pause
    exit /b 1
)

REM 5. Synchronize dependencies
echo [SYNC] Synchronizing backend dependencies...
"backend\venv\Scripts\python.exe" -m pip install --default-timeout=100 -r backend\requirements.txt >nul 2>&1

echo.
echo [STARTING] Starting Super Admin Backend (Port 8003)...
echo [INFO] Open http://127.0.0.1:8003/ in your browser.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8003/'"
echo [INFO] If the window closes immediately, check the output above for errors.
"backend\venv\Scripts\python.exe" -m uvicorn main:app --app-dir backend --port 8003 --host 127.0.0.1
if %errorlevel% neq 0 (
    echo.
    echo [CRASH] Server exited with an error. See output above.
)
pause
exit /b 0
