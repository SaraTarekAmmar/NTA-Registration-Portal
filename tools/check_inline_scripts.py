import argparse
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path


class InlineScriptParser(HTMLParser):
    def __init__(self, source_path):
        super().__init__(convert_charrefs=False)
        self.source_path = source_path
        self.scripts = []
        self._current = None
        self._line = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "script":
            return
        attr_map = {name.lower(): value for name, value in attrs}
        if attr_map.get("src"):
            return
        script_type = (attr_map.get("type") or "text/javascript").lower()
        if script_type not in ("text/javascript", "application/javascript", "module", ""):
            return
        self._current = []
        self._line = self.getpos()[0]

    def handle_data(self, data):
        if self._current is not None:
            self._current.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "script" or self._current is None:
            return
        self.scripts.append((self._line, "".join(self._current)))
        self._current = None
        self._line = None


def iter_html_files(root):
    ignored = {".git", "venv", ".venv", "__pycache__", "node_modules"}
    for path in root.rglob("*.html"):
        if any(part in ignored for part in path.parts):
            continue
        yield path


def check_script(node_bin, source_path, line_number, source):
    if not source.strip():
        return True, ""
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as tmp:
        tmp.write(source)
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run([node_bin, "--check", str(tmp_path)], text=True, capture_output=True)
        if result.returncode == 0:
            return True, ""
        label = f"{source_path}:{line_number}"
        return False, f"\n{label}\n{result.stderr or result.stdout}"
    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Syntax-check inline HTML <script> blocks with node --check.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--node", default="node")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    failures = []
    checked = 0

    for html_path in iter_html_files(root):
        parser = InlineScriptParser(html_path.relative_to(root))
        parser.feed(html_path.read_text(encoding="utf-8-sig", errors="replace"))
        for line_number, source in parser.scripts:
            checked += 1
            ok, message = check_script(args.node, html_path.relative_to(root), line_number, source)
            if not ok:
                failures.append(message)

    if failures:
        print("Inline script syntax check failed:", file=sys.stderr)
        print("".join(failures), file=sys.stderr)
        return 1

    print(f"Checked {checked} inline script block(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
