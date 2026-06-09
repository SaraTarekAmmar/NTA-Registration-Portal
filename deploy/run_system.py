#!/usr/bin/env python3
"""
NTA Registration Portal - Universal Smart Launcher
===================================================
Runs on Windows, Linux, and macOS.
Detects paths automatically - no hardcoded configuration needed.
"""

import subprocess
import sys
import os
import time
import platform
import shutil
import argparse

# ─────────────────────────────────────────────
# 1. PATH DETECTION
# ─────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)
USER_DIR    = os.path.join(BASE_DIR, 'user')
ADMIN_DIR   = os.path.join(BASE_DIR, 'admin')
SUPERADMIN_DIR = os.path.join(BASE_DIR, 'superadmin')

IS_WINDOWS = platform.system() == 'Windows'
PYTHON_BIN  = "python" if IS_WINDOWS else "python3"

# ─── ARGUMENT PARSING ───
parser = argparse.ArgumentParser(description="NTA Portal Launcher")
parser.add_argument("--headless", "--ssh", action="store_true", help="Run without opening browser (SSH/Linux mode)")
parser.add_argument("--seed", action="store_true", help="Populate database with dropdown and fake data")
args = parser.parse_args()

# Force headless if no display or explicitly requested
IS_HEADLESS = args.headless or (not IS_WINDOWS and not os.environ.get("DISPLAY"))

def venv_python(base):
    if IS_WINDOWS:
        return os.path.join(base, 'backend', 'venv', 'Scripts', 'python.exe')
    return os.path.join(base, 'backend', 'venv', 'bin', 'python')

def venv_pip(base):
    if IS_WINDOWS:
        return os.path.join(base, 'backend', 'venv', 'Scripts', 'pip.exe')
    return os.path.join(base, 'backend', 'venv', 'bin', 'pip')

# ─────────────────────────────────────────────
# 2. SETUP FUNCTIONS
# ─────────────────────────────────────────────
def verify_directories():
    for d in [USER_DIR, ADMIN_DIR, SUPERADMIN_DIR]:
        if not os.path.isdir(d):
            print(f"[ERROR] Missing directory: {d}")
            sys.exit(1)

