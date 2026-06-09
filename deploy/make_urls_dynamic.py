import os
import glob
import re

def make_urls_dynamic():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # We will search both user and admin portals for html and js files
    search_dirs = [
        os.path.join(project_root, 'admin'),
        os.path.join(project_root, 'user')
    ]
    
    # Regex to find hardcoded localhost URLs
    # This will match 'http://localhost:8001', 'http://127.0.0.1:8001', 'http://localhost:8002', etc.
    # and replace them with an empty string, seamlessly converting them to dynamic relative URLs!
    pattern = re.compile(r'https?://(?:localhost|127\.0\.0\.1):\d+')
    
    modified_count = 0
    file_count = 0
    
    for directory in search_dirs:
        for root, dirs, files in os.walk(directory):
            # Skip backend / venv folders to avoid touching libraries or compiled files
            if 'backend' in dirs:
                dirs.remove('backend')
            if 'venv' in dirs:
                dirs.remove('venv')
            if 'node_modules' in dirs:
                dirs.remove('node_modules')
                
            for file in files:
                if file.endswith('.html') or file.endswith('.js'):
                    file_path = os.path.join(root, file)
                    file_count += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Apply regex substitution
                        new_content, num_subs = pattern.subn('', content)
                        
                        if num_subs > 0:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            modified_count += 1
                            print(f"    [+] Made URLs dynamic in: {os.path.relpath(file_path, project_root)}")
                    except Exception as e:
                        print(f"    [!] Failed to process {file_path}: {e}")

    print(f"[*] Checked {file_count} frontend files. Updated {modified_count} files to use dynamic paths.")

if __name__ == "__main__":
    print("[*] Automatically converting any hardcoded localhost URLs to dynamic relative paths...")
    make_urls_dynamic()
