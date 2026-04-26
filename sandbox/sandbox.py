import subprocess
import os
import shutil
import tempfile
import glob

try:
    from agent.failure_logger import log_failure as _log_failure
except ImportError:
    # Graceful fallback if run standalone
    def _log_failure(**kwargs) -> str:
        return ""

# Using pre-built Manim image — no custom build needed
DOCKER_IMAGE = "manim-voiceover"
MIN_VIDEO_BYTES = 200_000


def _tail(text: str, max_chars: int = 20000) -> str:
    text = text or ""
    return text[-max_chars:] if len(text) > max_chars else text


def _extract_actual_error(stderr: str) -> str:
    """Extract the actual Python exception from Manim's verbose output.

    Manim's stderr interleaves INFO logs (dvisvgm, tex file writing) with real
    errors, making it hard for the debugger to find the root cause.  This
    function pulls out just the Traceback + exception line.
    """
    if not stderr:
        return ""
    lines = stderr.splitlines()

    # Walk through looking for the last Traceback block.
    error_lines: list[str] = []
    in_traceback = False
    for line in lines:
        if "Traceback" in line and "most recent call last" in line:
            in_traceback = True
            error_lines = [line]
        elif in_traceback:
            error_lines.append(line)
            stripped = line.strip()
            # A non-indented, non-empty line after traceback frames = the exception.
            if stripped and not line.startswith(" ") and not line.startswith("\t") and stripped != line:
                continue
            # Heuristic: exception lines start with a known Error suffix.
            if any(stripped.startswith(e) for e in (
                "TypeError", "ValueError", "NameError", "AttributeError",
                "RuntimeError", "ImportError", "KeyError", "IndexError",
                "FileNotFoundError", "ModuleNotFoundError", "SyntaxError",
                "ZeroDivisionError", "StopIteration", "RecursionError",
            )):
                break

    if error_lines:
        return "\n".join(error_lines)

    # Fallback: scan backwards for a bare exception line.
    for line in reversed(lines):
        stripped = line.strip()
        if any(stripped.startswith(e) for e in (
            "TypeError", "ValueError", "NameError", "AttributeError",
            "RuntimeError", "ImportError", "KeyError", "IndexError",
            "FileNotFoundError", "ModuleNotFoundError",
        )):
            return stripped

    # Final fallback – return tail.
    return _tail(stderr, 3000)


def _pick_newest(paths):
    existing = [p for p in paths if os.path.isfile(p)]
    if not existing:
        return None
    return max(existing, key=os.path.getmtime)


def _find_best_video(output_root: str):
    """Find the best final render video and avoid partial fragments."""
    generated_scene = glob.glob(
        os.path.join(output_root, "videos", "**", "GeneratedScene.mp4"),
        recursive=True,
    )
    best = _pick_newest(generated_scene)

    if best and os.path.getsize(best) >= MIN_VIDEO_BYTES:
        return best, ""

    all_mp4 = glob.glob(os.path.join(output_root, "**", "*.mp4"), recursive=True)
    final_candidates = [
        p for p in all_mp4
        if "partial_movie_files" not in p.replace("\\", "/")
    ]
    best = _pick_newest(final_candidates)
    if best and os.path.getsize(best) >= MIN_VIDEO_BYTES:
        return best, ""

    partials = glob.glob(
        os.path.join(output_root, "**", "partial_movie_files", "**", "*.mp4"),
        recursive=True,
    )
    if partials:
        return None, "Partial segments exist but final merged video is missing"

    if best and os.path.getsize(best) < MIN_VIDEO_BYTES:
        return None, f"Final video exists but is too small ({os.path.getsize(best)} bytes)"

    return None, "No video file was generated"

