import os

from agent.llm import call_llm
from agent.coder import extract_code
from rag.retriever import retrieve as rag_retrieve

DEBUGGER_MODEL = os.getenv("GEMINI_DEBUGGER_MODEL", "gemini-2.5-flash")

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

SANDBOX CONSTRAINT RULES — CRITICAL:
14. The code runs inside Docker with ONLY scene.py mounted. NO external files (images, SVGs, assets) exist.
15. If the error involves a missing file (e.g., FileNotFoundError for .png, .svg, .jpg), REPLACE the ImageMobject/SVGMobject with programmatic Manim shapes (Rectangle, Circle, Triangle, Polygon, etc.).
16. NEVER add `import os` or any filesystem operations — they are not needed and will cause errors.
17. NEVER use `.to_center()` — it does not exist in Manim. Use `.move_to(ORIGIN)` instead.

Common code fixes:
- Incomplete lines: `ELEMENT_SP` → `ELEMENT_SPACING = 0.5`
- Missing imports: add before class definition
- Unmatched brackets/parens: close them properly
- Undefined variables: check context and add missing definitions
- `.center` used as property → change to `.get_center()`
- `.get_top` / `.get_bottom` used without `()` → add `()`
- `ImageMobject("file.png")` → replace with shapes (e.g., Rectangle + Circle)
- `import os` → remove entirely
- `.to_center()` → `.move_to(ORIGIN)`

RELEVANT MANIM API REFERENCE (use to verify correct API usage):
{manim_context}

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

    # Common: .to_center() does not exist in Manim, use .move_to(ORIGIN)
    if "has no attribute 'to_center'" in err:
        fixed = _re.sub(r'\.to_center\(\)', '.move_to(ORIGIN)', fixed)

    # Common: remove import os if it causes NameError
    if "name 'os' is not defined" in err:
        fixed = _re.sub(r'^\s*import\s+os\s*\n', '', fixed, flags=_re.MULTILINE)
        fixed = _re.sub(r'^\s*from\s+os\b[^\n]*\n', '', fixed, flags=_re.MULTILINE)

    # Common: undefined color constants — replace with hex equivalents
    _COLOR_MAP = {
        "BROWN": '"#8B4513"',
        "LIGHT_BROWN": '"#CD853F"',
        "DARK_BROWN": '"#5C3317"',
        "CYAN": '"#00FFFF"',
        "DARK_GREEN": '"#006400"',
        "LIGHT_GREEN": '"#90EE90"',
        "DARK_RED": '"#8B0000"',
        "LIGHT_BLUE": '"#ADD8E6"',
        "DARK_GREY": '"#555555"',
        "LIGHT_GREY": '"#AAAAAA"',
        "MAGENTA": '"#FF00FF"',
        "LIME": '"#00FF00"',
        "NAVY": '"#000080"',
        "OLIVE": '"#808000"',
        "BEIGE": '"#F5F5DC"',
        "TURQUOISE": '"#40E0D0"',
        "VIOLET": '"#EE82EE"',
        "INDIGO": '"#4B0082"',
        "CORAL": '"#FF7F50"',
        "SALMON": '"#FA8072"',
        "TAN": '"#D2B48C"',
        "KHAKI": '"#F0E68C"',
        "AQUA": '"#00FFFF"',
        "CRIMSON": '"#DC143C"',
        "IVORY": '"#FFFFF0"',
        "LAVENDER": '"#E6E6FA"',
        "SILVER": '"#C0C0C0"',
        "SKYBLUE": '"#87CEEB"',
    }
    if "is not defined" in err:
        for color_name, hex_val in _COLOR_MAP.items():
            if color_name.lower() in err:
                # Replace bare color name used as a constant with hex string
                fixed = _re.sub(r'\b' + color_name + r'\b', hex_val, fixed)

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

    # Retrieve relevant Manim docs to help the LLM fix the error correctly
    try:
        rag_query = f"manim {error[:200]}"
        manim_context = rag_retrieve(rag_query, k=2)
        if manim_context:
            print(f"[Debugger] RAG injected {len(manim_context)} chars of API context")
        else:
            manim_context = "(no RAG context available)"
    except Exception:
        manim_context = "(no RAG context available)"

    prompt = DEBUGGER_PROMPT.format(code=code, error=error, manim_context=manim_context)
    response = call_llm(
        prompt,
        max_tokens=16384,
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