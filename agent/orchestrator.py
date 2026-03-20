from agent.planner import plan_animation, normalize_plan
from agent.coder import generate_manim_code
from agent.debugger import debug_manim_code
from sandbox.sandbox import run_manim_sandbox

MAX_ATTEMPTS = 3


def build_plan(user_query: str) -> dict:
    """Generate a structured animation plan from the user's prompt."""
    print("\n[Agent] Step 1: Planning...")
    return plan_animation(user_query)


def run_agent_with_plan(user_query: str, approved_plan: dict) -> dict:
    """
    Pipeline execution using a pre-approved plan.
    """
    print()
    print("=" * 50)
    print(f"[Agent] Starting generation for: {user_query}")
    print("=" * 50)

    # Step 1: Normalize/guard the approved plan.
    plan = normalize_plan(approved_plan or {}, user_query)
    category = plan.get("visual_style", "diagram")

    # Step 2: Generate code from plan
    print("\n[Agent] Step 2: Generating code...")
    code = generate_manim_code(user_query, plan)

    # Step 3: Compile with retry loop
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n[Agent] Attempt {attempt}/{MAX_ATTEMPTS}")

        result = run_manim_sandbox(code)

        if result["success"]:
            print(f"[Agent] Compiled on attempt {attempt}!")
            break

        print(f"[Agent] Compilation failed — sending to debugger...")

        if attempt < MAX_ATTEMPTS:
            code = debug_manim_code(code, result["error"])
        else:
            print(f"[Agent] All {MAX_ATTEMPTS} attempts failed")
            return {
                "status": "failed",
                "error": result["error"],
                "attempts": attempt
            }

    # Step 4: Voice is generated during Manim render via VoiceoverScene.
    has_audio = "self.voiceover(" in code and "VoiceoverScene" in code

    print()
    print("=" * 50)
    print(f"[Agent] COMPLETE!")
    print(f"[Agent] Video: {result['video_path']}")
    print("=" * 50)

    return {
        "status": "success",
        "video_path": result["video_path"],
        "has_audio": has_audio,
        "code": code,
        "plan": plan,
        "attempts": attempt,
        "category": category
    }


def run_agent(user_query: str) -> dict:
    """
    Full pipeline:
    1. Planner thinks about what animation to create
    2. Coder writes Manim code from the plan
    3. Sandbox compiles with retry loop
    4. Voice narration rendered directly in Manim
    5. Return final video
    """

    print()
    print("=" * 50)
    print(f"[Agent] Starting for: {user_query}")
    print("=" * 50)

    plan = build_plan(user_query)
    return run_agent_with_plan(user_query, plan)