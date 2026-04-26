"""Unit tests: test ONLY regex patterns without importing heavy modules."""
import re

# ── Test 1: SurroundingRoundedRectangle plain string replace ──
code1 = """
r = SurroundingRoundedRectangle(obj, color=YELLOW)
r2 = SurroundingRoundedRectangle(box, corner_radius=0.1)
"""
fixed1 = code1.replace('SurroundingRoundedRectangle', 'SurroundingRectangle')
assert 'SurroundingRoundedRectangle' not in fixed1
assert fixed1.count('SurroundingRectangle') == 2
print('PASS: plain str.replace() fixes SurroundingRoundedRectangle')

# Also test with regex word boundary (the existing approach)
fixed1b = re.sub(r'\bSurroundingRoundedRectangle\b', 'SurroundingRectangle', code1)
assert 'SurroundingRoundedRectangle' not in fixed1b
print('PASS: regex \\b also fixes SurroundingRoundedRectangle')

# ── Test 2: _strip_prosody_kwargs logic ──
PROSODY_RE = re.compile(r',\s*prosody\s*=\s*\{\{[^}]*\}\}|,\s*prosody\s*=\s*\{[^}]*\}')

code2 = """with self.voiceover(text='Hello world', prosody={'rate': '-15%'}) as tracker:
    pass
with self.voiceover(text='Bye', prosody={'rate': '-20%', 'volume': '+5%'}) as t:
    pass
"""
fixed2 = PROSODY_RE.sub('', code2)
assert 'prosody' not in fixed2, f'FAIL: {fixed2}'
print('PASS: prosody single-brace dict stripped correctly')

code3 = """with self.voiceover(text='Hello', prosody={{'rate': '-15%'}}) as t:
    pass
"""
fixed3 = PROSODY_RE.sub('', code3)
assert 'prosody' not in fixed3, f'FAIL: {fixed3}'
print('PASS: prosody double-brace dict stripped correctly')

# ── Test 3: Azure fallback regex ──
provider_re = re.compile(r'if provider == ["\']azure["\']:')
code4 = """
if provider == 'azure':
    self.set_speech_service(AzureService(voice='en-US'))
"""
patched4 = provider_re.sub('if False:  # [PATCHED: forced gTTS fallback]', code4)
assert 'if False:' in patched4
assert "if provider == 'azure':" not in patched4
print('PASS: Azure provider branch disabled by _force_gtts_fallback regex')

# ── Test 4: WS_ERROR_UNDERLYING_IO_ERROR classification ──
def _classify_failure(error_text):
    text = (error_text or '').lower()
    if (
        'speech synthesis failed' in text
        or 'cancellationreason.error' in text
        or 'ws_open_error' in text
        or 'ws_error_underlying_io_error' in text
        or 'underlying_io_error' in text
        or ('dns' in text and 'resolution failed' in text)
        or ('connection failed' in text and 'tts' in text)
        or ('websocket' in text and 'error' in text and 'tts' in text)
    ):
        return 'tts_synthesis_failed'
    if 'unexpected keyword argument' in text and "'prosody'" in text:
        return 'gtts_prosody_error'
    return 'other'

err1 = "WS_ERROR_UNDERLYING_IO_ERROR USP state: ReceivingData"
assert _classify_failure(err1) == 'tts_synthesis_failed', f'FAIL: {_classify_failure(err1)}'
print('PASS: WS_ERROR_UNDERLYING_IO_ERROR classified as tts_synthesis_failed')

err2 = "Exception: Speech synthesis failed"
assert _classify_failure(err2) == 'tts_synthesis_failed'
print('PASS: Speech synthesis failed classified as tts_synthesis_failed')

err3 = "TypeError: gTTS.__init__() got an unexpected keyword argument 'prosody'"
assert _classify_failure(err3) == 'gtts_prosody_error', f'FAIL: {_classify_failure(err3)}'
print('PASS: prosody TypeError classified as gtts_prosody_error')

print()
print('All tests PASSED!')
