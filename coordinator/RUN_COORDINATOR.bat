@echo off
TITLE NTA Coordinator Portal
SETLOCAL EnableDelayedExpansion

REM Change to the directory of this batch file
cd /d "%~dp0"

REM 1. Kill any process on port 8005
echo [PRE-FLIGHT] Checking for existing processes on port 8005...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8005') do (
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

REM 5. Synchronize Dependencies
echo [SYNC] Synchronizing backend dependencies...
"backend\venv\Scripts\python.exe" -m pip install --default-timeout=100 -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Dependency sync failed. Trying to continue...
)

REM 6. Check Database Connection
echo.
echo [DB CHECK] Verifying MySQL connection...
"backend\venv\Scripts\python.exe" "..\deploy\check_db.py"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Database connection failed!
    echo Fix the issue above, then try again.
    echo.
    echo HINT: Edit 'deploy\credentials.txt' with your MySQL root password.
    pause
    exit /b 1
)

:START_SERVER
echo [SUCCESS] Virtual environment and database verified.
echo [STARTING] Starting Coordinator Portal Backend (Port 8005)...
echo [INFO] Open http://localhost:8005/coordinator-login.html in your browser.
echo [INFO] If the window closes immediately, check the output above for errors.
"backend\venv\Scripts\python.exe" -m uvicorn main:app --app-dir backend --port 8005 --host 127.0.0.1 --http h11 --loop asyncio
if %errorlevel% neq 0 (
    echo.
    echo [CRASH] Server exited with an error. See output above.
    echo Common fix: Check your MySQL password in deploy\credentials.txt
)
pause
exit /b 0
