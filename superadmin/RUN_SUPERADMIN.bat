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
    pause
    exit /b 1
)

REM 3. Check for virtual environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment missing at superadmin\backend\venv
    pause
    exit /b 1
)

echo [NTA] Starting Super Admin Backend on Port 8003...
echo [NTA] Dashboard: http://localhost:8003

REM Launch browser automatically
start http://localhost:8003

REM Run the FastAPI app
cd backend
"venv\Scripts\python.exe" -m uvicorn main:app --port 8003 --reload
if %errorlevel% neq 0 (
    echo.
    echo [CRASH] Super Admin server exited with an error.
)

pause
exit /b 0
