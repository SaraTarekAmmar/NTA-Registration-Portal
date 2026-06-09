import os
import re

def update_env_files():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    creds_path = os.path.join(script_dir, "credentials.txt")

    if not os.path.exists(creds_path):
        print("[SKIP] credentials.txt not found. Using existing .env values.")
        return

    # 1. Read the new password
    new_password = None
    with open(creds_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('DB_PASSWORD='):
                new_password = line.split('=')[1].strip()
                break
    
    if new_password is None:
        print("[SKIP] DB_PASSWORD not defined in credentials.txt")
        return

    # 2. Find all .env files
    env_targets = [
        os.path.join(project_root, 'admin', 'backend', '.env'),
        os.path.join(project_root, 'user', 'backend', '.env'),
        os.path.join(project_root, 'superadmin', 'backend', '.env')
    ]

    print(f"[*] Updating MySQL credentials to: {'*' * len(new_password)}")
    
    for env_file in env_targets:
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace DB_PASSWORD= line
            new_content = re.sub(r'DB_PASSWORD=.*', f'DB_PASSWORD={new_password}', content)
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"    [+] Updated: {os.path.relpath(env_file, project_root)}")
        else:
            print(f"    [!] Missing: {os.path.relpath(env_file, project_root)}")

if __name__ == "__main__":
    update_env_files()
