from pathlib import Path
import re

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
content = html_path.read_text(encoding="utf-8")

# Find all labels
labels = re.findall(r"<label[^>]*>(.*?)</label>", content, re.DOTALL)
print(f"Total labels found: {len(labels)}")

unlabeled = []
for label in labels:
    clean = label.strip()
    if not clean:
        continue
    # Check if they have the words
    if "اجبارى" not in clean and "اختيارى" not in clean and "إجباري" not in clean and "اختياري" not in clean:
        # Ignore checkbox wrap labels if they don't contain inputs
        if "<input" not in clean:
            unlabeled.append(clean)

print("UNLABELED LABES:")
for idx, label in enumerate(unlabeled):
    # Print index and a safe representation of label text (only printable ASCII or hex/repr to avoid encoding errors)
    ascii_safe = label.encode("ascii", errors="replace").decode("ascii")
    print(f"{idx}: {ascii_safe}")
