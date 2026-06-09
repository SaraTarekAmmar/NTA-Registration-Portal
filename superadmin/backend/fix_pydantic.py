import subprocess
import sys
import os

def fix():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
    
    if not os.path.exists(venv_python):
        print(f"[ERROR] Venv not found at {venv_python}")
        return

    print("[*] Installing missing Pydantic email validation engine...")
    
    try:
        subprocess.run([venv_python, "-m", "pip", "install", "email-validator"], check=True)
        print("\n[SUCCESS] Final dependency synchronized.")
        print("[ACTION] You can now restart your server.")
    except subprocess.CalledProcessError as e:
        print(f"[FAILED] Error during installation: {e}")

if __name__ == "__main__":
    fix()
