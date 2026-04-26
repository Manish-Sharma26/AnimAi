"""
Headless runner — LSTM (Long Short-Term Memory) Deep Learning video
Covers: What is LSTM, Why we need it, Key terminologies & gates, How it works with diagram.
"""
import os, sys
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import build_plan, run_agent_with_plan

QUERY = (
    "Create a comprehensive educational video on LSTM (Long Short-Term Memory) networks for deep learning beginners. "
    "The video MUST cover these topics in order:\n\n"
    
    "SEGMENT 1 - WHAT IS LSTM:\n"
    "Start by explaining what LSTM is — a special type of Recurrent Neural Network (RNN) "
    "designed to learn long-term dependencies in sequential data. "
    "Show that LSTM stands for Long Short-Term Memory. "
    "Mention it was introduced to solve problems vanilla RNNs face.\n\n"
    
    "SEGMENT 2 - WHY WE NEED LSTM (The Problem with Vanilla RNNs):\n"
    "Explain the vanishing gradient problem in standard RNNs — "
    "as sequences get longer, gradients shrink exponentially during backpropagation, "
    "making it impossible for RNNs to learn long-range dependencies. "
    "Use a visual analogy: imagine passing a message through a long chain of people — "
    "by the end, the message is completely distorted. "
    "Show a simple diagram of an unrolled RNN with gradients shrinking at each time step.\n\n"
    
    "SEGMENT 3 - KEY TERMINOLOGIES WITH FUNCTIONS (Core Animation):\n"
    "This is the main animation segment. Show a clear LSTM cell architecture diagram with these components:\n"
    "  (a) Cell State (C_t): The memory highway — a horizontal line running through the top of the cell. "
    "It carries information across time steps with minimal changes. Like a conveyor belt.\n"
    "  (b) Forget Gate: Uses sigmoid function σ(W_f · [h_{t-1}, x_t] + b_f). "
    "Decides what information to THROW AWAY from the cell state. Output is between 0 (forget) and 1 (keep).\n"
    "  (c) Input Gate: Uses sigmoid σ(W_i · [h_{t-1}, x_t] + b_i) to decide WHAT to update, "
    "and tanh(W_C · [h_{t-1}, x_t] + b_C) to create candidate values. Together they update the cell state.\n"
    "  (d) Output Gate: Uses sigmoid σ(W_o · [h_{t-1}, x_t] + b_o) to decide what to output, "
    "then multiplies by tanh(C_t) to produce the hidden state h_t.\n"
    "  (e) Hidden State (h_t): The output of the LSTM cell at each time step.\n"
    "  (f) Sigmoid (σ): Squashes values between 0 and 1 — acts as a gate controller.\n"
    "  (g) Tanh: Squashes values between -1 and 1 — regulates information flow.\n"
    "Show each gate lighting up as you explain it, with arrows showing data flow.\n\n"
    
    "SEGMENT 4 - HOW LSTM WORKS (Step-by-Step with Diagram):\n"
    "Walk through one time step of an LSTM cell:\n"
    "  Step 1: Previous hidden state h_{t-1} and current input x_t enter the cell.\n"
    "  Step 2: Forget gate decides what to remove from old cell state.\n"
    "  Step 3: Input gate decides what new information to add.\n"
    "  Step 4: Cell state is updated: C_t = f_t * C_{t-1} + i_t * C̃_t\n"
    "  Step 5: Output gate produces new hidden state: h_t = o_t * tanh(C_t)\n"
    "Show data flowing through the cell with colored arrows — "
    "red for forget, green for input/add, blue for output.\n\n"
    
    "SEGMENT 5 - SUMMARY:\n"
    "End with a clean summary card listing: "
    "LSTM solves the vanishing gradient problem. "
    "Three gates (Forget, Input, Output) control information flow. "
    "Cell state acts as long-term memory. "
    "Hidden state acts as short-term/working memory.\n\n"
    
    "VISUAL STYLE: Use a dark background (#0F0F1A), color-coded components "
    "(blue for cell state, red for forget gate, green for input gate, purple for output gate), "
    "smooth animations with arrows showing data flow, and clear labeled diagrams. "
    "Target audience: ML/DL beginner with basic neural network knowledge."
)

print("=" * 70)
print("AnimAi Studio — LSTM Deep Learning Video")
print("=" * 70)
print(f"\nQuery:\n{QUERY[:300]}...\n")
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
