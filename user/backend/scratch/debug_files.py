import re
from pathlib import Path

html = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html").read_bytes().decode("utf-8")

# Find all file inputs regardless of attribute order
FILE_ANY_RE = re.compile(r'<input[^>]*type=["\']file["\'][^>]*/?>',  re.IGNORECASE)
for m in FILE_ANY_RE.finditer(html):
    name_m = re.search(r'name=["\']([^"\']+)["\']', m.group())
    nm = name_m.group(1) if name_m else "(no name)"
    # check for small within 400 chars after
    after = html[m.end():m.end()+400]
    has_small = bool(re.search(r'<small', after, re.I))
    flag = "HAS_HINT" if has_small else "MISSING_HINT"
    print(f"{flag} | {nm}")
