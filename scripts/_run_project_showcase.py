"""
Headless runner — AnimAI Studio Project Showcase Video
Generates a video ABOUT the project itself, explaining the multi-agent
AI pipeline that converts natural language → educational Manim animations.
"""
import os, sys, shutil
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import build_plan, run_agent_with_plan

QUERY = (
    "Create a professional educational video that explains how the AnimAI Studio project works. "
    "AnimAI Studio is an AI-powered system that turns plain English descriptions into "
    "professional educational Manim animations with voice narration, automatically.\n\n"

    "SEGMENT 1 — WHAT IS ANIMAI STUDIO (Introduction):\n"
    "Show the title 'AnimAI Studio' with a film clapperboard icon (use a Rectangle with lines). "
    "Define it: AnimAI Studio is an AI-powered multi-agent system that converts natural language "
    "descriptions into fully narrated, professional educational animations. "
    "Show why it matters: Creating educational videos manually takes hours of coding and editing. "
    "AnimAI Studio does it in minutes using AI agents that think like a teacher, plan like a "
    "curriculum designer, and code like an expert animator.\n\n"

    "SEGMENT 2 — HOW THE MULTI-AGENT PIPELINE WORKS (Theory & Analogy):\n"
    "Show a LEFT column with the 5-agent pipeline as a vertical flowchart:\n"
    "  Agent 1: Teacher Agent — Understands the concept, identifies prerequisites, analogies, "
    "and the best way to teach it. Like a professor preparing a lecture.\n"
    "  Agent 2: Planner Agent — Converts the teaching plan into a 5-segment video structure "
    "(Introduction, Theory, Core Animation, User Message, Summary). Like a film director "
    "creating a storyboard.\n"
    "  Agent 3: Coder Agent — Writes actual Manim Python code from the plan, using RAG-retrieved "
    "API patterns. Like a skilled animator who writes code.\n"
    "  Agent 4: Debugger Agent — Automatically detects and fixes compilation errors. "
    "Like a QA engineer who catches bugs.\n"
    "  Agent 5: Voice Engine — Renders speech narration directly inside the animation using "
    "Azure Speech or gTTS. Like a narrator recording a voiceover.\n"
    "Show on the RIGHT column an analogy: Think of it like a film production team — "
    "a teacher writes the script, a director plans the shots, a coder animates the scenes, "
    "a debugger reviews for errors, and a narrator adds the voice.\n\n"

    "SEGMENT 3 — CORE ANIMATION (The Pipeline in Action):\n"
    "This is the main visual. Show a horizontal pipeline diagram with boxes and arrows:\n"
    "  Step 1: Show a text box labeled 'User Prompt' containing 'Explain how gradient descent works'. "
    "An arrow flows to the next box. Show key text: 'Natural Language Input'.\n"
    "  Step 2: Show the prompt going through 'Teacher Agent' (brain icon as a Circle), "
    "which outputs a structured JSON with core_idea, analogy, steps. "
    "Then an arrow to 'Planner Agent' which creates a 5-segment storyboard. "
    "Show key text: 'AI Plans the Video'.\n"
    "  Step 3: AHA MOMENT — Show 'Coder Agent' generating Python code (show a code block "
    "Rectangle with lines of colored text), and if it fails, a red X appears, then "
    "'Debugger Agent' fixes it automatically with a green checkmark. "
    "Show a retry loop arrow (up to 3 attempts). Show key text: 'Self-Healing Code Generation'.\n"
    "  Step 4: Show the code going into a 'Docker Sandbox' box (a container icon as Rectangle), "
    "which outputs a final MP4 video file icon. Show key text: 'Safe Isolated Rendering'.\n\n"

    "SEGMENT 4 — KEY FEATURES (User Message):\n"
    "Show a list of features as bullet points:\n"
    "  Feature 1: RAG-Enhanced — Retrieves real Manim documentation patterns using FAISS vector search.\n"
    "  Feature 2: Self-Healing — Auto-debugs and retries up to 3 times if code fails.\n"
    "  Feature 3: Feedback Learning — Learns from user thumbs-up to improve future generations.\n"
    "  Feature 4: Voice Narration — Azure Speech primary, gTTS fallback, rendered inside Manim.\n"
    "  Feature 5: Docker Sandbox — Safe isolated execution, no risk to host system.\n\n"

    "SEGMENT 5 — SUMMARY:\n"
    "Show a green summary banner with the takeaway: "
    "'AnimAI Studio transforms any topic into a professional narrated animation in minutes, "
    "using a team of AI agents that teach, plan, code, debug, and narrate — automatically.' "
    "End with 'Built with Gemini + Manim + Azure Speech'.\n\n"

    "VISUAL STYLE: Use dark background (#0F0F1A), blue (#4FACFE) for titles, "
    "yellow (#F9CA24) for highlights, green (#6AB04C) for success elements, "
    "red for error indicators. Use smooth animations, arrows between pipeline stages, "
    "and a split-screen layout for Segments 2 and 3. "
    "Make the pipeline diagram the star visual — show data flowing through each agent. "
    "Target audience: developer or educator seeing this project for the first time."
)

OUTPUT_NAME = "animai_showcase_video.mp4"

print("=" * 70)
print("AnimAi Studio — Project Showcase Video (Meta Demo!)")
print("=" * 70)
print(f"\nQuery:\n{QUERY[:400]}...\n")
print("=" * 70)

print("\n[Step 1] Building animation plan...")
plan = build_plan(QUERY)
print(f"  Title   : {plan.get('title', '(none)')}")
segs = plan.get('segments', [])
for s in segs:
    print(f"    • {s.get('type','?')} ({s.get('duration_seconds','?')}s)")

print("\n[Step 2] Running agent pipeline...")
result = run_agent_with_plan(QUERY, plan)

print("\n" + "=" * 70)
print(f"STATUS   : {result.get('status')}")
print(f"ATTEMPTS : {result.get('attempts', '?')}")

if result.get("status") == "success":
    video_path = result.get("video_path", "")
    print(f"VIDEO    : {video_path}")
    print(f"HAS_AUDIO: {result.get('has_audio')}")

    # Copy to named output
    if video_path and os.path.exists(video_path):
        dest = os.path.join("outputs", OUTPUT_NAME)
        shutil.copy(video_path, dest)
        print(f"SAVED AS : {dest}")

    print("\n[SUCCESS] Project showcase video generated!")
    print("Your AnimAI Studio just made a video about itself! 🎬🤖")
else:
    print("\n[FAILED] Error:")
    print((result.get("error", "") or "")[:4000])
    print("\n[FAILED] Last code head:")
    print((result.get("code", "") or "")[:2000])
