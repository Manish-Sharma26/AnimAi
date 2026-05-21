/**
 * Explore Page — Public community gallery
 * 
 * Shows all public animations shared by users (no auth required to view).
 * Read-only — no delete or share buttons.
 */

import { useState, useEffect } from "react";
import api from "../services/api";
import AnimationCard from "../components/AnimationCard";

export default function Explore() {
  const [animations, setAnimations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });

  const loadPublic = async (page = 1) => {
    setLoading(true);
    try {
      const { data } = await api.get(`/gallery?page=${page}&limit=20`);
      setAnimations(data.animations);
      setPagination(data.pagination);
    } catch (err) {
      console.error("Failed to load public gallery:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPublic();
  }, []);

  return (
    <div className="page fade-in">
      <div className="page__header">
        <h1 className="page__title">Explore</h1>
        <p className="page__subtitle">
          Discover animations shared by the community
        </p>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", paddingTop: "3rem" }}>
          <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
        </div>
      ) : animations.length === 0 ? (
        <div className="gallery__empty">
          <p>No public animations yet</p>
          <p className="gallery__empty-sub">
            Be the first to share an animation with the community!
          </p>
        </div>
      ) : (
        <>
          <div className="gallery__grid">
            {animations.map((anim) => (
              <AnimationCard
                key={anim._id}
                animation={anim}
                showActions={false}
              />
            ))}
          </div>

          {pagination.pages > 1 && (
            <div className="gallery__pagination">
              {Array.from({ length: pagination.pages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  className={`btn btn--sm ${p === pagination.page ? "btn--primary" : "btn--ghost"}`}
                  onClick={() => loadPublic(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
