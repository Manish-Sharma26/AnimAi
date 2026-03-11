# debug.py
import re

with open("test_scene.py", "r") as f:
    code = f.read()

print("Raw code:")
print(code)
print()

# Test extraction
lines = []
for line in code.split("\n"):
    match = re.search(r'#\s*VOICEOVER:\s*(.+)', line)
    if match:
        lines.append(match.group(1).strip())

print(f"Found {len(lines)} voiceover lines:")
for l in lines:
    print(f"  - {l}")