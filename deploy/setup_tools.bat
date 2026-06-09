@echo off
setlocal
title NTA Portal - Environment Setup Tool

echo =======================================================
echo NTA REGISTRATION PORTAL - ENVIRONMENT SETUP
echo =======================================================
echo This script will install MySQL Server and MySQL Workbench
echo using Windows Package Manager (winget).
echo.
echo Please run this as Administrator for a smooth installation.
echo =======================================================
echo.

:: Check for winget
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 'winget' not found. Please install App Installer from Microsoft Store.
    pause
    exit /b 1
)

:: 1. Install MySQL Server 8.0
echo [1/3] Installing MySQL Server...
winget install Oracle.MySQL -e --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo [WARNING] MySQL installation returned error code %errorlevel%. 
    echo           It might already be installed or requires manual setup.
) else (
    echo [SUCCESS] MySQL Server installed.
)

:: 2. Install MySQL Workbench
echo [2/3] Installing MySQL Workbench...
winget install Oracle.MySQLWorkbench -e --silent --accept-package-agreements
if %errorlevel% neq 0 (
    echo [WARNING] MySQL Workbench installation returned error code %errorlevel%.
) else (
    echo [SUCCESS] MySQL Workbench installed.
)

:: 3. Install Python 3.10 if missing
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [3/3] Installing Python 3.10...
    winget install Python.Python.3.10 -e --silent --accept-package-agreements
) else (
    echo [3/3] Python is already installed.
)

echo.
echo =======================================================
echo SETUP COMPLETE
echo =======================================================
echo 1. Open MySQL Workbench and note your 'root' password.
echo 2. Open 'deploy\credentials.txt' and set DB_PASSWORD=
echo    to your MySQL root password.
echo 3. Run 'deploy\RUN_SYSTEM.bat' to start the application.
echo    (It will auto-create the database, schema, and accounts.)
echo =======================================================
pause