def run_manim_sandbox(code: str, timeout: int = 300, query: str = "") -> dict:
    """
    Takes Manim Python code as a string.
    Runs it inside Docker using pre-built Manim image.
    Returns success/failure + video path or error message.
    """

    # Fast fail on syntax problems so debugger gets precise line-level feedback.
    try:
        compile(code, "scene.py", "exec")
    except SyntaxError as e:
        os.makedirs("outputs", exist_ok=True)
        with open(os.path.join("outputs", "last_failed_scene.py"), "w", encoding="utf-8") as f:
            f.write(code)

        syntax_error = (
            f"SyntaxError: {e.msg} at line {e.lineno}, offset {e.offset}\n"
            f"Line: {e.text or ''}"
        )
        with open(os.path.join("outputs", "last_failed_log.txt"), "w", encoding="utf-8") as f:
            f.write(syntax_error)

        # Persist to timestamped failure log
        _log_failure(
            error=syntax_error,
            code=code,
            failure_type="syntax_error",
            query=query,
        )

        print("[Sandbox] ❌ Python syntax check failed before Docker run")
        print(f"[Sandbox] Error: {syntax_error}")
        return {"success": False, "error": syntax_error, "stdout": "", "stderr": syntax_error}

    # Step 1: Create a temporary folder on your Windows machine
    tmp_dir = tempfile.mkdtemp()

    # Fix Windows path for Docker — convert C:\Users\... to /c/Users/...
    docker_path = tmp_dir.replace("\\", "/")
    if docker_path[1] == ":":
        docker_path = "/" + docker_path[0].lower() + docker_path[2:]

    try:
        # Step 2: Write the code into a file in that folder
        scene_path = os.path.join(tmp_dir, "scene.py")
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"[Sandbox] Running code in Docker...")
        print(f"[Sandbox] Using image: {DOCKER_IMAGE}")

        # Step 3: Run Docker with pre-built image
        docker_cmd = [
            "docker", "run",
            "--rm",
            "-v", f"{docker_path}:/sandbox",
            "--workdir", "/sandbox",
        ]

        # Forward host env vars required by AzureService and TTS provider selection.
        for env_name in (
            "AZURE_SUBSCRIPTION_KEY",
            "AZURE_SERVICE_REGION",
            "TTS_PROVIDER",
            "TTS_FALLBACK_PROVIDER",
            "AZURE_TTS_VOICE",
            "AZURE_TTS_STYLE",
        ):
            if os.getenv(env_name):
                docker_cmd.extend(["-e", env_name])

        docker_cmd.extend([
            DOCKER_IMAGE,
            "manim", "render",
            "--media_dir", "/sandbox/output",
            "--verbosity", "WARNING",
            "-ql",
            "/sandbox/scene.py",
        ])

        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )

        # Step 4: Check if it worked
        if result.returncode == 0:
            video_path, video_error = _find_best_video(os.path.join(tmp_dir, "output"))

            if video_path:
                os.makedirs("outputs", exist_ok=True)
                final_path = os.path.join("outputs", "animation.mp4")
                shutil.copy(video_path, final_path)

                with open(os.path.join("outputs", "last_success_scene.py"), "w", encoding="utf-8") as f:
                    f.write(code)

                print(f"[Sandbox] ✅ Success! Video saved to: {final_path}")
                return {
                    "success": True,
                    "video_path": final_path,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                print(f"[Sandbox] ❌ Compiled but video artifact invalid: {video_error}")
                return {
                    "success": False,
                    "error": video_error,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        else:
            # Extract the actual Python exception first; fall back to raw tail.
            extracted = _extract_actual_error(result.stderr)
            stderr_tail = _tail(result.stderr)
            stdout_tail = _tail(result.stdout)
            combined_error = (
                "[extracted error]\n"
                f"{extracted}\n\n"
                "[manim stderr tail]\n"
                f"{stderr_tail}\n\n"
                "[manim stdout]\n"
                f"{stdout_tail}"
            )

            # Keep last failed artifacts for easier local debugging.
            os.makedirs("outputs", exist_ok=True)
            with open(os.path.join("outputs", "last_failed_scene.py"), "w", encoding="utf-8") as f:
                f.write(code)
            with open(os.path.join("outputs", "last_failed_log.txt"), "w", encoding="utf-8") as f:
                f.write(combined_error)

            # Detect failure type for better log tagging
            _err_lower = combined_error.lower()
            if "word boundaries are required" in _err_lower or "wait_until_bookmark" in _err_lower:
                _failure_type = "bookmark_error"
            elif (
                "speech synthesis failed" in _err_lower
                or "cancellationreason.error" in _err_lower
                or "ws_open_error" in _err_lower
                or ("dns" in _err_lower and "resolution failed" in _err_lower)
            ):
                _failure_type = "tts_synthesis_failed"
            elif "no video file was generated" in _err_lower:
                _failure_type = "no_video"
            elif "syntaxerror" in _err_lower:
                _failure_type = "syntax_error"
            elif "attributeerror" in _err_lower:
                _failure_type = "attribute_error"
            elif "nameerror" in _err_lower:
                _failure_type = "name_error"
            elif "typeerror" in _err_lower:
                _failure_type = "type_error"
            else:
                _failure_type = "runtime_error"

            # Persist to timestamped failure log
            _log_failure(
                error=combined_error,
                code=code,
                failure_type=_failure_type,
                query=query,
            )

            print(f"[Sandbox] ❌ Compilation failed")
            print(f"[Sandbox] Error: {_tail(combined_error, 1200)}")
            return {
                "success": False,
                "error": combined_error,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        print("[Sandbox] ❌ Timed out")
        return {"success": False, "error": f"Rendering timed out after {timeout} seconds"}

    except Exception as e:
        print(f"[Sandbox] ❌ Unexpected error: {e}")
        return {"success": False, "error": str(e)}

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)