"""Print missed labels to file instead of console."""
import re
from pathlib import Path

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
html = html_path.read_bytes().decode("utf-8")

MARKER_RE = re.compile(r"اجبارى|اختيارى")
LABEL_ELEM_RE = re.compile(
    r'<label(?![^>]*class=["\'][^"\']*(?:reg-btn|photo-upload-btn)[^"\']*["\'])[^>]*>(.*?)</label>',
    re.DOTALL | re.IGNORECASE
)
QUIZ_SKIP = [
    "تم تسليمك دليلاً","When explaining a concept","aha! moment",
    "A website performs poorly","In a strategy game","write a book",
    "sounds most like a compliment","Deep work","finishing a project",
]

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()

misses = []
for m in LABEL_ELEM_RE.finditer(html):
    inner = m.group(1)
    txt = strip_tags(inner)
    if not txt or len(txt) < 3: continue
    if MARKER_RE.search(txt): continue
    if re.search(r'<input[^>]*type=["\'](?:file|submit|button|image|reset)["\']', inner, re.IGNORECASE): continue
    skip = any(s in txt for s in QUIZ_SKIP)
    if skip: continue
    misses.append(txt[:90])

out = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\backend\scratch\missed_labels.txt")
out.write_text("\n".join(f"• {m}" for m in misses), encoding="utf-8")
print(f"Missed: {len(misses)} — see missed_labels.txt")
