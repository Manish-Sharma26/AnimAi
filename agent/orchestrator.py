from agent.planner import plan_animation, normalize_plan
from agent.teacher import teach_concept
from agent.coder import generate_manim_code, revise_manim_code
from agent.debugger import debug_manim_code
from sandbox.sandbox import run_manim_sandbox

MAX_ATTEMPTS = 3
MAX_REVISION_TRIES = 3


def _classify_failure(error_text: str) -> str:
    text = (error_text or "").lower()
    if "syntaxerror" in text and (
        "was never closed" in text
        or "unexpected eof" in text
        or "eol while scanning" in text
    ):
        return "syntax_truncation"
    if "no video file was generated" in text:
        return "no_video"
    if "timed out" in text:
        return "timeout"
    if "unsupported operand type(s) for -: 'method' and 'float'" in text:
        return "known_manim_runtime"
    return "other"


def build_plan(user_query: str) -> dict:
    """Generate a structured animation plan from the user's prompt.

    Returns a dict with 'plan' and 'teacher_explanation' keys.
    """
    print("\n[Agent] Step 1a: Teacher explaining concept...")
    teacher_explanation = teach_concept(user_query)

    print("\n[Agent] Step 1b: Planning animation from teacher explanation...")
    plan = plan_animation(user_query, teacher_explanation=teacher_explanation)

    plan["teacher_explanation"] = teacher_explanation
    return plan


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
            failure_type = _classify_failure(result.get("error", ""))

            if failure_type == "syntax_truncation":
                print("[Agent] Recovery: syntax truncation detected, regenerating code...")
                code = generate_manim_code(user_query, plan)
                continue

            if failure_type in ("timeout", "no_video"):
                print("[Agent] Recovery: rerunning sandbox with extended timeout...")
                rerun = run_manim_sandbox(code, timeout=180)
                if rerun["success"]:
                    result = rerun
                    print(f"[Agent] Compiled on attempt {attempt} after rerun!")
                    break
                result = rerun

            if failure_type == "known_manim_runtime":
                print("[Agent] Recovery: applying runtime-focused debugger fix...")

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


def apply_user_changes(
    user_query: str,
    approved_plan: dict,
    existing_code: str,
    change_request: str,
    max_revision_tries: int = MAX_REVISION_TRIES,
) -> dict:
    """Apply user feedback to existing code and re-render with up to 3 revision tries."""
    print()
    print("=" * 50)
    print(f"[Agent] Applying user-requested changes: {change_request}")
    print("=" * 50)

    plan = normalize_plan(approved_plan or {}, user_query)
    category = plan.get("visual_style", "diagram")
    code = existing_code or ""

    for revision_try in range(1, max_revision_tries + 1):
        print(f"\n[Agent] Revision try {revision_try}/{max_revision_tries}")
        code = revise_manim_code(
            user_query,
            plan,
            code,
            change_request,
            max_attempts=3,
        )

        result = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"[Agent] Compile attempt {attempt}/{MAX_ATTEMPTS} (revision try {revision_try})")
            result = run_manim_sandbox(code)
            if result["success"]:
                print("[Agent] Revised animation compiled successfully")
                has_audio = "self.voiceover(" in code and "VoiceoverScene" in code
                return {
                    "status": "success",
                    "video_path": result["video_path"],
                    "has_audio": has_audio,
                    "code": code,
                    "plan": plan,
                    "attempts": attempt,
                    "revision_try": revision_try,
                    "category": category,
                }

            if attempt < MAX_ATTEMPTS:
                failure_type = _classify_failure(result.get("error", ""))

                if failure_type == "syntax_truncation":
                    print("[Agent] Recovery: syntax truncation in revised code, re-revising...")
                    code = revise_manim_code(
                        user_query,
                        plan,
                        code,
                        change_request,
                        max_attempts=1,
                    )
                    continue

                if failure_type in ("timeout", "no_video"):
                    print("[Agent] Recovery: rerunning revised code with extended timeout...")
                    rerun = run_manim_sandbox(code, timeout=180)
                    if rerun["success"]:
                        has_audio = "self.voiceover(" in code and "VoiceoverScene" in code
                        return {
                            "status": "success",
                            "video_path": rerun["video_path"],
                            "has_audio": has_audio,
                            "code": code,
                            "plan": plan,
                            "attempts": attempt,
                            "revision_try": revision_try,
                            "category": category,
                        }
                    result = rerun

                code = debug_manim_code(code, result["error"])

    return {
        "status": "failed",
        "error": (result or {}).get("error", "Failed to apply requested changes"),
        "attempts": MAX_ATTEMPTS,
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