import re
from agent.llm import call_llm
from rag.retriever import retrieve

CODER_PROMPT = """You are an expert Manim animator creating professional educational animations for AnimAI Studio.

STRICT CODE RULES:
1. Always use `from manim import *`
2. Class must extend Scene and be named GeneratedScene
3. Add # VOICEOVER: comment before every animation block
4. Never use VoiceoverScene or any external imports
5. Always set: self.camera.background_color = "#0F0F1A"

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

HERE ARE RELEVANT MANIM PATTERNS FROM DOCUMENTATION:
{rag_context}

Now generate a complete, stunning, professional Manim animation for:
{query}

Use the patterns above as reference. Make it visually rich with colors, smooth animations, and clear educational value.
Add # VOICEOVER: comments at every step.
Return ONLY the Python code. No explanation.
```python"""


def generate_manim_code(query: str, plan: dict = None) -> str:
    """
    Retrieves relevant Manim docs then calls Groq to generate code.
    """
    print(f"[Coder] Generating code for: {query}")

    # Retrieve relevant patterns from docs
    print(f"[RAG] Searching docs for relevant patterns...")
    rag_context = retrieve(query, k=4)
    print(f"[RAG] Found relevant patterns")

    prompt = CODER_PROMPT.format(query=query, rag_context=rag_context)
    response = call_llm(prompt, max_tokens=3000)

    code = extract_code(response)
    print(f"[Coder] Generated {len(code.splitlines())} lines of code")
    return code


def extract_code(text: str) -> str:
    """
    Extracts Python code from LLM response.
    Handles cases where model wraps in ```python blocks or not.
    """
    # Try to find ```python ... ``` block
    match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try plain ``` block
    match = re.search(r'```\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no code block found, return as is
    return text.strip()