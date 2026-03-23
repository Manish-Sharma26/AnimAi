import json
import os
from agent.llm import call_llm

TEACHER_MODEL = os.getenv("GEMINI_TEACHER_MODEL", "gemini-3.0-flash")

TEACHER_PROMPT = """You are a world-class teacher who explains concepts to students in a simple, clear, and engaging way.

A student has asked about the following topic:
{query}

Your job is to break down this concept so that an animation designer can turn it into a visual educational video.

Think about:
1. What is the core idea in one sentence?
2. What are the key components or terms the student must understand?
3. What is the step-by-step process or logic? (Use concrete values, not abstract descriptions)
4. What is a simple real-world analogy that makes this click?
5. What is the single most common misconception about this topic?
6. What should the student walk away remembering?

Return ONLY a JSON object in this exact format:
{{
    "topic": "Clear name of the topic",
    "core_idea": "One-sentence explanation of the concept",
    "key_terms": [
        {{"term": "Term 1", "meaning": "Simple definition"}},
        {{"term": "Term 2", "meaning": "Simple definition"}}
    ],
    "step_by_step": [
        "Step 1: concrete description with specific values or examples",
        "Step 2: concrete description with specific values or examples",
        "Step 3: concrete description with specific values or examples"
    ],
    "analogy": "A relatable real-world analogy",
    "misconception": "The most common mistake students make about this",
    "takeaway": "The single most important thing to remember",
    "visual_complexity": "low or medium or high",
    "max_simultaneous_objects": 8
}}

QUALITY RULES:
- Use specific numbers, values, and examples — never be abstract.
- Speak as if explaining to a curious 14-year-old.
- Keep each step_by_step entry to 1-2 sentences max.
- The analogy should be something from everyday life.
- Generate 3 to 6 step_by_step entries.
- Estimate visual_complexity: "low" (≤5 simultaneous objects on screen), "medium" (6-10), "high" (11+).
- Set max_simultaneous_objects to a realistic count for the topic — this tells the animator how many things can be on screen at once.

Return ONLY the JSON. No explanation before or after."""

TEACHER_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING"},
        "core_idea": {"type": "STRING"},
        "key_terms": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "term": {"type": "STRING"},
                    "meaning": {"type": "STRING"},
                },
                "required": ["term", "meaning"],
            },
        },
        "step_by_step": {"type": "ARRAY", "items": {"type": "STRING"}},
        "analogy": {"type": "STRING"},
        "misconception": {"type": "STRING"},
        "takeaway": {"type": "STRING"},
        "visual_complexity": {"type": "STRING"},
        "max_simultaneous_objects": {"type": "INTEGER"},
    },
    "required": [
        "topic",
        "core_idea",
        "key_terms",
        "step_by_step",
        "analogy",
        "misconception",
        "takeaway",
        "visual_complexity",
        "max_simultaneous_objects",
    ],
}


def _normalize_explanation(explanation: dict, query: str) -> dict:
    """Ensure the teacher output is structurally safe."""
    safe = dict(explanation or {})

    safe["topic"] = safe.get("topic") or query[:60]
    safe["core_idea"] = safe.get("core_idea") or f"Understanding the fundamentals of {query}"
    safe["key_terms"] = safe.get("key_terms") or []
    safe["step_by_step"] = safe.get("step_by_step") or [
        f"Start by understanding what {query} means at its simplest level.",
        "Walk through the main process with a concrete example.",
        "Observe the key moment where the result becomes clear.",
    ]
    safe["analogy"] = safe.get("analogy") or ""
    safe["misconception"] = safe.get("misconception") or ""
    safe["takeaway"] = safe.get("takeaway") or f"The key idea behind {query}"
    safe["visual_complexity"] = safe.get("visual_complexity") or "medium"
    safe["max_simultaneous_objects"] = int(safe.get("max_simultaneous_objects") or 8)

    return safe


def teach_concept(query: str) -> dict:
    """
    Takes a user's topic and returns a clear, structured educational
    explanation that can guide the animation planner.
    """
    print(f"[Teacher] Explaining concept: {query}")

    response = call_llm(
        TEACHER_PROMPT.format(query=query),
        max_tokens=4096,
        response_mime_type="application/json",
        response_schema=TEACHER_RESPONSE_SCHEMA,
        preferred_model=TEACHER_MODEL,
    )

    try:
        explanation = json.loads(response.strip())
        explanation = _normalize_explanation(explanation, query)
        print(f"[Teacher] Core idea: {explanation.get('core_idea', '')[:80]}")
        print(f"[Teacher] Steps: {len(explanation.get('step_by_step', []))}")
        return explanation
    except Exception as e:
        print(f"[Teacher] WARNING: JSON parse failed: {e}")
        return _normalize_explanation({}, query)
