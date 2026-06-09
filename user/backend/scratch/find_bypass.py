from pathlib import Path

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
content = html_path.read_text(encoding="utf-8")

for idx, line in enumerate(content.splitlines()):
    if "devBypass" in line or "bypass" in line:
        print(f"Line {idx+1}: {line.strip()}")
