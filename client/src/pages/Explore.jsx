/**
 * Explore Page — Public community gallery
 * 
 * Shows all public animations shared by users (no auth required to view).
 * Clicking a card opens a premium video modal with play button overlay.
 */

import { useState, useEffect } from "react";
import api from "../services/api";
import AnimationCard from "../components/AnimationCard";

export default function Explore() {
  const [animations, setAnimations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  const [selectedAnim, setSelectedAnim] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);

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

  const handleCardClick = async (anim) => {
    if (anim.videoUrl) {
      setSelectedAnim(anim);
      return;
    }
    setModalLoading(true);
    try {
      const { data } = await api.get(`/gallery/${anim._id}`);
      setSelectedAnim(data.animation);
    } catch (err) {
      console.error("Failed to load animation:", err);
    } finally {
      setModalLoading(false);
    }
  };

  const closeModal = () => {
    setSelectedAnim(null);
  };

  // Close modal on Escape key
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") closeModal();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
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
                onCardClick={handleCardClick}
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

      {/* Video Modal */}
      {(selectedAnim || modalLoading) && (
        <div className="explore-modal-overlay" onClick={closeModal}>
          <div className="explore-modal" onClick={(e) => e.stopPropagation()}>
            {/* Close button */}
            <button className="explore-modal__close" onClick={closeModal}>
              ✕
            </button>

            {modalLoading ? (
              <div className="explore-modal__loading">
                <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
              </div>
            ) : (
              <>
                {/* Video */}
                <div className="explore-modal__video-wrap">
                  <video
                    className="explore-modal__video"
                    src={selectedAnim?.videoUrl}
                    poster={selectedAnim?.thumbnailUrl || undefined}
                    controls
                    autoPlay
                    playsInline
                  />
                </div>

                {/* Info Bar */}
                <div className="explore-modal__info">
                  <div className="explore-modal__info-left">
                    <p className="explore-modal__prompt">{selectedAnim?.prompt}</p>
                    <div className="explore-modal__meta">
                      {selectedAnim?.userId?.username && (
                        <span className="explore-modal__author">
                          <span className="explore-modal__avatar">
                            {selectedAnim.userId.username.charAt(0).toUpperCase()}
                          </span>
                          @{selectedAnim.userId.username}
                        </span>
                      )}
                      {selectedAnim?.videoDuration && (
                        <span className="explore-modal__duration">
                          🕐 {Math.round(selectedAnim.videoDuration)}s
                        </span>
                      )}
                      {selectedAnim?.videoSizeBytes && (
                        <span className="explore-modal__size">
                          📦 {(selectedAnim.videoSizeBytes / 1024 / 1024).toFixed(1)}MB
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="explore-modal__info-right">
                    <a
                      href={selectedAnim?.videoUrl}
                      download
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn--primary btn--sm"
                    >
                      ⬇ Download
                    </a>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
