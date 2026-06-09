from pathlib import Path

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
content = html_path.read_bytes().decode("utf-8")

hint_css = (
    "  /* File upload instruction hints */\r\r\n"
    "  .file-upload-hint {\r\r\n"
    "    display: block;\r\r\n"
    "    margin-top: 6px;\r\r\n"
    "    font-size: 12px;\r\r\n"
    "    color: #64748b;\r\r\n"
    "    line-height: 1.5;\r\r\n"
    "    direction: rtl;\r\r\n"
    "  }\r\r\n"
    "  body.dark-mode .file-upload-hint { color: #94a3b8; }\r\r\n"
)

# Insert before </style>
close_style = "</style>"
idx = content.find(close_style)
if idx == -1:
    print("ERROR: </style> not found")
else:
    content = content[:idx] + hint_css + content[idx:]
    html_path.write_bytes(content.encode("utf-8"))
    print("CSS inserted successfully before </style>")
