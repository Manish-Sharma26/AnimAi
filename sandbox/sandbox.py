import subprocess
import os
import shutil
import tempfile
import glob

# Using pre-built Manim image — no custom build needed
DOCKER_IMAGE = "manim-voiceover"

def run_manim_sandbox(code: str, timeout: int = 120) -> dict:
    """
    Takes Manim Python code as a string.
    Runs it inside Docker using pre-built Manim image.
    Returns success/failure + video path or error message.
    """

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
        result = subprocess.run(
            [
                "docker", "run",
                "--rm",
                "-v", f"{docker_path}:/sandbox",
                "--workdir", "/sandbox",
                DOCKER_IMAGE,
                "manim", "render",
                "--media_dir", "/sandbox/output",
                "-ql",
                "/sandbox/scene.py"
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )

        # Step 4: Check if it worked
        if result.returncode == 0:
            video_files = glob.glob(
                os.path.join(tmp_dir, "output", "**", "*.mp4"),
                recursive=True
            )

            if video_files:
                video_path = video_files[0]
                os.makedirs("outputs", exist_ok=True)
                final_path = os.path.join("outputs", "animation.mp4")
                shutil.copy(video_path, final_path)

                print(f"[Sandbox] ✅ Success! Video saved to: {final_path}")
                return {
                    "success": True,
                    "video_path": final_path,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                print("[Sandbox] ❌ Compiled but no video file found")
                return {
                    "success": False,
                    "error": "No video file was generated",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        else:
            print(f"[Sandbox] ❌ Compilation failed")
            print(f"[Sandbox] Error: {result.stderr[:500]}")
            return {
                "success": False,
                "error": result.stderr,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        print("[Sandbox] ❌ Timed out")
        return {"success": False, "error": "Rendering timed out after 120 seconds"}

    except Exception as e:
        print(f"[Sandbox] ❌ Unexpected error: {e}")
        return {"success": False, "error": str(e)}

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)