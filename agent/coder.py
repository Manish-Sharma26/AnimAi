import re
import json
import os
from agent.llm import call_llm

CODER_MODEL = os.getenv("GEMINI_CODER_MODEL", "gemini-2.5-pro")
MAX_GENERATION_ATTEMPTS = 3


def _build_coder_plan_payload(plan: dict) -> dict:
    """Keep only essential planner fields to reduce prompt size and truncation risk."""
    safe = plan or {}
    keys = [
        "title",
        "visual_style",
        "opening_scene",
        "steps",
        "voiceovers",
        "closing_scene",
        "summary",
        "duration_seconds",
    ]
    compact = {k: safe.get(k) for k in keys if k in safe}

    # Cap step/voiceover lengths to avoid massive prompts from over-verbose plans.
    steps = [str(s)[:220] for s in (compact.get("steps") or [])]
    voiceovers = [str(v)[:220] for v in (compact.get("voiceovers") or [])]
    compact["steps"] = steps[:8]
    compact["voiceovers"] = voiceovers[:8]
    return compact

CODER_PROMPT = """You are an expert Manim animator creating professional educational animations for AnimAI Studio.

STRICT CODE RULES:
1. Always use `from manim import *`
2. Also import `VoiceoverScene` and `GTTSService`:
    - `from manim_voiceover import VoiceoverScene`
    - `from manim_voiceover.services.gtts import GTTSService`
3. Class must extend `VoiceoverScene` and be named `GeneratedScene`
4. In `construct()`, call `self.set_speech_service(GTTSService(lang=\"en\"))` before any narration
5. Add # VOICEOVER: comment and matching `with self.voiceover(text=...)` block before every meaningful animation block
6. Always set: self.camera.background_color = "#0F0F1A"

DESIGN RULES — ALWAYS FOLLOW:
- Background: "#0F0F1A" (dark navy)
- Primary color: "#4FACFE" (cyan blue)
- Highlight: "#F9CA24" (golden yellow)
- Success: "#6AB04C" (green)
- Fail: "#EB4D4B" (red)
- Use RoundedRectangle for boxes, Circle for nodes
- Use LaggedStart for staggered entrance animations
- Use smooth run_time=0.6 transitions
- Always add title with underline at top
- Always end with a result banner

VOICEOVER QUALITY RULES:
- Never write generic lines like "Introduction", "Now we continue", "Visiting node".
- Each voiceover must explain why the visual matters, not just describe motion.
- Tie narration to concrete on-screen details (values, labels, relationships, comparisons).
- Keep each voiceover as a natural teaching line (about 12-28 words).
- Voiceover count should roughly match the number of key teaching moments.

ANIMATION QUALITY RULES:
- Build a clear learning arc: setup -> process -> key transition -> conclusion.
- Prefer topic-appropriate visual encoding (color, position, grouping, emphasis) over random motion.
- Use callouts/highlights to direct attention when a key idea changes.

ANIMATION PLAN (use this as the source of truth):
{plan_json}

PLAN USAGE RULES:
- Convert each entry in plan.voiceovers into a matching `# VOICEOVER:` comment and a matching `with self.voiceover(text=...)` block.
- Keep voiceover wording very close to plan.voiceovers unless a tiny edit improves grammar.
- Align each voiceover with the corresponding visual step in plan.steps.

Now generate a complete, stunning, professional Manim animation for:
{query}

Use only the animation plan above as your source of truth. Make it visually rich with colors, smooth animations, and clear educational value.
Add # VOICEOVER: comments and matching `with self.voiceover(...)` blocks at every step.
Return ONLY the Python code. No explanation.
"""


def _likely_truncated_tail(code: str) -> bool:
    stripped = (code or "").rstrip()
    if not stripped:
        return True
    bad_tails = ("=", "(", "[", "{", ",", ".", ":", "\\")
    if stripped.endswith(bad_tails):
        return True
    return False


