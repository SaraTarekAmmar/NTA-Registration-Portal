@echo off
TITLE NTA Portal - Account Installer
REM =========================================================
REM NTA REGISTRATION PORTAL - STANDALONE ACCOUNT SEEDER
REM Installs / updates ALL accounts without restarting servers.
REM
REM Use this after a fresh deploy or after editing:
REM   - trainee_accounts.txt
REM   - trainer_accounts.txt
REM   - admin/apply_default_credentials.py
REM =========================================================

cd /d "%~dp0"

where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo.
echo =======================================================
echo [*] Step 1/3 - Syncing DB credentials from credentials.txt...
python update_credentials.py
echo.

echo [*] Step 2/3 - Applying staff credentials (admin, editor, superadmin, trainers, trainees)...
set ADMIN_VENV=..\admin\backend\venv\Scripts\python.exe
if not exist %ADMIN_VENV% (
    echo [ERROR] Admin venv not found. Please run RUN_SYSTEM.bat first.
    pause
    exit /b 1
)

%ADMIN_VENV% ..\admin\apply_default_credentials.py
echo.

echo [*] Step 3a/3 - Installing trainees from trainee_accounts.txt...
%ADMIN_VENV% install_trainees.py
echo.

echo [*] Step 3b/3 - Installing trainers from trainer_accounts.txt...
%ADMIN_VENV% install_trainers.py
echo.

echo =======================================================
echo [SUCCESS] All accounts have been installed / updated.
echo =======================================================
pause
