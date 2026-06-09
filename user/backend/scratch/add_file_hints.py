"""
Insert file upload hints for the 5 missing inputs.
Uses position-based insertion after each matching input tag.
"""
import re
from pathlib import Path

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
html = html_path.read_bytes().decode("utf-8")

INSTRUCTIONS = {
    "graduationCertificateScan": "📎 الصيغ المقبولة: PDF، JPG، PNG — الحجم الأقصى: 5 ميجابايت — شهادة التخرج أو كشف الدرجات.",
    "employmentSectionCv":       "📎 الصيغ المقبولة: PDF، DOC، DOCX — الحجم الأقصى: 5 ميجابايت — السيرة الذاتية الكاملة المحدّثة.",
    "prizeCertificate":          "📎 الصيغ المقبولة: PDF، JPG، PNG — الحجم الأقصى: 3 ميجابايت — صورة أو وثيقة الجائزة/التكريم.",
    "sectionSevenCriminalRecordCertificate": "📎 الصيغ المقبولة: PDF، JPG، PNG — الحجم الأقصى: 5 ميجابايت — شهادة السجل الجنائي المعتمدة.",
    "photoFront":                "📸 صيغ الصور: JPG أو PNG — الحجم الأقصى: 2 ميجابايت — صورة شخصية واضحة من الأمام بخلفية بيضاء.",
}
HINT_CLASS = "file-upload-hint"

FILE_ANY_RE = re.compile(r'(<input[^>]*type=["\']file["\'][^>]*/>)', re.IGNORECASE | re.DOTALL)
NAME_RE     = re.compile(r'name=["\']([^"\']+)["\']', re.IGNORECASE)
SMALL_RE    = re.compile(r'<small', re.IGNORECASE)

inserted = 0
parts = []
prev = 0

for m in FILE_ANY_RE.finditer(html):
    tag = m.group(1)
    name_m = NAME_RE.search(tag)
    if not name_m:
        continue
    name = name_m.group(1).rstrip("[]")
    if name not in INSTRUCTIONS:
        continue
    # Check next 400 chars for existing <small>
    ahead = html[m.end():m.end()+400]
    if SMALL_RE.search(ahead):
        continue
    hint = f'<small class="{HINT_CLASS}">{INSTRUCTIONS[name]}</small>\n'
    parts.append(html[prev:m.end()])
    parts.append(hint)
    prev = m.end()
    inserted += 1

parts.append(html[prev:])
new_html = "".join(parts)
html_path.write_bytes(new_html.encode("utf-8"))
print(f"Inserted {inserted} file upload hints.")
