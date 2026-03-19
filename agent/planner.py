import json
from agent.llm import call_llm

PLANNER_PROMPT = """You are an expert educational animation planner.
A teacher wants an animation for the following topic.
Your job is to plan exactly what the animation should show — before any code is written.

Think carefully about:
1. What visual elements are needed for THIS topic (specific labels, values, symbols)
2. What the step-by-step sequence should be (clear learning progression)
3. What each voiceover line should EXPLAIN (not announce) at that exact step
4. What the final summary should show

Return ONLY a JSON object in this exact format:
{{
    "title": "Short animation title",
    "visual_style": "one of: array_boxes, bar_chart, diagram, graph_plot, physics_motion, timeline, flowchart",
    "elements": ["list", "of", "visual", "elements", "needed"],
    "steps": [
        "Step 1: concrete visual action",
        "Step 2: concrete visual action",
        "Step 3: concrete visual action",
        "Step 4: concrete visual action"
    ],
    "voiceovers": [
        "One or two explanatory sentences for step 1",
        "One or two explanatory sentences for step 2",
        "One or two explanatory sentences for step 3",
        "One or two explanatory sentences for step 4"
    ],
    "duration_seconds": 45,
    "summary": "Final message shown at end of video"
}}

VOICEOVER QUALITY RULES:
- Each line must teach cause-and-effect, logic, or intuition for that step.
- Avoid placeholders like "Introduction", "Now we do step 2", "This is happening".
- Include topic-specific terms, values, or relationships.
- Keep each line concise: 12 to 28 words.
- `steps` and `voiceovers` must have the same length.

PLANNING RULES:
- Generate 4 to 7 steps.
- Every step should describe a visible animation action.
- Prefer progressive reveal: setup -> process -> key transition -> result.

VISUAL STYLE GUIDE:
- array_boxes: for search algorithms, data structures, memory
- bar_chart: for sorting algorithms, comparisons, statistics
- diagram: for biology, chemistry, science concepts, how things work
- graph_plot: for math functions, physics equations, data trends
- physics_motion: for moving objects, forces, trajectories, waves
- timeline: for history, sequences, processes, lifecycles
- flowchart: for processes, decision trees, how systems work

Topic to plan: {query}

Return ONLY the JSON. No explanation before or after."""


def _normalize_plan(plan: dict, query: str) -> dict:
    """Ensure the planner output is safe and structurally usable by the coder."""
    safe = dict(plan or {})

    safe["title"] = safe.get("title") or query[:40]
    safe["visual_style"] = safe.get("visual_style") or "diagram"
    safe["elements"] = safe.get("elements") or ["shapes", "labels", "arrows"]
    safe["duration_seconds"] = int(safe.get("duration_seconds") or 45)
    safe["summary"] = safe.get("summary") or f"Understanding {query}"

    steps = safe.get("steps") or []
    voiceovers = safe.get("voiceovers") or []

    if not steps:
        steps = [
            f"Introduce the core idea of {query}",
            "Show the main process with labeled visuals",
            "Highlight the key transition or decision",
            "Conclude with final result and takeaway"
        ]

    # Ensure we have one voiceover line per step.
    if len(voiceovers) < len(steps):
        for i in range(len(voiceovers), len(steps)):
            step_text = steps[i]
            voiceovers.append(
                f"In this step, {step_text.lower()}. Notice how it supports the overall logic of {query}."
            )
    elif len(voiceovers) > len(steps):
        voiceovers = voiceovers[:len(steps)]

    polished_voiceovers = []
    generic_markers = [
        "introduction",
        "conclusion",
        "step",
        "now we",
        "visiting node",
        "this is happening"
    ]

    for line in voiceovers:
        text = str(line).strip()
        lower = text.lower()
        word_count = len(text.split())

        if any(marker in lower for marker in generic_markers):
            text = (
                f"{text}. This is important in {query} because it changes what we should track next."
            )
        elif word_count < 10:
            text = (
                f"{text}. This gives context for the next decision in {query}."
            )

        polished_voiceovers.append(text)

    safe["steps"] = steps
    safe["voiceovers"] = polished_voiceovers
    return safe


def normalize_plan(plan: dict, query: str) -> dict:
    """Public wrapper used when plans are edited in the UI before execution."""
    return _normalize_plan(plan, query)


def plan_animation(query: str) -> dict:
    """
    Takes a teacher's request and returns a structured plan
    before any code is generated.
    """
    print(f"[Planner] Planning animation for: {query}")

    response = call_llm(PLANNER_PROMPT.format(query=query), max_tokens=1500)

    # Parse JSON response with multiple fallback strategies
    try:
        # Strategy 1: Try to parse response as-is (if it's clean JSON)
        clean = response.strip()
        try:
            plan = json.loads(clean)
            plan = _normalize_plan(plan, query)
            print(f"[Planner] Visual style: {plan.get('visual_style')}")
            print(f"[Planner] Steps: {len(plan.get('steps', []))}")
            print(f"[Planner] Duration: {plan.get('duration_seconds')}s")
            return plan
        except json.JSONDecodeError:
            pass

        # Strategy 2: Look for JSON in code fences
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        # Strategy 3: Extract JSON object (look for first { and last })
        if "{" in clean and "}" in clean:
            start_idx = clean.find("{")
            end_idx = clean.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                clean = clean[start_idx:end_idx]

        plan = json.loads(clean)
        plan = _normalize_plan(plan, query)
        print(f"[Planner] Visual style: {plan.get('visual_style')}")
        print(f"[Planner] Steps: {len(plan.get('steps', []))}")
        print(f"[Planner] Duration: {plan.get('duration_seconds')}s")
        return plan

    except Exception as e:
        print(f"[Planner] ⚠️  JSON parse failed: {e}")
        print(f"[Planner] Using fallback plan")
        # Return a safe default plan
        return _normalize_plan({
            "title": query[:40],
            "visual_style": "diagram",
            "elements": ["shapes", "labels", "arrows"],
            "steps": [
                f"Introduce the core idea of {query}",
                "Show the main process with labeled visuals",
                "Highlight the key transition or decision",
                "Conclude with final result and takeaway"
            ],
            "voiceovers": [
                f"We begin with the central idea of {query} and define the key parts before the process starts.",
                "Next, watch how each part changes over time so the mechanism becomes clear and measurable.",
                "This transition is critical because it determines the outcome and reduces common misunderstandings.",
                "Finally, we connect the result to the main takeaway so you can apply the same pattern elsewhere."
            ],
            "duration_seconds": 45,
            "summary": f"Understanding {query}"
        }, query)