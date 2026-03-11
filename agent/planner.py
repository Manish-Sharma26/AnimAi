import json
from agent.llm import call_llm

PLANNER_PROMPT = """You are an expert educational animation planner.
A teacher wants an animation for the following topic.
Your job is to plan exactly what the animation should show — before any code is written.

Think carefully about:
1. What visual elements are needed
2. What the step-by-step sequence should be
3. What each voiceover line should say
4. What the final summary should show

Return ONLY a JSON object in this exact format:
{{
    "title": "Short animation title",
    "visual_style": "one of: array_boxes, bar_chart, diagram, graph_plot, physics_motion, timeline, flowchart",
    "elements": ["list", "of", "visual", "elements", "needed"],
    "steps": [
        "Step 1: what happens visually",
        "Step 2: what happens visually",
        "Step 3: what happens visually"
    ],
    "voiceovers": [
        "Voiceover for step 1",
        "Voiceover for step 2",
        "Voiceover for step 3"
    ],
    "duration_seconds": 45,
    "summary": "Final message shown at end of video"
}}

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


def plan_animation(query: str) -> dict:
    """
    Takes a teacher's request and returns a structured plan
    before any code is generated.
    """
    print(f"[Planner] Planning animation for: {query}")

    response = call_llm(PLANNER_PROMPT.format(query=query), max_tokens=1000)

    # Parse JSON response
    try:
        # Clean response in case AI added extra text
        clean = response.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        plan = json.loads(clean)
        print(f"[Planner] Visual style: {plan.get('visual_style')}")
        print(f"[Planner] Steps: {len(plan.get('steps', []))}")
        print(f"[Planner] Duration: {plan.get('duration_seconds')}s")
        return plan

    except Exception as e:
        print(f"[Planner] JSON parse failed: {e}")
        # Return a safe default plan
        return {
            "title": query[:40],
            "visual_style": "diagram",
            "elements": ["shapes", "labels", "arrows"],
            "steps": ["Show the concept", "Explain the details", "Summarize"],
            "voiceovers": [f"Let us explore {query}", "Here are the key details", "In summary"],
            "duration_seconds": 45,
            "summary": f"Understanding {query}"
        }