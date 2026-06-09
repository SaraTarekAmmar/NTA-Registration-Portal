from pathlib import Path

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
content = html_path.read_text(encoding="utf-8").splitlines()

output = []
for idx, line in enumerate(content):
    if "devBypassWidget" in line:
        start = max(0, idx - 10)
        end = min(len(content), idx + 20)
        for i in range(start, end):
            output.append(f"Line {i+1}: {content[i]}")

Path("scratch/bypass_snippet.txt").write_text("\n".join(output), encoding="utf-8")
print("Done")
