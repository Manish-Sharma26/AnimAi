"""
Headless runner — Generate two videos: Gradient Descent + LSTM
"""
import os, sys, shutil, time
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import build_plan, run_agent_with_plan

# ──────────────────────────────────────────────
# VIDEO 1: Gradient Descent
# ──────────────────────────────────────────────
QUERY_GD = (
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

# ──────────────────────────────────────────────
# VIDEO 2: LSTM
# ──────────────────────────────────────────────
QUERY_LSTM = (
    "Teach LSTM (Long Short-Term Memory) networks for beginners. "
    "Include: (1) intuitive theory — why regular RNNs forget and LSTMs remember, "
    "use a conveyor belt analogy for the cell state, "
    "(2) the key components: cell state, forget gate, input gate, output gate, "
    "show how each gate controls information flow with sigmoid and tanh, "
    "(3) a step-by-step walkthrough of one LSTM cell processing a sequence — "
    "show data flowing through the forget gate (what to discard), "
    "input gate (what new info to store), and output gate (what to output), "
    "(4) show how the cell state acts as a 'highway' carrying long-term memory, "
    "(5) end with a clean summary card. "
    "Make it visually beautiful with a dark background, color-coded gates, "
    "smooth animations, and clear labels. Target: Deep Learning beginner."
)

videos = [
    ("Gradient Descent", QUERY_GD),
    ("LSTM", QUERY_LSTM),
]

results = []

for i, (name, query) in enumerate(videos, 1):
    print("\n" + "█" * 70)
    print(f"  VIDEO {i}/2: {name}")
    print("█" * 70)
    print(f"\nQuery:\n{query}\n")

    try:
        print(f"\n[{name}] Step 1: Building animation plan...")
        plan = build_plan(query)
        print(f"  Title   : {plan.get('title', '(none)')}")
        segs = plan.get('segments', [])
        for s in segs:
            print(f"    • {s.get('type','?')} ({s.get('duration_seconds','?')}s)")

        print(f"\n[{name}] Step 2: Running agent pipeline...")
        result = run_agent_with_plan(query, plan)

        print(f"\n[{name}] STATUS: {result.get('status')}")
        print(f"[{name}] ATTEMPTS: {result.get('attempts', '?')}")

        if result.get("status") == "success":
            video_path = result.get('video_path', '')
            print(f"[{name}] VIDEO: {video_path}")
            print(f"[{name}] HAS_AUDIO: {result.get('has_audio')}")

            # Copy to outputs folder with a readable name
            safe_name = name.lower().replace(" ", "_")
            dest = os.path.join("outputs", f"{safe_name}_video.mp4")
            if video_path and os.path.exists(video_path):
                os.makedirs("outputs", exist_ok=True)
                shutil.copy2(video_path, dest)
                print(f"[{name}] COPIED TO: {dest}")

            results.append({"name": name, "status": "success", "path": dest})
        else:
            print(f"\n[{name}] FAILED:")
            print((result.get("error", "") or "")[:3000])
            results.append({"name": name, "status": "failed", "error": (result.get("error", "") or "")[:500]})
    except Exception as e:
        print(f"\n[{name}] EXCEPTION: {e}")
        results.append({"name": name, "status": "exception", "error": str(e)})

# ──────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
for r in results:
    status = r["status"].upper()
    if status == "SUCCESS":
        print(f"  ✅ {r['name']}: {r.get('path', 'N/A')}")
    else:
        print(f"  ❌ {r['name']}: {r.get('error', 'unknown')[:200]}")
print("=" * 70)
