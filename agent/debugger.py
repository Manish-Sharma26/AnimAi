from agent.llm import call_llm
from agent.coder import extract_code

DEBUGGER_PROMPT = """You are a Manim debugging expert.
This Manim Python code failed to compile with the error below.

BROKEN CODE:
{code}

ERROR MESSAGE:
{error}

Analyze the error carefully and fix the code.
Common Manim mistakes to check:
- Wrong class or method names
- Incorrect animation syntax
- Wrong use of VGroup or positioning
- Missing self. prefix
- Wrong coordinate usage

Return the complete fixed Python code only.
```python"""


def debug_manim_code(code: str, error: str) -> str:
    """
    Takes broken code + error message.
    Asks Groq to fix it.
    Returns corrected code.
    """
    print(f"[Debugger] Analyzing error: {error[:100]}...")

    prompt = DEBUGGER_PROMPT.format(code=code, error=error)
    response = call_llm(prompt, max_tokens=3000)
    fixed_code = extract_code(response)

    print(f"[Debugger] Fixed code generated ({len(fixed_code.splitlines())} lines)")
    return fixed_code