"""
Headless runner — Gradient Descent Beginner ML video
Rich prompt: theory + solved example + data table, beginner-friendly.
"""
import os, sys
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import build_plan, run_agent_with_plan

QUERY = (
    "Teach gradient descent for complete beginners in machine learning. "
    "Include: (1) intuitive theory using a ball rolling downhill analogy, "
    "(2) the maths: cost function J = (1/2m) * sum of (predicted - actual)^2, "
    "learning rate alpha, update rule theta = theta - alpha * gradient, "
    "(3) a fully worked numerical example — use a small dataset table with columns: "
    "x (Hours Studied), y (Test Score), predicted, error, squared_error — "
    "show 3 data points (1h->52, 2h->74, 3h->91), start with theta=0, "
    "do 2 gradient descent steps and show the theta value updating each time, "
    "(4) visualise the cost function as a parabola curve and show the ball moving "
    "toward the minimum as theta updates, "
    "(5) end with a clean summary card. "
    "Make it visually beautiful with a dark background, color-coded equations, "
    "animated tables, and smooth transitions. Target: ML beginner with no prior knowledge."
)

print("=" * 70)
print("AnimAi Studio — Gradient Descent Beginner Video")
print("=" * 70)
print(f"\nQuery:\n{QUERY}\n")
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
    print(f"VIDEO    : {result.get('video_path')}")
    print(f"HAS_AUDIO: {result.get('has_audio')}")
    print("\n[SUCCESS] Video generated successfully!")
else:
    print("\n[FAILED] Error:")
    print((result.get("error", "") or "")[:4000])
    print("\n[FAILED] Last code head:")
    print((result.get("code", "") or "")[:2000])
