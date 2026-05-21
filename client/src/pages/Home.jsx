/**
 * Home Page — Prompt input with example buttons
 * Creates an animation via API and navigates to Studio page.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const EXAMPLE_PROMPTS = [
  "Explain how binary search works",
  "What is gradient descent?",
  "How does a Redis queue work?",
  "Explain the concept of recursion",
  "How do neural networks learn?",
  "What is the Big O notation?",
];

export default function Home() {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");

    try {
      const { data } = await api.post("/animations", { prompt: prompt.trim() });
      navigate(`/studio/${data.animation.id}`);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to create animation");
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && prompt.trim()) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="page fade-in">
      <div className="home">
        <div className="home__hero">
          <h1 className="home__title">
            Turn ideas into{" "}
            <span className="home__title-accent">animated videos</span>
          </h1>
          <p className="home__subtitle">
            Type any topic and our AI will create a beautiful animated
            explanation video — complete with voiceover.
          </p>
        </div>

        <div className="home__input-area">
          <textarea
            id="prompt-input"
            className="input home__textarea"
            placeholder="Describe what you want to explain..."
            value={prompt}
            onChange={(e) => { setPrompt(e.target.value); setError(""); }}
            onKeyDown={handleKeyDown}
          />

          {error && (
            <div className="auth-card__error" style={{ marginTop: "0.75rem" }}>
              {error}
            </div>
          )}

          <button
            id="generate-btn"
            className="btn btn--primary btn--lg home__generate-btn"
            disabled={!prompt.trim() || loading}
            onClick={handleGenerate}
          >
            {loading ? <span className="spinner" /> : "🎬 Create Animation"}
          </button>

          <div className="home__examples">
            <p className="home__examples-label">Try an example:</p>
            <div className="home__examples-grid">
              {EXAMPLE_PROMPTS.map((p) => (
                <button
                  key={p}
                  className="btn btn--ghost btn--sm"
                  onClick={() => setPrompt(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
