import re
import json
from agent.llm import call_llm
from rag.retriever import retrieve

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

OPTIONAL LEARNED EXAMPLE (adapt style, do not copy blindly):
{learned_example}

HERE ARE RELEVANT MANIM PATTERNS FROM DOCUMENTATION:
{rag_context}

Now generate a complete, stunning, professional Manim animation for:
{query}

Use the patterns above as reference. Make it visually rich with colors, smooth animations, and clear educational value.
Add # VOICEOVER: comments and matching `with self.voiceover(...)` blocks at every step.
Return ONLY the Python code. No explanation.
"""


def generate_manim_code(query: str, plan: dict = None) -> str:
    """
    Retrieves relevant Manim docs then calls Claude to generate code.
    Guards against truncation and enforces completeness.
    """
    print(f"[Coder] Generating code for: {query}")

    # Retrieve relevant patterns from docs
    print(f"[RAG] Searching docs for relevant patterns...")
    rag_context = retrieve(query, k=4)
    print(f"[RAG] Found relevant patterns")

    plan = plan or {}
    plan_json = json.dumps(plan, indent=2)
    learned_example = plan.get("learned_example", "None")

    prompt = CODER_PROMPT.format(
        query=query,
        rag_context=rag_context,
        plan_json=plan_json,
        learned_example=learned_example
    )
    # Use very high token limit to prevent truncation of complex animations.
    # Better to overshoot and trim than to get incomplete code.
    response = call_llm(prompt, max_tokens=5500)

    code = extract_code(response)
    
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