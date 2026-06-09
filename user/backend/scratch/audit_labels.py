"""
Audit registration.html for:
1. File upload inputs missing instructions
2. Labels missing (اجبارى) / (اختيارى) markers
Uses stdlib only (no bs4).
"""
import re
from pathlib import Path

html = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html").read_text(encoding="utf-8")

# Split by step
step_blocks = re.split(r'(<div[^>]*data-step="(\d+)"[^>]*>)', html)

# Rebuild as list of (step_num, block_html)
steps = []
i = 0
while i < len(step_blocks):
    m = re.match(r'<div[^>]*data-step="(\d+)"', step_blocks[i] if i < len(step_blocks) else "")
    if m:
        step_num = int(step_blocks[i+1]) if (i+1) < len(step_blocks) else "?"
        block = step_blocks[i] + (step_blocks[i+2] if (i+2) < len(step_blocks) else "")
        steps.append((step_blocks[i+1], block))
        i += 3
    else:
        i += 1

# Re-split cleanly
step_pattern = re.compile(r'<div[^>]*class="reg-step[^"]*"[^>]*data-step="(\d+)"[^>]*>(.*?)(?=<div[^>]*class="reg-step|$)', re.DOTALL)
steps = [(m.group(1), m.group(2)) for m in step_pattern.finditer(html)]

output = []
MARKER_RE = re.compile(r"اجبارى|اختيارى")
LABEL_RE  = re.compile(r"<label(?![^>]*class=['\"]reg-btn)[^>]*>(.*?)</label>", re.DOTALL | re.IGNORECASE)
FILE_INPUT_RE = re.compile(r'<input[^>]*type=["\']file["\'][^>]*>', re.IGNORECASE)
NAME_RE   = re.compile(r'name=["\']([^"\']+)["\']')
ACCEPT_RE = re.compile(r'accept=["\']([^"\']+)["\']')
STRIP_TAGS = re.compile(r'<[^>]+>')

def strip(s):
    return STRIP_TAGS.sub("", s).strip()

# ── 1. File upload instruction audit ─────────────────────────────────────────
output.append("=" * 80)
output.append("FILE UPLOAD AUDIT — inputs missing format/instruction hints")
output.append("=" * 80)

for snum, shtml in steps:
    file_inputs = FILE_INPUT_RE.findall(shtml)
    for fi in file_inputs:
        name = NAME_RE.search(fi)
        name = name.group(1) if name else "(no name)"
        accept = ACCEPT_RE.search(fi)
        accept_val = accept.group(1) if accept else ""
        # Look for <small> or <p class=...desc...> within ~600 chars after the input
        pos = shtml.find(fi)
        after = shtml[pos:pos+600]
        has_small  = bool(re.search(r'<small[^>]*>([^<]{5,})<', after))
        has_desc_p = bool(re.search(r'<p[^>]*desc[^>]*>([^<]{5,})<', after))
        has_accept = bool(accept_val)
        ok = has_small or has_desc_p or has_accept
        if not ok:
            output.append(f"  Step {snum} | {name:<40} ← NO instructions/accept hint")

output.append("")
output.append("=" * 80)
output.append("LABEL MARKER AUDIT — labels missing (اجبارى) or (اختيارى)")
output.append("=" * 80)

for snum, shtml in steps:
    labels = LABEL_RE.findall(shtml)
    missing = []
    for inner in labels:
        txt = strip(inner)
        if not txt or len(txt) < 3:
            continue
        # Skip file-button labels (they are styled buttons, not field labels)
        if "photo-upload-btn" in inner or "reg-btn" in inner:
            continue
        # Skip checkbox/radio wrappers with very short text
        if re.search(r'<input[^>]*type=["\'](?:checkbox|radio|file|submit|button)["\']', inner):
            continue
        if not MARKER_RE.search(txt):
            missing.append(txt[:80])
    if missing:
        output.append(f"\nStep {snum} — {len(missing)} label(s) missing marker:")
        for m in missing:
            output.append(f"    • {m}")

out_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\backend\scratch\audit_report.txt")
out_path.write_text("\n".join(output), encoding="utf-8")
print(f"Done — {len(output)} lines — {out_path}")
