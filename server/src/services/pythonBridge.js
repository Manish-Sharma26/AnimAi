/**
 * Python Bridge — HTTP calls from Node.js to FastAPI
 * 
 * This is how the two backends communicate:
 *   Node.js (Express) ──HTTP──▶ Python (FastAPI)
 * 
 * WHY AXIOS AND NOT fetch()?
 * - Built-in timeout support
 * - Automatic JSON parsing
 * - Better error handling (throws on 4xx/5xx)
 * - Request/response interceptors (useful for logging)
 * 
 * TIMEOUT VALUES:
 * - /plan:     60s  (LLM call to generate plan)
 * - /generate: 300s (LLM + Manim render + audio = up to 5 min)
 * - /revise:   300s (same as generate)
 */

const axios = require("axios");
const config = require("../config/env");

const pythonAPI = axios.create({
  baseURL: config.PYTHON_API_URL,
  headers: { "Content-Type": "application/json" },
});

// Log all requests to Python service
pythonAPI.interceptors.request.use((req) => {
  console.log(`[PythonBridge] → ${req.method.toUpperCase()} ${req.baseURL}${req.url}`);
  return req;
});

async function createPlan(prompt) {
  const { data } = await pythonAPI.post("/plan", { prompt }, { timeout: 120000 });
  return data;
}

async function generateVideo(prompt, plan, animationId) {
  const { data } = await pythonAPI.post("/generate", { prompt, plan, animation_id: animationId }, { timeout: 300000 });
  return data;
}

async function reviseVideo(prompt, plan, code, changeRequest) {
  const { data } = await pythonAPI.post("/revise", {
    prompt,
    plan,
    code,
    change_request: changeRequest,
  }, { timeout: 300000 });
  return data;
}

async function checkHealth() {
  const { data } = await pythonAPI.get("/health", { timeout: 5000 });
  return data;
}

module.exports = { createPlan, generateVideo, reviseVideo, checkHealth };
