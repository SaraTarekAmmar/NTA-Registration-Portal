@echo off
TITLE NTA Portal Seeder
REM =========================================================
REM NTA REGISTRATION PORTAL - DATABASE SEEDER
REM This script populates the database with master data and fake profiles.
REM =========================================================

cd /d "%~dp0"

where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [*] Starting full database seeding...
echo [*] This will populate master data and fake trainee profiles.
echo.

python run_system.py --seed

echo.
echo [SUCCESS] Seeding process finished.
pause
