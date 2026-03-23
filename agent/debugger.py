import os

from agent.llm import call_llm
from agent.coder import extract_code

DEBUGGER_MODEL = os.getenv("GEMINI_DEBUGGER_MODEL", "gemini-3.0-flash")

DEBUGGER_PROMPT = """You are an expert Manim debugger.
Your ONLY job: fix the specific compilation error with minimal changes.

BROKEN CODE:
{code}

ERROR:
{error}

⚠️  CRITICAL RULES:
1. PRESERVE all animation logic, visual elements, and scene structure.
2. Fix ONLY the line or block causing the error — do NOT rewrite the whole scene.
3. If the error is a truncated/incomplete line (like `ELEMENT_SP` with no value), complete it intelligently.
4. If lines are cut off mid-definition, infer the intent and complete them.
5. NEVER replace working code with placeholder animations like 'Hello World'.
6. Return the complete, fixed file from `from manim import *` to the end of `construct()`.
7. Ensure all parentheses, brackets, and string quotes are balanced.
8. The fixed code must pass `compile(code, 'scene.py', 'exec')` check.
9. If the code uses `VoiceoverScene` and `GTTSService`, preserve those imports and `self.set_speech_service(...)` setup.
10. For Manim positioning APIs, use callable getters like `get_center()`, `get_top()`, `get_bottom()` when passing points to `move_to`, `next_to`, or vector math.

LAYOUT AWARENESS RULES:
11. If the error involves objects going off-screen or clipping, add `.scale_to_fit_width(config.frame_width - 2)` or reduce `font_size` values.
12. If the error shows leftover elements or pile-up, add `self.play(FadeOut(*old_elements))` before the failing animation block.
13. Common layout fixes:
    - "off-screen" or "clipping" → add scale_to_fit_width/height after positioning
    - "overlap" → increase buff values in .arrange() calls to at least 0.3, or reduce font_size
    - elements piling up → add FadeOut of previous step's elements before the new step
    - content too wide → add `.scale_to_fit_width(config.frame_width - 2)` on the VGroup
    - content too tall → add `.scale_to_fit_height(config.frame_height - 1.5)` on the VGroup

Common code fixes:
- Incomplete lines: `ELEMENT_SP` → `ELEMENT_SPACING = 0.5`
- Missing imports: add before class definition
- Unmatched brackets/parens: close them properly
- Undefined variables: check context and add missing definitions
- `.center` used as property → change to `.get_center()`
- `.get_top` / `.get_bottom` used without `()` → add `()`

Return ONLY the complete, syntactically valid Python code. No commentary.
"""


def _apply_common_manim_runtime_fixes(code: str, error: str) -> str:
    """Apply deterministic fixes for frequent Manim runtime mistakes."""
    import re as _re
    fixed = code
    err = (error or "").lower()

    # Common LLM mistake: `obj.center` used as a point instead of `obj.get_center()`.
    if "unsupported operand type(s) for -: 'method' and 'float'" in err or "has no attribute 'center'" in err:
        fixed = _re.sub(r'\.center\b(?!\()', '.get_center()', fixed)

    # Common: using get_top/get_bottom as properties instead of methods
    if "'method'" in err:
        fixed = _re.sub(r'\.get_top\b(?!\()', '.get_top()', fixed)
        fixed = _re.sub(r'\.get_bottom\b(?!\()', '.get_bottom()', fixed)
        fixed = _re.sub(r'\.get_left\b(?!\()', '.get_left()', fixed)
        fixed = _re.sub(r'\.get_right\b(?!\()', '.get_right()', fixed)

    return fixed


def debug_manim_code(code: str, error: str) -> str:
    """
    Takes broken code + error message.
    Asks Claude to fix it surgically (preserve logic, don't rewrite).
    Returns corrected code.
    """
    print(f"[Debugger] Analyzing error: {error[:100]}...")

    deterministic_fix = _apply_common_manim_runtime_fixes(code, error)
    if deterministic_fix != code:
        print("[Debugger] Applied deterministic Manim runtime fix")
        return deterministic_fix

    prompt = DEBUGGER_PROMPT.format(code=code, error=error)
    response = call_llm(
        prompt,
        max_tokens=6000,
        preferred_model=DEBUGGER_MODEL,
        disable_thinking=True,
    )
    fixed_code = extract_code(response)

    print(f"[Debugger] Fixed code generated ({len(fixed_code.splitlines())} lines)")
    
    # Sanity check: fixed code should not be drastically shorter (surgical fix, not rewrite)
    if len(fixed_code.strip()) < len(code.strip()) * 0.4:
        print(f"[Debugger] ⚠️  WARNING: Fixed code is much shorter than original.")
        print(f"[Debugger] Original: {len(code.splitlines())} lines, Fixed: {len(fixed_code.splitlines())} lines")
        print(f"[Debugger] Debugger may have over-simplified or lost animation logic.")
    
    return fixed_code