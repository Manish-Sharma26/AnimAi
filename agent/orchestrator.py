from agent.planner import plan_animation
from agent.coder import generate_manim_code
from agent.debugger import debug_manim_code
from agent.feedback import get_learned_examples
from sandbox.sandbox import run_manim_sandbox
from sandbox.audio_merger import add_voice_to_video
import os

MAX_ATTEMPTS = 3


def run_agent(user_query: str) -> dict:
    """
    Full pipeline:
    1. Planner thinks about what animation to create
    2. Coder writes Manim code from the plan
    3. Sandbox compiles with retry loop
    4. Voice narration added
    5. Return final video
    """

    print()
    print("=" * 50)
    print(f"[Agent] Starting for: {user_query}")
    print("=" * 50)

    # Step 1: Plan the animation
    print("\n[Agent] Step 1: Planning...")
    plan = plan_animation(user_query)

    # Check if we have learned examples for this category
    category = plan.get("visual_style", "diagram")
    learned = get_learned_examples(category, k=1)
    if learned:
        print(f"[Agent] Found {len(learned)} learned example(s) for category: {category}")
        # Inject best learned example into plan for coder context
        plan["learned_example"] = learned[0]["code"]

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

    # Step 4: Add voice
    print(f"\n[Agent] Adding voice narration...")
    os.makedirs("outputs", exist_ok=True)

    voice_result = add_voice_to_video(
        code=code,
        video_path=result["video_path"],
        output_path="outputs/final_animation.mp4"
    )

    print()
    print("=" * 50)
    print(f"[Agent] COMPLETE!")
    print(f"[Agent] Video: {voice_result['video_path']}")
    print("=" * 50)

    return {
        "status": "success",
        "video_path": voice_result["video_path"],
        "has_audio": voice_result["has_audio"],
        "code": code,
        "plan": plan,
        "attempts": attempt,
        "category": category
    }