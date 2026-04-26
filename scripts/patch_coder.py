"""Patch coder.py to add belt-and-suspenders SurroundingRoundedRectangle fix."""
import re

with open('agent/coder.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the wait_until_bookmark line and insert the fix right after it
# The file uses CRLF line endings
marker = r"    fixed = re.sub(r'\bself\.wait_until_bookmark\s*\([^)]*\)\s*\n?', '', fixed)"
if marker not in content:
    # Try with r\n (CRLF stored as two chars)
    print("Marker not found, searching...")
    idx = content.find('wait_until_bookmark')
    print(repr(content[idx-5:idx+150]))
    exit(1)

insert_after = marker
addition = (
    "\r\n"
    "\r\n"
    "    # \u2500\u2500 BELT-AND-SUSPENDERS: plain string replacement for SurroundingRoundedRectangle \u2500\u2500\r\n"
    "    # The _PREVENTIVE_SUBSTITUTIONS regex uses \\b word boundaries which should always fire,\r\n"
    "    # but as a safety net we also do a plain string replace so no edge-case can slip through.\r\n"
    "    fixed = fixed.replace('SurroundingRoundedRectangle', 'SurroundingRectangle')"
)

new_content = content.replace(insert_after, insert_after + addition, 1)
if new_content == content:
    print("ERROR: replacement had no effect")
    exit(1)

with open('agent/coder.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("OK: SurroundingRoundedRectangle belt-and-suspenders fix inserted into coder.py")
print(f"File size: {len(new_content)} bytes")
