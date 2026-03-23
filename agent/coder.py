import re
import json
import os
from agent.llm import call_llm_detailed

CODER_MODEL = os.getenv("GEMINI_CODER_MODEL", "gemini-3.0-flash")
MAX_GENERATION_ATTEMPTS = 3
MAX_CONTINUATION_ATTEMPTS = 2


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
- Use RoundedRectangle for boxes, Circle for nodes
- Use LaggedStart for staggered entrance animations
- Use smooth run_time=0.6 transitions
- Always add title with underline at top
- Always end with a result banner

COLOR RULES — CRITICAL FOR VISIBILITY:
- The background is very dark (#0F0F1A). Every color you choose MUST have strong contrast against it.
- NEVER use BLACK, DARK_BLUE, DARK_GRAY, "#000000", "#111111", or any very dark color for strokes or fills — they will be INVISIBLE.
- For text on dark backgrounds: use WHITE, "#E0E0E0", or any bright/light color.
- For text on colored fills: ensure text color has high contrast with the fill (dark text on light fills, light text on dark fills).
- For highlights and emphasis: use bright, saturated colors (yellows, cyans, greens, oranges) that stand out against the navy background.
- For box/rectangle fills: use colors with opacity (e.g., set_fill(color, opacity=0.8)) so they don't blend into the background.
- Pick a coherent palette of 3-5 colors. Use one for primary elements, one for highlights/emphasis, one for success states, one for error/warning states.
- Test mentally: "Would this color be clearly visible on a #0F0F1A background?" If not, pick a brighter one.

SCENE TRANSITION RULES — CRITICAL FOR PREVENTING ELEMENT PILE-UP:
- Before each new voiceover/step, FadeOut ALL mobjects from the previous step that are no longer needed.
- Track persistent elements (like a title bar) in a variable (e.g., `title_group`) and exclude them from cleanup.
- For step transitions, use: `self.play(*[FadeOut(mob) for mob in self.mobjects if mob != title_group])`
- For major phase changes (setup → process → result), clear the ENTIRE screen: `self.play(*[FadeOut(mob) for mob in self.mobjects])` and then re-add only what's needed.
- NEVER let elements from step N remain visible during step N+1 unless they are explicitly part of the continuing narrative.
- Use `self.wait(0.3)` between cleanup and new element introduction for visual breathing room.
- The animation plan's steps include "Remove: [...]" and "Keep: [...]" hints — follow them.

LAYOUT RULES — PREVENT OVERLAP AND CLIPPING:
- Manim's default frame is 14.2 units wide × 8 units tall. The SAFE ZONE for content is x=[-6.5, 6.5], y=[-3.5, 3.5].
- MANDATORY: Use `.arrange(direction, buff=0.3)` for any group of 2+ elements. NEVER use `buff` less than 0.25.
- MANDATORY: After building any VGroup with 3+ elements, call `.scale_to_fit_width(config.frame_width - 2)` to guarantee it fits.
- MANDATORY: After positioning all elements for a step, check total height: if the content group's height would exceed 6.5 units, scale it down with `.scale_to_fit_height(config.frame_height - 1.5)`.
- For text labels on shapes: use `font_size=22` or smaller. Never exceed `font_size=28` in scenes with more than 3 visual elements.
- Never stack more than 3 text lines vertically without reducing `font_size`.
- Use `.to_edge()` with `buff=0.5` for elements at screen edges to prevent clipping.
- For trees and graphs: use `scale()` on the entire group to fit within frame bounds after construction.
- Always leave vertical space between the title and main content (at least `buff=0.5`).
- If placing elements manually, verify they stay within x=[-6.5, 6.5] and y=[-3.5, 3.5].
- For arrays with >6 elements: split across 2 rows using `.arrange_in_grid(rows=2, buff=0.3)`.
- Use `.next_to()` for relative positioning instead of absolute coordinates whenever possible.

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
- Keep all key visuals fully inside frame; avoid clipped or half-visible structures.
- Avoid text/object overlap by spacing elements and scaling groups when needed.

GOLDEN CODE PATTERN (follow this structure for EVERY step):
```python
# --- Step N: [description from plan] ---
# Clean up elements from previous step
if 'step_n_minus_1_group' in dir() and step_n_minus_1_group is not None:
    self.play(FadeOut(step_n_minus_1_group))
    self.wait(0.3)

# Build new elements for this step
step_n_group = VGroup(...)
step_n_group.arrange(DOWN, buff=0.3)
# Scale to fit if needed
if step_n_group.width > config.frame_width - 2:
    step_n_group.scale_to_fit_width(config.frame_width - 2)
if step_n_group.height > config.frame_height - 1.5:
    step_n_group.scale_to_fit_height(config.frame_height - 1.5)
step_n_group.next_to(title_group, DOWN, buff=0.5)

# VOICEOVER: [narration text from plan]
with self.voiceover(text="..."):
    self.play(FadeIn(step_n_group))
    # ... step-specific animations ...
```

ANIMATION PLAN (use this as the source of truth):
{plan_json}

PLAN USAGE RULES:
- Convert each entry in plan.voiceovers into a matching `# VOICEOVER:` comment and a matching `with self.voiceover(text=...)` block.
- Keep voiceover wording very close to plan.voiceovers unless a tiny edit improves grammar.
- Align each voiceover with the corresponding visual step in plan.steps.
- Follow the "Remove:" and "Keep:" hints in each plan step for scene cleanup.

Now generate a complete, stunning, professional Manim animation for:
{query}

Use only the animation plan above as your source of truth. Make it visually rich with colors, smooth animations, and clear educational value.
Add # VOICEOVER: comments and matching `with self.voiceover(...)` blocks at every step.
Return ONLY the Python code. No explanation.
"""

REVISION_PROMPT = """You are an expert Manim code editor.
You are given existing working Manim code and user-requested changes.

TASK:
- Apply the requested changes to the existing code.
- Preserve all working parts unless they conflict with the requested changes.
- Keep class name `GeneratedScene` and `VoiceoverScene` usage.
- Keep `self.set_speech_service(GTTSService(lang=\"en\"))`.
- Keep or improve existing voiceover blocks.
- Return the FULL updated Python file from imports to end of `construct()`.

QUALITY RULES:
- Ensure no clipping/overlap where possible.
- For binary tree topics, ensure the full tree is visible on screen (not half-cut).
- Keep animations educational and readable.

SCENE TRANSITION RULES:
- Before each new step, FadeOut ALL elements from the previous step that are no longer needed.
- Track persistent elements (like title) in a variable and exclude from cleanup.
- NEVER let elements from step N remain visible during step N+1 unless they are part of the continuing narrative.

LAYOUT RULES:
- Safe zone: x=[-6.5, 6.5], y=[-3.5, 3.5]. Frame is 14.2 wide x 8 tall.
- Use .arrange(direction, buff=0.3) for groups. Never buff < 0.25.
- After building VGroups with 3+ elements, call .scale_to_fit_width(config.frame_width - 2).
- For text labels: font_size=22 or smaller in dense scenes.
- Use .next_to() for relative positioning instead of absolute coordinates.

TOPIC:
{query}

PLAN JSON:
{plan_json}

USER REQUESTED CHANGES:
{change_request}

EXISTING CODE:
{existing_code}

Return ONLY Python code. No markdown or commentary.
"""


def _likely_truncated_tail(code: str) -> bool:
    stripped = (code or "").rstrip()
    if not stripped:
        return True
    bad_tails = ("=", "(", "[", "{", ",", ".", ":", "\\")
    if stripped.endswith(bad_tails):
        return True
    return False


def _binary_tree_completeness_error(code: str, query: str) -> str:
    """Heuristic guard against half-visible or incomplete binary tree renders."""
    text = (query or "").lower()
    if "binary tree" not in text:
        return ""

    # If a Graph-based layout is used, assume structure is likely complete.
    if "Graph(" in code:
        return ""

    node_count = len(re.findall(r"Circle\(|Dot\(|RoundedRectangle\(", code))
    edge_count = len(re.findall(r"Line\(|Arrow\(", code))

    if node_count < 6 or edge_count < 4:
        return "binary tree appears incomplete; ensure full tree nodes and edges are visible"

    return ""


def _validate_generated_code(code: str, expected_steps: int, query: str = "") -> str:
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

    tree_error = _binary_tree_completeness_error(code, query)
    if tree_error:
        return tree_error

    try:
        compile(code, "scene.py", "exec")
    except SyntaxError as e:
        return f"syntax error: {e.msg} at line {e.lineno}"

    return ""


def _stitch_continuation(base_code: str, continuation: str) -> str:
    """Append continuation safely to existing code."""
    left = (base_code or "").rstrip()
    right = (continuation or "").lstrip()
    if not left:
        return right
    if not right:
        return left
    return f"{left}\n{right}"


def _continuation_prompt(query: str, plan_json: str, partial_code: str) -> str:
    tail_lines = "\n".join((partial_code or "").splitlines()[-60:])
    return (
        "You are continuing an incomplete Python file for a Manim Voiceover scene.\n"
        "Do NOT restart from imports or class declaration.\n"
        "Return ONLY the remaining lines that should come after the partial tail.\n"
        "Do not include markdown fences or explanations.\n\n"
        f"Topic: {query}\n"
        f"Plan JSON: {plan_json}\n\n"
        "Partial file tail (continue from here):\n"
        f"{tail_lines}\n"
    )


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

        response_details = call_llm_detailed(
            prompt_for_attempt,
            max_tokens=16384,
            preferred_model=CODER_MODEL,
            disable_thinking=True,
        )

        code = extract_code(response_details.get("text", ""))
        finish_reason = str(response_details.get("finish_reason", "")).upper()
        last_code = code

        validation_error = _validate_generated_code(code, expected_steps=expected_steps, query=query)

        if validation_error and "MAX_TOKENS" in finish_reason:
            continued_code = code
            continuation_error = validation_error
            for hop in range(1, MAX_CONTINUATION_ATTEMPTS + 1):
                cont_prompt = _continuation_prompt(query, plan_json, continued_code)
                cont_details = call_llm_detailed(
                    cont_prompt,
                    max_tokens=8192,
                    preferred_model=CODER_MODEL,
                    disable_thinking=True,
                )
                cont_piece = extract_code(cont_details.get("text", ""))
                if not cont_piece.strip():
                    break

                continued_code = _stitch_continuation(continued_code, cont_piece)
                continuation_error = _validate_generated_code(
                    continued_code,
                    expected_steps=expected_steps,
                    query=query,
                )
                if not continuation_error:
                    print(f"[Coder] ✅ Continuation succeeded after {hop} hop(s)")
                    code = continued_code
                    validation_error = ""
                    break

                cont_finish = str(cont_details.get("finish_reason", "")).upper()
                if "MAX_TOKENS" not in cont_finish:
                    break

            last_code = code if not validation_error else continued_code

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


def revise_manim_code(
    query: str,
    plan: dict,
    existing_code: str,
    change_request: str,
    max_attempts: int = 3,
) -> str:
    """Apply user-requested changes to existing code with validation and retry."""
    print(f"[Coder] Revising code with user feedback: {change_request[:120]}")

    plan_payload = _build_coder_plan_payload(plan or {})
    plan_json = json.dumps(plan_payload, indent=2)
    prompt = REVISION_PROMPT.format(
        query=query,
        plan_json=plan_json,
        change_request=change_request,
        existing_code=existing_code,
    )

    expected_steps = len((plan or {}).get("steps", []))
    last_code = existing_code
    last_validation_error = ""

    for attempt in range(1, max_attempts + 1):
        prompt_for_attempt = prompt
        if attempt > 1:
            prompt_for_attempt += (
                "\n\nIMPORTANT RETRY INSTRUCTION:\n"
                "The previous revision was invalid. Return the full corrected file.\n"
                f"Validation failure to fix: {last_validation_error}\n"
            )

        details = call_llm_detailed(
            prompt_for_attempt,
            max_tokens=8192,
            preferred_model=CODER_MODEL,
            disable_thinking=True,
        )

        candidate = extract_code(details.get("text", ""))
        finish_reason = str(details.get("finish_reason", "")).upper()
        if not candidate.strip():
            candidate = last_code

        validation_error = _validate_generated_code(
            candidate,
            expected_steps=expected_steps,
            query=query,
        )

        if validation_error and "MAX_TOKENS" in finish_reason:
            continued_code = candidate
            for _ in range(MAX_CONTINUATION_ATTEMPTS):
                cont_prompt = _continuation_prompt(query, plan_json, continued_code)
                cont = call_llm_detailed(
                    cont_prompt,
                    max_tokens=4096,
                    preferred_model=CODER_MODEL,
                    disable_thinking=True,
                )
                cont_piece = extract_code(cont.get("text", ""))
                if not cont_piece.strip():
                    break
                continued_code = _stitch_continuation(continued_code, cont_piece)
                validation_error = _validate_generated_code(
                    continued_code,
                    expected_steps=expected_steps,
                    query=query,
                )
                if not validation_error:
                    candidate = continued_code
                    break
                if "MAX_TOKENS" not in str(cont.get("finish_reason", "")).upper():
                    break

        if not validation_error:
            print(f"[Coder] Revision successful on attempt {attempt}")
            return candidate

        last_code = candidate
        last_validation_error = validation_error
        print(f"[Coder] ⚠️  Revision attempt {attempt} failed validation: {validation_error}")

    print("[Coder] ⚠️  Returning last revised code after max attempts")
    return last_code


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