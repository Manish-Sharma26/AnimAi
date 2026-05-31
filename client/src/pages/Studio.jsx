/**
 * Studio Page — The core animation generation experience
 * 
 * Flow:
 * 1. Shows the prompt (passed via URL state or loaded from API)
 * 2. Click "Generate Plan" → calls Python AI to create animation plan
 * 3. User reviews and approves the plan
 * 4. Click "Generate Video" → queues job, shows progress
 * 5. Socket.io pushes real-time progress: planning → coding → compiling → uploading → complete
 * 6. On complete → video player appears with Cloudinary URL
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../services/api";
import useSocket from "../hooks/useSocket";
import ProgressTracker from "../components/ProgressTracker";
import VideoPlayer from "../components/VideoPlayer";

export default function Studio() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { socket, connected } = useSocket();

  const [animation, setAnimation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Plan state
  const [planLoading, setPlanLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const [planApproved, setPlanApproved] = useState(false);

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState({ step: null, percent: 0, message: "" });
  const [jobId, setJobId] = useState(null);

  // Load animation data
  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const { data } = await api.get(`/animations/${id}`);
        setAnimation(data.animation);

        // If animation already has a plan, show it
        if (data.animation.plan && Object.keys(data.animation.plan).length > 0) {
          setPlan(data.animation.plan);
          if (["generating", "success", "failed", "approved"].includes(data.animation.status)) {
            setPlanApproved(true);
          }
        }

        // If already generating, resume tracking
        if (data.animation.status === "generating") {
          setGenerating(true);
        }
      } catch (err) {
        setError("Animation not found");
      } finally {
        setLoading(false);
      }
    };

    if (id) loadAnimation();
  }, [id]);

  // ── Socket.io listeners — PRIMARY update mechanism ─────────────────────────
  useEffect(() => {
    if (!socket || !id) return;

    const handleProgress = (data) => {
      if (data.animationId === id) {
        setProgress({
          step: data.step,
          percent: data.percent,
          message: data.message || "",
        });
      }
    };

    const handleComplete = (data) => {
      if (data.animationId === id) {
        setProgress({ step: "complete", percent: 100, message: "Your video is ready!" });
        setGenerating(false);
        // Reload animation to get videoUrl
        api.get(`/animations/${id}`).then(({ data }) => {
          setAnimation(data.animation);
        });
      }
    };

    const handleFailed = (data) => {
      if (data.animationId === id) {
        setGenerating(false);
        setError(data.error || "Generation failed");
        setProgress({ step: null, percent: 0, message: "" });
        api.get(`/animations/${id}`).then(({ data }) => {
          setAnimation(data.animation);
        });
      }
    };

    const handleRetrying = (data) => {
      if (data.animationId === id) {
        setProgress({
          step: "compiling",
          percent: 10,
          message: `Attempt ${data.attempt} failed — retrying (${data.attempt}/${data.maxAttempts})...`,
        });
        // Keep generating=true so the progress UI stays visible
      }
    };

    socket.on("job:progress", handleProgress);
    socket.on("job:complete", handleComplete);
    socket.on("job:failed", handleFailed);
    socket.on("job:retrying", handleRetrying);

    return () => {
      socket.off("job:progress", handleProgress);
      socket.off("job:complete", handleComplete);
      socket.off("job:failed", handleFailed);
      socket.off("job:retrying", handleRetrying);
    };
  }, [socket, id]);

  // ── Polling fallback (only if socket disconnects) ──────────────────────────
  useEffect(() => {
    if (!generating || !jobId) return;
    // Only poll if socket is disconnected
    if (connected) return;

    const interval = setInterval(async () => {
      try {
        const { data } = await api.get(`/animations/jobs/${jobId}`);
        if (data.state === "completed") {
          setGenerating(false);
          setProgress({ step: "complete", percent: 100, message: "Your video is ready!" });
          const { data: animData } = await api.get(`/animations/${id}`);
          setAnimation(animData.animation);
          clearInterval(interval);
        } else if (data.state === "failed") {
          setGenerating(false);
          setError(data.failedReason || "Generation failed");
          clearInterval(interval);
        }
      } catch {
        // Ignore polling errors
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [generating, jobId, id, connected]);

  // Generate plan via Python AI service
  const handleGeneratePlan = async () => {
    setPlanLoading(true);
    setError("");

    try {
      const { data } = await api.post(`/animations/${id}/plan`);
      setPlan(data.plan);
      setAnimation(data.animation);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to generate plan — is the Python service running?");
    } finally {
      setPlanLoading(false);
    }
  };

  // Approve plan
  const handleApprovePlan = async () => {
    setPlanApproved(true);
    try {
      await api.put(`/animations/${id}`, { plan, status: "approved" });
      setAnimation((prev) => ({ ...prev, status: "approved" }));
    } catch (err) {
      console.error("Failed to save plan approval:", err);
    }
  };

  // Generate video
  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    setProgress({ step: "planning", percent: 5, message: "Queuing generation..." });

    try {
      const { data } = await api.post("/animations/generate", { animationId: id });
      setJobId(data.jobId);
    } catch (err) {
      setGenerating(false);
      setError(err.response?.data?.message || "Failed to start generation");
      setProgress({ step: null, percent: 0, message: "" });
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="page" style={{ display: "flex", justifyContent: "center", paddingTop: "4rem" }}>
        <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
      </div>
    );
  }

  if (error && !animation) {
    return (
      <div className="page fade-in">
        <div className="studio__error">
          <h2>Something went wrong</h2>
          <p>{error}</p>
          <button className="btn btn--primary" onClick={() => navigate("/")}>
            Go Home
          </button>
        </div>
      </div>
    );
  }

  const isSuccess = animation?.status === "success";
  const isFailed = animation?.status === "failed";
  const hasPlan = plan && Object.keys(plan).length > 0;

  return (
    <div className="page fade-in">
      <div className="studio">
        {/* Header */}
        <div className="studio__header">
          <button className="btn btn--ghost btn--sm" onClick={() => navigate("/")}>
            ← Back
          </button>
          <div className="studio__status-badge" data-status={animation?.status}>
            {animation?.status}
          </div>
        </div>

        {/* Prompt */}
        <div className="studio__prompt-card">
          <h2 className="studio__prompt-label">Your Prompt</h2>
          <p className="studio__prompt-text">{animation?.prompt}</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="auth-card__error" style={{ marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        {/* ──────── Step 1: Generate Plan ──────── */}
        {!hasPlan && !planLoading && !isSuccess && !generating && (
          <button
            className="btn btn--primary btn--lg"
            onClick={handleGeneratePlan}
            style={{ width: "100%", marginBottom: "2rem" }}
          >
            🧠 Generate Animation Plan
          </button>
        )}

        {/* Plan Loading */}
        {planLoading && (
          <div className="plan-loading" style={{ marginBottom: "2rem" }}>
            <div className="plan-loading__inner">
              <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
              <p className="plan-loading__text">
                AI is analyzing your prompt and creating the animation plan...
              </p>
            </div>
          </div>
        )}

        {/* ──────── Step 2: Review Plan ──────── */}
        {hasPlan && !planApproved && !generating && !isSuccess && (
          <div className="plan-review" style={{ marginBottom: "2rem" }}>
            <h3 className="plan-review__title">📋 Animation Plan</h3>
            <p className="plan-review__subtitle">
              Review the AI-generated plan before generating the video
            </p>

            <div className="plan-review__card">
              {plan.title && (
                <div className="plan-review__field">
                  <span className="plan-review__label">Title</span>
                  <span className="plan-review__value">{plan.title}</span>
                </div>
              )}
              {plan.visual_style && (
                <div className="plan-review__field">
                  <span className="plan-review__label">Visual Style</span>
                  <span className="plan-review__value">{plan.visual_style}</span>
                </div>
              )}
              {plan.duration_seconds && (
                <div className="plan-review__field">
                  <span className="plan-review__label">Estimated Duration</span>
                  <span className="plan-review__value">{plan.duration_seconds}s</span>
                </div>
              )}
              {plan.opening_scene && (
                <div className="plan-review__field">
                  <span className="plan-review__label">Opening Scene</span>
                  <span className="plan-review__value">{plan.opening_scene}</span>
                </div>
              )}
              {plan.steps && plan.steps.length > 0 && (
                <div className="plan-review__field">
                  <span className="plan-review__label">Steps</span>
                  <ol className="plan-review__steps">
                    {plan.steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
              {plan.full_script && plan.full_script.length > 0 && (
                <div className="plan-review__field">
                  <span className="plan-review__label">Script</span>
                  <ol className="plan-review__steps">
                    {plan.full_script.map((beat, i) => (
                      <li key={i}>{beat}</li>
                    ))}
                  </ol>
                </div>
              )}
              {plan.closing_scene && (
                <div className="plan-review__field">
                  <span className="plan-review__label">Closing Scene</span>
                  <span className="plan-review__value">{plan.closing_scene}</span>
                </div>
              )}

              {/* Teacher Explanation */}
              {plan.teacher_explanation && (
                <div className="plan-review__teacher">
                  <h4>🧑‍🏫 Teacher's Explanation</h4>
                  {plan.teacher_explanation.core_idea && (
                    <p><strong>Core Idea:</strong> {plan.teacher_explanation.core_idea}</p>
                  )}
                  {plan.teacher_explanation.analogy && (
                    <p><strong>Analogy:</strong> {plan.teacher_explanation.analogy}</p>
                  )}
                  {plan.teacher_explanation.takeaway && (
                    <p><strong>Takeaway:</strong> {plan.teacher_explanation.takeaway}</p>
                  )}
                </div>
              )}
            </div>

            <div className="plan-review__actions">
              <button
                className="btn btn--primary btn--lg"
                onClick={handleApprovePlan}
                style={{ flex: 1 }}
              >
                ✅ Approve Plan & Generate Video
              </button>
              <button
                className="btn btn--ghost"
                onClick={handleGeneratePlan}
                style={{ flex: 0 }}
              >
                🔄 Re-plan
              </button>
            </div>
          </div>
        )}

        {/* ──────── Step 3: Generate Video ──────── */}
        {planApproved && !isSuccess && !generating && (
          <button
            className="btn btn--primary btn--lg"
            onClick={handleGenerate}
            style={{ width: "100%", marginBottom: "2rem" }}
          >
            🎬 Generate Animation Video
          </button>
        )}

        {/* Progress Tracker + Live Status */}
        {generating && (
          <div style={{ marginBottom: "2rem" }}>
            <ProgressTracker currentStep={progress.step} percent={progress.percent} />
            {progress.message && (
              <p className="studio__progress-msg">
                {progress.message}
              </p>
            )}
            {!connected && (
              <p className="studio__progress-msg" style={{ color: "var(--warning)", fontSize: "0.75rem" }}>
                ⚠ Live connection lost — using fallback polling
              </p>
            )}
          </div>
        )}

        {/* Video Player */}
        {isSuccess && animation?.videoUrl && (
          <div style={{ marginBottom: "2rem" }}>
            <VideoPlayer
              videoUrl={animation.videoUrl}
              thumbnailUrl={animation.thumbnailUrl}
            />
          </div>
        )}

        {/* Stats */}
        {isSuccess && (
          <div className="studio__stats">
            {animation.videoDuration && (
              <div className="studio__stat">
                <span className="studio__stat-label">Duration</span>
                <span className="studio__stat-value">
                  {Math.round(animation.videoDuration)}s
                </span>
              </div>
            )}
            {animation.videoSizeBytes && (
              <div className="studio__stat">
                <span className="studio__stat-label">Size</span>
                <span className="studio__stat-value">
                  {(animation.videoSizeBytes / 1024 / 1024).toFixed(1)}MB
                </span>
              </div>
            )}
            {animation.attempts && (
              <div className="studio__stat">
                <span className="studio__stat-label">Attempts</span>
                <span className="studio__stat-value">{animation.attempts}</span>
              </div>
            )}
            {animation.hasAudio && (
              <div className="studio__stat">
                <span className="studio__stat-label">Audio</span>
                <span className="studio__stat-value">Yes</span>
              </div>
            )}
          </div>
        )}

        {/* Re-generate */}
        {(isSuccess || isFailed) && (
          <button
            className="btn btn--ghost"
            onClick={handleGenerate}
            style={{ width: "100%", marginTop: "1rem" }}
          >
            🔄 Re-generate
          </button>
        )}
      </div>
    </div>
  );
}