def ensure_venv(portal_dir, portal_name):
    venv_dir = os.path.join(portal_dir, 'backend', 'venv')
    py_exec   = venv_python(portal_dir)
    req_file  = os.path.join(portal_dir, 'backend', 'requirements.txt')

    if os.path.isfile(py_exec):
        try:
            subprocess.run([py_exec, '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, OSError):
            print(f"[{portal_name}] Broken virtual environment detected. Removing it to recreate...")
            shutil.rmtree(venv_dir, ignore_errors=True)

    if not os.path.isfile(py_exec):
        print(f"[{portal_name}] Creating virtual environment...")
        subprocess.run([PYTHON_BIN, '-m', 'venv', venv_dir], check=True)

    if os.path.isfile(req_file):
        pip = venv_pip(portal_dir)
        print(f"[{portal_name}] Upgrading pip...")
        subprocess.run([pip, 'install', '--upgrade', 'pip'], check=False)
        
        print(f"[{portal_name}] Synchronizing dependencies (this may take a minute)...")
        subprocess.run([pip, 'install', '-r', req_file], check=False)

def verify_env_file(portal_dir, portal_name):
    env_file = os.path.join(portal_dir, 'backend', '.env')
    if not os.path.isfile(env_file):
        print(f"[WARNING] {portal_name}: .env missing at {env_file}")

def free_port(port):
    if IS_WINDOWS:
        try:
            output = subprocess.check_output(f'netstat -aon | findstr :{port}', shell=True).decode()
            for line in output.splitlines():
                pid = line.strip().split()[-1]
                if pid.isdigit(): os.system(f'taskkill /F /T /PID {pid} 2>nul')
        except: pass
    else:
        try: subprocess.run(['fuser', '-k', f'{port}/tcp'], stderr=subprocess.DEVNULL)
        except: pass

# ─────────────────────────────────────────────
# 3. EXECUTION
# ─────────────────────────────────────────────
def start_server(portal_dir, portal_name, port):
    py = venv_python(portal_dir)
    cmd = [
        py, '-m', 'uvicorn', 'backend.main:app',
        '--port', str(port),
        '--host', '0.0.0.0',
        '--http', 'h11',
        '--loop', 'asyncio'
    ]

    log_dir = os.path.join(portal_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f'{portal_name.lower().replace(" ", "_")}.log')

    if IS_WINDOWS and not IS_HEADLESS:
        # On Windows, we open a new console window to show the logs
        proc = subprocess.Popen(cmd, cwd=portal_dir,
                                creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        # On Linux/SSH or headless, we still log to a file
        log_file = open(log_path, 'w')
        proc = subprocess.Popen(cmd, cwd=portal_dir, stdout=log_file, stderr=log_file)

    print(f"[{portal_name}] Started (PID {proc.pid}). Log: {log_path}")
    return proc, log_path


def check_server_alive(proc, log_path, portal_name, wait=5):
    time.sleep(wait)
    if proc.poll() is not None:
        print(f"")
        print(f"  ╔══════════════════════════════════════════════════╗")
        print(f"  ║  [CRASH] {portal_name} server stopped immediately!  ║")
        print(f"  ╚══════════════════════════════════════════════════╝")
        print(f"  Reason (from log: {log_path}):")
        print(f"  {'─' * 50}")
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            for line in lines[-20:]:
                print(f"  | {line.rstrip()}")
        except Exception as e:
            print(f"  [Could not read log: {e}]")
        print(f"  {'─' * 50}")
        return False
    return True

def main():
    print("=" * 55)
    print("NTA REGISTRATION PORTAL - MASTER LAUNCHER")
    print("=" * 55)

    verify_directories()

    ensure_venv(USER_DIR,  "User")
    ensure_venv(ADMIN_DIR, "Admin")
    ensure_venv(SUPERADMIN_DIR, "Super Admin")

    config_script = os.path.join(SCRIPT_DIR, 'update_credentials.py')
    if os.path.isfile(config_script):
        print("[*] Synchronizing MySQL credentials from credentials.txt...")
        subprocess.run([sys.executable, config_script], check=False)

    init_script = os.path.join(SCRIPT_DIR, 'init_db.py')
    if os.path.isfile(init_script):
        print("[*] Automatically initializing database schema...")
        subprocess.run([venv_python(ADMIN_DIR), init_script], check=False)

    # SEEDING LOGIC
    if args.seed:
        print("\n" + "─" * 40)
        print("[*] RUNNING FULL DATABASE SEEDING...")
        
        dropdown_script = os.path.join(SCRIPT_DIR, 'seed_dropdown_data.py')
        if os.path.isfile(dropdown_script):
            print("[*] Seeding dropdown master data (Countries, Skills, etc.)...")
            subprocess.run([venv_python(ADMIN_DIR), dropdown_script], check=False)
            
        fake_data_script = os.path.join(SCRIPT_DIR, 'seed_fake_data.py')
        if os.path.isfile(fake_data_script):
            print("[*] Seeding fake trainee profiles for testing...")
            subprocess.run([venv_python(ADMIN_DIR), fake_data_script], check=False)
            
        print("─" * 40 + "\n")

    seed_exams_script = os.path.join(SCRIPT_DIR, 'seed_exams.py')
    if os.path.isfile(seed_exams_script):
        print("[*] Automatically seeding standardized exams...")
        subprocess.run([venv_python(ADMIN_DIR), seed_exams_script], check=False)

    creds_script = os.path.join(ADMIN_DIR, 'apply_default_credentials.py')
    if os.path.isfile(creds_script):
        print("[*] Applying default hashed passwords for All Roles...")
        subprocess.run([venv_python(ADMIN_DIR), creds_script], check=False)

    trainees_script = os.path.join(SCRIPT_DIR, 'install_trainees.py')
    if os.path.isfile(trainees_script):
        print("[*] Syncing trainee accounts from trainee_accounts.txt...")
        subprocess.run([venv_python(ADMIN_DIR), trainees_script], check=False)

    trainers_script = os.path.join(SCRIPT_DIR, 'install_trainers.py')
    if os.path.isfile(trainers_script):
        print("[*] Syncing trainer accounts from trainer_accounts.txt...")
        subprocess.run([venv_python(ADMIN_DIR), trainers_script], check=False)

    check_script = os.path.join(SCRIPT_DIR, 'check_db.py')
    if os.path.isfile(check_script):
        print("[*] Checking database connectivity...")
        result = subprocess.run([venv_python(ADMIN_DIR), check_script], check=False)
        if result.returncode != 0:
            print("[ABORTED] Database connection failed.")
            sys.exit(1)

    free_port(7771)
    free_port(8002)
    free_port(8003)
    time.sleep(1)

    user_proc, user_log   = start_server(USER_DIR,  "User Portal",  7771)
    admin_proc, admin_log = start_server(ADMIN_DIR, "Admin Portal", 8002)
    super_proc, super_log = start_server(SUPERADMIN_DIR, "Super Admin", 8003)

    print()
    print("[*] Verifying servers...")
    user_ok  = check_server_alive(user_proc,  user_log,  "User Portal")
    admin_ok = check_server_alive(admin_proc, admin_log, "Admin Portal")
    super_ok = check_server_alive(super_proc, super_log, "Super Admin")

    if not IS_HEADLESS:
        import webbrowser
        time.sleep(1)
        print()
        print("[SUCCESS] All NTA Portals are running!")
        print("  User Portal  -> http://127.0.0.1:7771/")
        print("  Admin Portal -> http://127.0.0.1:8002/")
        print("  Control Center -> http://127.0.0.1:8003/")
        print()
        webbrowser.open("http://127.0.0.1:7771/")
        webbrowser.open("http://127.0.0.1:8002/")
        webbrowser.open("http://127.0.0.1:8003/")
        input("\nPress Enter to exit launcher (servers stay running)...\n")

if __name__ == '__main__':
    main()