def _validate_generated_code(code: str, expected_steps: int) -> str:
    """Return empty string when code looks complete, else a short validation error."""
    if not code.strip():
        return "empty output"

    if "class GeneratedScene(VoiceoverScene):" not in code:
        return "missing GeneratedScene class"

    if "def construct(self):" not in code:
        return "missing construct method"

    if "self.set_speech_service(GTTSService(lang=\"en\"))" not in code:
        return "missing GTTS speech service setup"

    if "with self.voiceover(" not in code:
        return "missing voiceover blocks"

    if _likely_truncated_tail(code):
        return "output appears truncated near the end"

    if expected_steps > 3 and len(code.splitlines()) < 45:
        return "output too short for requested step count"

    try:
        compile(code, "scene.py", "exec")
    except SyntaxError as e:
        return f"syntax error: {e.msg} at line {e.lineno}"

    return ""


def generate_manim_code(query: str, plan: dict = None) -> str:
    """
    Calls Gemini to generate Manim code from the planner output.
    Guards against truncation and enforces completeness.
    """
    print(f"[Coder] Generating code for: {query}")

    plan = plan or {}
    plan_payload = _build_coder_plan_payload(plan)
    plan_json = json.dumps(plan_payload, indent=2)

    prompt = CODER_PROMPT.format(
        query=query,
        plan_json=plan_json,
    )
    expected_steps = len(plan.get("steps", []))
    last_code = ""
    last_validation_error = ""

    # Use very high token limit to prevent truncation of complex animations.
    # Better to overshoot and retry than to return incomplete code.
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        prompt_for_attempt = prompt
        if attempt > 1:
            prompt_for_attempt += (
                "\n\nIMPORTANT RETRY INSTRUCTION:\n"
                "Previous output was incomplete or invalid. "
                "Return the FULL file from imports to the final wait call. "
                "Do not stop mid-line or mid-block.\n"
                f"Validation failure to fix: {last_validation_error}\n"
            )

        response = call_llm(
            prompt_for_attempt,
            max_tokens=8192,
            preferred_model=CODER_MODEL,
            disable_thinking=True,
        )

        code = extract_code(response)
        last_code = code

        validation_error = _validate_generated_code(code, expected_steps=expected_steps)
        if not validation_error:
            break

        last_validation_error = validation_error
        print(f"[Coder] ⚠️  Generation attempt {attempt} failed validation: {validation_error}")
    else:
        print("[Coder] ⚠️  Returning last generated code after retries; debugger may be required.")

    code = last_code
    
    # Guard: Check for incomplete lines that might cause NameError
    lines = code.split('\n')
    incomplete_indicators = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Check for incomplete variable declarations (bare identifier with no value)
        if stripped and not stripped.startswith('#') and '=' not in stripped:
            if stripped.isidentifier() and not any(c in stripped for c in '()[]{}'):
                incomplete_indicators.append(f"Line {i}: '{stripped}' looks incomplete")
    
    if incomplete_indicators:
        print(f"[Coder] ⚠️  WARNING: Code may have incomplete lines (will likely fail):")
        for ind in incomplete_indicators[:3]:
            print(f"  {ind}")
    
    # Guard: Check if code is suspiciously short (< 60 lines for a complex animation)
    code_lines = len(code.splitlines())
    if code_lines < 60 and len(plan.get("steps", [])) > 3:
        print(f"[Coder] ⚠️  WARNING: Code is very short ({code_lines} lines) for a {len(plan.get('steps', []))}-step animation.")
        print(f"[Coder] This may indicate truncation or over-simplification. Debugger will likely be needed.")
    
    print(f"[Coder] Generated {code_lines} lines of code")
    return code


def extract_code(text: str) -> str:
    """
    Extracts Python code from LLM response.
    Handles cases where model wraps in ```python blocks or not.
    """
    clean = (text or "").strip()

    # Try to find ```python ... ``` block
    match = re.search(r'```python\s*(.*?)```', clean, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try plain ``` block
    match = re.search(r'```\s*(.*?)```', clean, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Handle incomplete fences like "```python" with no closing fence.
    if clean.startswith("```"):
        lines = clean.splitlines()
        if lines:
            lines = lines[1:]
        clean = "\n".join(lines).strip()

    # Remove trailing unmatched closing fence if present.
    if clean.endswith("```"):
        clean = clean[:-3].rstrip()

    # If no code block found, return as is
    return clean