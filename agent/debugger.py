from agent.llm import call_llm
from agent.coder import extract_code

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

Common fixes:
- Incomplete lines: `ELEMENT_SP` → `ELEMENT_SPACING = 0.5`
- Missing imports: add before class definition
- Unmatched brackets/parens: close them properly
- Undefined variables: check context and add missing definitions

Return ONLY the complete, syntactically valid Python code. No commentary.
"""


def debug_manim_code(code: str, error: str) -> str:
    """
    Takes broken code + error message.
    Asks Claude to fix it surgically (preserve logic, don't rewrite).
    Returns corrected code.
    """
    print(f"[Debugger] Analyzing error: {error[:100]}...")

    prompt = DEBUGGER_PROMPT.format(code=code, error=error)
    response = call_llm(prompt, max_tokens=6000)
    fixed_code = extract_code(response)

    print(f"[Debugger] Fixed code generated ({len(fixed_code.splitlines())} lines)")
    
    # Sanity check: fixed code should not be drastically shorter (surgical fix, not rewrite)
    if len(fixed_code.strip()) < len(code.strip()) * 0.4:
        print(f"[Debugger] ⚠️  WARNING: Fixed code is much shorter than original.")
        print(f"[Debugger] Original: {len(code.splitlines())} lines, Fixed: {len(fixed_code.splitlines())} lines")
        print(f"[Debugger] Debugger may have over-simplified or lost animation logic.")
    
    return fixed_code