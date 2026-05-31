"""
AnimAI Studio — FastAPI AI Microservice

This is a THIN wrapper around the existing Python pipeline.
It exposes three endpoints that the Node.js server calls via HTTP:

  POST /plan      → build_plan(prompt)
  POST /generate  → run_agent_with_plan(prompt, plan)
  POST /revise    → apply_user_changes(prompt, plan, code, change_request)
  GET  /health    → {"status": "ok"}

The agent/, sandbox/, and rag/ directories remain 100% untouched.
This file just imports and calls their functions via HTTP.

INTERVIEW TIP:
"The FastAPI service is a 50-line wrapper. All the AI logic — LLM calls,
 Manim rendering, FAISS retrieval — lives in the existing Python modules.
 FastAPI just exposes them as HTTP endpoints so the Node.js API can call
 them. This is the microservice boundary — Python handles compute-heavy
 AI work, Node handles I/O-heavy API work."
"""

import sys
import os
import traceback

# Fix Windows cp1252 encoding crash — agent modules print emoji characters
# which can't be encoded by the default Windows console encoding.
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Add project root to Python path so we can import agent/, sandbox/, rag/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from agent.orchestrator import build_plan, run_agent_with_plan, apply_user_changes

app = FastAPI(
    title="AnimAI Pipeline Service",
    description="AI microservice wrapping the animation generation pipeline",
    version="1.0.0",
)


# ── Request Models ────────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    prompt: str

class GenerateRequest(BaseModel):
    prompt: str
    plan: dict

class ReviseRequest(BaseModel):
    prompt: str
    plan: dict
    code: str
    change_request: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "AnimAI Pipeline"}


@app.post("/plan")
def create_plan(req: PlanRequest):
    """Generate a structured animation plan from a user prompt."""
    try:
        result = build_plan(req.prompt)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
def generate_video(req: GenerateRequest):
    """Run the full AI pipeline: plan → code → render → video."""
    try:
        result = run_agent_with_plan(req.prompt, req.plan)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/revise")
def revise_video(req: ReviseRequest):
    """Apply user changes to existing code and re-render."""
    try:
        result = apply_user_changes(
            req.prompt,
            req.plan,
            req.code,
            req.change_request,
        )
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
