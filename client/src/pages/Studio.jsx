/**
 * Studio Page — The core animation generation experience
 * 
 * Flow:
 * 1. Shows the prompt (passed via URL state or loaded from API)
 * 2. Click "Generate Video" → queues job, shows progress
 * 3. Socket.io events update the progress tracker in real-time
 * 4. On complete → video player appears with Cloudinary URL
 * 5. User can provide feedback or request revisions
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../services/api";
import useSocket from "../hooks/useSocket";
import ProgressTracker from "../components/ProgressTracker";
import VideoPlayer from "../components/VideoPlayer";

export default function Studio() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { socket } = useSocket();

  const [animation, setAnimation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState({ step: null, percent: 0 });
  const [jobId, setJobId] = useState(null);

  // Feedback
  const [revision, setRevision] = useState("");

  // Load animation data
  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const { data } = await api.get(`/animations/${id}`);
        setAnimation(data.animation);

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

  // Socket.io event listeners
  useEffect(() => {
    if (!socket || !id) return;

    const handleProgress = (data) => {
      if (data.animationId === id) {
        setProgress({ step: data.step, percent: data.percent });
      }
    };

    const handleComplete = (data) => {
      if (data.animationId === id) {
        setProgress({ step: "complete", percent: 100 });
        setGenerating(false);
        // Reload animation to get updated videoUrl
        api.get(`/animations/${id}`).then(({ data }) => {
          setAnimation(data.animation);
        });
      }
    };

    const handleFailed = (data) => {
      if (data.animationId === id) {
        setGenerating(false);
        setError(data.error || "Generation failed");
        setProgress({ step: null, percent: 0 });
      }
    };

    socket.on("job:progress", handleProgress);
    socket.on("job:complete", handleComplete);
    socket.on("job:failed", handleFailed);

    return () => {
      socket.off("job:progress", handleProgress);
      socket.off("job:complete", handleComplete);
      socket.off("job:failed", handleFailed);
    };
  }, [socket, id]);

  // Generate video
  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    setProgress({ step: "planning", percent: 10 });

    try {
      const { data } = await api.post("/animations/generate", { animationId: id });
      setJobId(data.jobId);
    } catch (err) {
      setGenerating(false);
      setError(err.response?.data?.message || "Failed to start generation");
      setProgress({ step: null, percent: 0 });
    }
  };

  // Poll for status (fallback if Socket.io disconnects)
  useEffect(() => {
    if (!generating || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const { data } = await api.get(`/animations/jobs/${jobId}`);
        if (data.state === "completed") {
          setGenerating(false);
          setProgress({ step: "complete", percent: 100 });
          const { data: animData } = await api.get(`/animations/${id}`);
          setAnimation(animData.animation);
          clearInterval(interval);
        } else if (data.state === "failed") {
          setGenerating(false);
          setError("Generation failed");
          clearInterval(interval);
        }
      } catch {
        // ignore polling errors
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [generating, jobId, id]);

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

        {/* Generate Button (only if not yet generated) */}
        {!isSuccess && !generating && (
          <button
            className="btn btn--primary btn--lg"
            onClick={handleGenerate}
            style={{ width: "100%", marginBottom: "2rem" }}
          >
            🎬 Generate Animation Video
          </button>
        )}

        {/* Progress Tracker */}
        {generating && (
          <div style={{ marginBottom: "2rem" }}>
            <ProgressTracker currentStep={progress.step} percent={progress.percent} />
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
