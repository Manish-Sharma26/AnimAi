import os
import re

from agent.planner import plan_animation, normalize_plan
from agent.teacher import teach_concept
from agent.intent import classify_query_intent, extract_topic_from_query
from agent.coder import generate_manim_code, revise_manim_code
from agent.debugger import debug_manim_code
from agent.validator import validate_video_structure, format_validation_for_prompt
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
    if "word boundaries are required" in text or "wait_until_bookmark" in text:
        return "bookmark_error"
    # Azure TTS synthesis failure — DNS/network failure DURING synthesis (not constructor)
    # Triggered by: "speech synthesis failed", "cancellationreason.error",
    # "ws_open_error", "dns resolution failed", "connection failed"
    if (
        "speech synthesis failed" in text
        or "cancellationreason.error" in text
        or "ws_open_error" in text
        or "ws_error_underlying_io_error" in text
        or "underlying_io_error" in text
        or ("dns" in text and "resolution failed" in text)
        or ("connection failed" in text and "tts" in text)
        or ("websocket" in text and "error" in text and "tts" in text)
    ):
        return "tts_synthesis_failed"
    if "unexpected keyword argument" in text and (
        "'alignment'" in text or "'max_width'" in text or "'justify'" in text
    ):
        return "invalid_text_param"
    # gTTS does not accept prosody= — strip it when this error appears
    if "unexpected keyword argument" in text and "'prosody'" in text:
        return "gtts_prosody_error"
    if "unexpected keyword argument" in text and "'corner_radius'" in text:
        return "corner_radius_error"
    if "has a" in text and "<= 0 seconds" in text and "duration" in text:
        return "negative_wait_duration"
    if "has no attribute 'set_camera_orientation'" in text:
        return "3d_scene_error"
    if "_get_axis_label()" in text and "unexpected keyword argument" in text:
        return "axis_label_error"
    if "unsupported operand type(s) for -: 'method' and 'float'" in text:
        return "known_manim_runtime"
    if "getter() takes 1 positional argument but 2 were given" in text:
        return "deprecated_api"
    if "getter() takes 1 positional argument" in text and "get_part_by_text" in text:
        return "getter_takes_1_arg"
    if "attributeerror" in text:
        return "attribute_error"
    if "nameerror" in text:
        return "name_error"
    return "other"


def _force_gtts_fallback(code: str) -> str:
    """Patch generated code to force gTTS as the TTS provider.

    When Azure synthesis fails at runtime (DNS/network error during a voiceover
    call), the try/except around AzureService(**kwargs) doesn't help — the
    failure happens inside the voiceover context manager, not the constructor.

    This function rewrites the TTS setup block to use gTTS directly AND strips
    the ``prosody=`` keyword argument from all voiceover calls, because
    GTTSService does NOT accept ``prosody`` — it raises:
        TypeError: gTTS.__init__() got an unexpected keyword argument 'prosody'
    """
    import re
    # Replace the provider check so it always branches to GTTSService
    # Strategy: inject an override at the top of the TTS block so the azure
    # branch is bypassed even if TTS_PROVIDER env var says "azure".
    patched = re.sub(
        r'if provider == ["\']azure["\']:',
        'if False:  # [PATCHED: forced gTTS fallback — Azure unavailable]',
        code,
    )

    # GTTSService does NOT support the prosody= kwarg — strip it from every
    # self.voiceover(..., prosody={...}) call to prevent a TypeError crash.
    # This targets the prosody= argument in any self.voiceover(...) call.
    patched = re.sub(
        r',\s*prosody\s*=\s*\{[^}]*\}',
        '',  # remove ", prosody={...}" entirely
        patched,
    )
    return patched


