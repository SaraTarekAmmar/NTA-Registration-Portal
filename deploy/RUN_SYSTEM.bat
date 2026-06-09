@echo off
TITLE NTA Portal Launcher
REM =========================================================
REM NTA REGISTRATION PORTAL - WINDOWS LAUNCHER
REM This script delegates ALL logic to run_system.py
REM It works from ANY location - no hardcoded paths.
REM =========================================================

REM Change to the directory where this .bat file is located
cd /d "%~dp0"

REM Check if Python is available
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Launch the universal Python script
python run_system.py

echo.
echo [LAUNCHER] Script finished.
pause
