from pathlib import Path

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
content = html_path.read_bytes().decode("utf-8")

# The broken section starts at `  @keyframes slideDown {\r\r\n</div>\r\r\n`
# and is followed immediately by the reg-back-btn anchor.
# We need to replace this broken fragment with the correct closed CSS + HTML structure.

broken = (
    "  @keyframes slideDown {\r\r\n"
    "</div>\r\r\n"
    "<a class=\"reg-back-btn\" href=\"index.html\">\r\r\n"
    "<span class=\"reg-back-btn__icon\">\u2190</span>\r\r\n"
    "<span>\u0627\u0644\u0639\u0648\u062f\u0629 \u0644\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644</span>\r\r\n"
    "</a>\r\r\n"
)

fixed = (
    "  @keyframes slideDown {\r\r\n"
    "    from { opacity: 0; transform: translateY(-10px); }\r\r\n"
    "    to   { opacity: 1; transform: translateY(0);      }\r\r\n"
    "  }\r\r\n"
    "  .emp-work-nature-wrap {\r\r\n"
    "    transition: opacity 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;\r\r\n"
    "    will-change: opacity, transform;\r\r\n"
    "  }\r\r\n"
    "  .emp-work-nature-wrap.is-updating { opacity: 0.72; transform: translateY(-2px); }\r\r\n"
    "  .registration-page .emp-work-nature-wrap select {\r\r\n"
    "    transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;\r\r\n"
    "  }\r\r\n"
    "</style>\r\r\n"
    "</head>\r\r\n"
    "<body class=\"registration-page\">\r\r\n"
    "<div class=\"reg-bg\"></div>\r\r\n"
    "<div class=\"reg-logo\">\r\r\n"
    "<img alt=\"\" class=\"reg-header__logo-img reg-logo__img\" src=\"images/logo2.png\"/>\r\r\n"
    "</div>\r\r\n"
    "<a class=\"reg-back-btn\" href=\"index.html\">\r\r\n"
    "<span class=\"reg-back-btn__icon\">\u2190</span>\r\r\n"
    "<span>\u0627\u0644\u0639\u0648\u062f\u0629 \u0644\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644</span>\r\r\n"
    "</a>\r\r\n"
)

if broken in content:
    content = content.replace(broken, fixed, 1)
    html_path.write_bytes(content.encode("utf-8"))
    print("SUCCESS: HTML structure repaired.")
else:
    # Try to find the actual bytes around line 56
    lines = content.split("\r\r\n")
    for i, l in enumerate(lines[53:60], start=54):
        print(f"Line {i}: {repr(l[:80])}")
    print("FAILED: broken fragment not found. See lines above.")
