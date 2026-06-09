import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def load_robust_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        pos = 0
        combined = []
        while pos < len(content):
            while pos < len(content) and content[pos].isspace():
                pos += 1
            if pos >= len(content):
                break
            try:
                obj, next_pos = decoder.raw_decode(content, pos)
                if isinstance(obj, list):
                    combined.extend(obj)
                else:
                    combined.append(obj)
                pos = next_pos
            except Exception as e:
                cleaned = content.replace("]\n[", ",").replace("]\r\n[", ",")
                return json.loads(cleaned)
        return combined

data = load_robust_json('Egypt V2.json')
print(f"Total universities: {len(data)}")
for i, u in enumerate(data):
    print(f"{i+1}: {u.get('name')}")
