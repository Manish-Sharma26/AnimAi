"""Unit tests for the three failure fixes."""
import sys
sys.path.insert(0, '.')
from agent.coder import _strip_prosody_kwargs, _apply_preventive_fixes
from agent.orchestrator import _force_gtts_fallback, _classify_failure

# Test 1: SurroundingRoundedRectangle fix via _apply_preventive_fixes
test_code = """
from manim import *
def test():
    r = SurroundingRoundedRectangle(obj, color=YELLOW)
    r2 = SurroundingRoundedRectangle(box, corner_radius=0.1)
"""
fixed = _apply_preventive_fixes(test_code)
assert 'SurroundingRoundedRectangle' not in fixed, 'FAIL: SurroundingRoundedRectangle still in code'
assert 'SurroundingRectangle' in fixed, 'FAIL: SurroundingRectangle not in code'
print('PASS: SurroundingRoundedRectangle fixed by _apply_preventive_fixes')

# Test 2: _strip_prosody_kwargs — single-brace dict
test_voiceover = """
with self.voiceover(text='Hello world', prosody={'rate': '-15%'}) as tracker:
    pass
"""
stripped = _strip_prosody_kwargs(test_voiceover)
assert 'prosody' not in stripped, f'FAIL: prosody still in code after strip: {stripped}'
print('PASS: _strip_prosody_kwargs strips single-brace prosody dict')

# Test 3: _strip_prosody_kwargs — double-brace dict (from f-string templates)
test_voiceover2 = """
with self.voiceover(text='Hello', prosody={{'rate': '-20%'}}) as t:
    pass
"""
stripped2 = _strip_prosody_kwargs(test_voiceover2)
assert 'prosody' not in stripped2, f'FAIL: prosody still in code after strip: {stripped2}'
print('PASS: _strip_prosody_kwargs strips double-brace prosody dict')

# Test 4: _force_gtts_fallback disables Azure AND strips prosody
test_code2 = """
if provider == 'azure':
    self.set_speech_service(AzureService(voice='en-US'))
with self.voiceover(text='Hello', prosody={'rate': '-15%'}) as t:
    pass
"""
patched = _force_gtts_fallback(test_code2)
assert 'if False:' in patched, 'FAIL: azure branch not disabled by _force_gtts_fallback'
assert 'prosody' not in patched, f'FAIL: prosody still in patched code: {patched}'
print('PASS: _force_gtts_fallback disables Azure AND strips prosody')

# Test 5: _classify_failure detects WS_ERROR_UNDERLYING_IO_ERROR
err5 = "WS_ERROR_UNDERLYING_IO_ERROR USP state: ReceivingData. Received audio size: 103680"
assert _classify_failure(err5) == 'tts_synthesis_failed', f'FAIL: got {_classify_failure(err5)}'
print('PASS: _classify_failure detects WS_ERROR_UNDERLYING_IO_ERROR as tts_synthesis_failed')

# Test 6: _classify_failure detects gTTS prosody TypeError
err6 = "TypeError: gTTS.__init__() got an unexpected keyword argument 'prosody'"
assert _classify_failure(err6) == 'gtts_prosody_error', f'FAIL: got {_classify_failure(err6)}'
print('PASS: _classify_failure detects prosody TypeError as gtts_prosody_error')

print()
print('All tests PASSED!')
