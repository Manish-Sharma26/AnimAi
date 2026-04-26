"""Patch coder.py: add prosody kwarg stripping in _apply_preventive_fixes when gTTS is active."""

with open('agent/coder.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the unique anchor
anchor = "    return fixed\n\n\ndef _stitch_continuation"
if anchor not in content:
    # Try CRLF variant
    anchor = "    return fixed\r\n\r\n\r\ndef _stitch_continuation"
    if anchor not in content:
        print("ERROR: anchor not found")
        idx = content.find('_stitch_continuation')
        print(repr(content[max(0,idx-300):idx+10]))
        exit(1)
    lf_type = '\r\n'
else:
    lf_type = '\n'

# Build replacement: insert prosody stripping before 'return fixed'
prosody_block = (
    f"\n    # \u2500\u2500 Strip prosody= kwarg when active provider is gTTS \u2500\u2500{lf_type}"
    f"    # GTTSService does NOT support prosody=; calling self.voiceover(prosody={{...}}) with{lf_type}"
    f"    # gTTS raises: TypeError: gTTS.__init__() got an unexpected keyword argument 'prosody'.{lf_type}"
    f"    # Strip prosody from generated code whenever gTTS is the *primary* provider so the{lf_type}"
    f"    # code is always safe. When Azure is primary, prosody stays (Azure supports it).{lf_type}"
    f"    # The orchestrator's _force_gtts_fallback() also strips prosody on Azure failures.{lf_type}"
    f"    _active_provider = os.getenv('TTS_PROVIDER', 'azure').strip().lower(){lf_type}"
    f"    if _active_provider != 'azure':{lf_type}"
    f"        fixed = _strip_prosody_kwargs(fixed){lf_type}"
)

old = "    return fixed" + lf_type + lf_type + lf_type + "def _stitch_continuation"
new = prosody_block + "    return fixed" + lf_type + lf_type + lf_type + "def _stitch_continuation"

if old not in content:
    print(f"ERROR: old replacement target not found (lf_type={repr(lf_type)})")
    idx = content.find('def _stitch_continuation')
    print(repr(content[max(0,idx-200):idx+10]))
    exit(1)

new_content = content.replace(old, new, 1)
if new_content == content:
    print("ERROR: replacement had no effect")
    exit(1)

with open('agent/coder.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"OK: prosody kwarg stripping added to _apply_preventive_fixes (lf_type={repr(lf_type)})")
print(f"File size: {len(new_content)} bytes")