def build_plan(user_query: str) -> dict:
    """Generate a structured animation plan from the user's prompt.

    Detects query intent (three tiers):
    - ``"bare_topic"``          → user typed only a topic name (e.g. "RNN")
    - ``"simple_explanation"``  → user typed a short educational request
      (e.g. "explain gradient descent", "what is backpropagation")
    Both use the strict 5-beat pedagogical arc with zero content overlap:
      Topic Name → Theory → Working → Need/Use Case → Summary

    - ``"detailed"``    → user wrote a specific, complex instruction
      → uses the standard comprehensive 5-segment planner.

    Returns a dict with 'plan', 'teacher_explanation', and 'intent' keys.
    """
    intent = classify_query_intent(user_query)
    print(f"\n[Agent] Query intent detected: {intent!r} for: {user_query!r}")

    # For simple_explanation, extract the clean topic name
    if intent == "simple_explanation":
        topic_name = extract_topic_from_query(user_query)
        print(f"[Agent] Extracted topic name: {topic_name!r} from query: {user_query!r}")
        teacher_query = topic_name
    else:
        teacher_query = user_query

    print("\n[Agent] Step 1a: Teacher explaining concept...")
    teacher_explanation = teach_concept(teacher_query, intent=intent)

    print("\n[Agent] Step 1b: Planning animation from teacher explanation...")
    plan = plan_animation(teacher_query, teacher_explanation=teacher_explanation, intent=intent)

    plan["teacher_explanation"] = teacher_explanation
    plan["_intent"] = intent
    plan["_original_query"] = user_query
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

    # Step 2b: Validate video structure and fix if needed
    structure_report = validate_video_structure(code, plan)
    if not structure_report["valid"]:
        print(f"[Agent] ⚠️ Structure validation found issues: {structure_report['issues']}")
        fix_prompt = format_validation_for_prompt(structure_report)
        print("[Agent] Sending to debugger for structure fixes...")
        code = debug_manim_code(code, f"STRUCTURE VALIDATION FAILED:\n{fix_prompt}")

    # Step 3: Compile with retry loop
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n[Agent] Attempt {attempt}/{MAX_ATTEMPTS}")

        result = run_manim_sandbox(code, query=user_query)

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

            if failure_type == "bookmark_error":
                print("[Agent] Recovery: stripping GTTSService-incompatible bookmarks...")
                code = re.sub("<bookmark\s+mark=[\"'][^\"']*[\"']\s*/>", '', code)
                code = re.sub(r'\bself\.wait_until_bookmark\s*\([^)]*\)\s*\n?', '', code)
                continue

            if failure_type == "tts_synthesis_failed":
                # Azure TTS failed DURING synthesis (DNS/network error), not at constructor level.
                # The try/except in the generated code only covers AzureService(**kwargs) init.
                # We must force gTTS at the code level and retry the sandbox.
                print("[Agent] Recovery: Azure TTS synthesis failed (DNS/network error) — "
                      "patching code to force gTTS fallback and retrying...")
                code = _force_gtts_fallback(code)
                # Also set env var for the rest of this run so future retries stay on gTTS
                os.environ["TTS_PROVIDER"] = "gtts"
                continue

            if failure_type == "invalid_text_param":
                from agent.coder import _strip_kwarg
                print("[Agent] Recovery: stripping invalid Text() parameters (alignment/max_width/justify)...")
                for bad_kw in ("alignment", "max_width", "justify"):
                    code = _strip_kwarg(code, bad_kw)
                continue

            if failure_type == "gtts_prosody_error":
                print("[Agent] Recovery: stripping prosody= kwargs unsupported by GTTSService...")
                from agent.coder import _strip_prosody_kwargs
                code = _strip_prosody_kwargs(code)
                continue

            if failure_type == "corner_radius_error":
                print("[Agent] Recovery: converting Rectangle(corner_radius=X) → RoundedRectangle(corner_radius=X)...")
                def _fix_corner_radius(code_str: str) -> str:
                    lines = code_str.split('\n')
                    out = []
                    for line in lines:
                        if 'corner_radius' in line and 'Rectangle(' in line and 'RoundedRectangle' not in line:
                            line = line.replace('Rectangle(', 'RoundedRectangle(')
                        out.append(line)
                    return '\n'.join(out)
                code = _fix_corner_radius(code)
                continue

            if failure_type == "getter_takes_1_arg":
                print("[Agent] Recovery: removing get_part_by_text() calls that crash at runtime...")
                code = re.sub(r'(\w+)\.get_part_by_text\([^)]+\)', r'\1', code)
                continue

            if failure_type == "negative_wait_duration":
                print("[Agent] Recovery: guarding tracker.get_remaining_duration() against zero/negative values...")
                code = re.sub(
                    r'self\.wait\(tracker\.get_remaining_duration\(\)\)',
                    'self.wait(max(0.05, tracker.get_remaining_duration()))',
                    code
                )
                code = re.sub(
                    r'run_time\s*=\s*tracker\.get_remaining_duration\(\)',
                    'run_time=max(0.05, tracker.get_remaining_duration())',
                    code
                )
                continue

            if failure_type == "3d_scene_error":
                print("[Agent] Recovery: removing 3D scene methods incompatible with VoiceoverScene...")
                code = re.sub(
                    r'\bself\.set_camera_orientation\s*\([^)]*\)\s*\n?',
                    '# [REMOVED: set_camera_orientation not available on VoiceoverScene]\n',
                    code
                )
                code = re.sub(r'\bThreeDAxes\b', 'Axes', code)
                continue

            if failure_type == "axis_label_error":
                print("[Agent] Recovery: stripping invalid kwargs from get_x/y_axis_label calls...")
                def _fix_axis_label_line(line):
                    if 'get_x_axis_label' in line or 'get_y_axis_label' in line or 'get_axis_labels' in line:
                        for bad_kw in ('color', 'font_size', 'weight', 'stroke_width'):
                            line = re.sub(r',\s*' + bad_kw + r'\s*=[^,)]+', '', line)
                    return line
                code = '\n'.join(_fix_axis_label_line(ln) for ln in code.split('\n'))
                continue

            if failure_type in ("timeout", "no_video"):
                print("[Agent] Recovery: rerunning sandbox with extended timeout...")
                rerun = run_manim_sandbox(code, timeout=180, query=user_query)
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
            result = run_manim_sandbox(code, query=user_query)
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
                    rerun = run_manim_sandbox(code, timeout=180, query=user_query)
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

                if failure_type == "tts_synthesis_failed":
                    print("[Agent] Recovery: Azure TTS synthesis failed in revision — "
                          "patching code to force gTTS fallback and retrying...")
                    code = _force_gtts_fallback(code)
                    os.environ["TTS_PROVIDER"] = "gtts"
                    continue

                if failure_type == "gtts_prosody_error":
                    print("[Agent] Recovery: stripping prosody= kwargs unsupported by GTTSService (revision)...")
                    from agent.coder import _strip_prosody_kwargs
                    code = _strip_prosody_kwargs(code)
                    continue

                code = debug_manim_code(code, result["error"])

    return {
        "status": "failed",
        "error": (result or {}).get("error", "Failed to apply requested changes"),
        "attempts": MAX_ATTEMPTS,
    }

