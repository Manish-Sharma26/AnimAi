/**
 * Gallery Page — User's animation history
 * 
 * Shows a grid of the user's own animations with:
 * - Cloudinary thumbnails
 * - Status badges
 * - Share toggle (public/private)
 * - Delete button
 * - Click to navigate to Studio page
 */

import { useState, useEffect } from "react";
import api from "../services/api";
import AnimationCard from "../components/AnimationCard";

export default function Gallery() {
  const [animations, setAnimations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });

  const loadAnimations = async (page = 1) => {
    setLoading(true);
    try {
      const { data } = await api.get(`/animations?page=${page}&limit=12`);
      setAnimations(data.animations);
      setPagination(data.pagination);
    } catch (err) {
      console.error("Failed to load animations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnimations();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this animation? This cannot be undone.")) return;
    try {
      await api.delete(`/animations/${id}`);
      setAnimations((prev) => prev.filter((a) => a._id !== id));
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleToggleShare = async (id) => {
    try {
      const { data } = await api.patch(`/animations/${id}/share`);
      setAnimations((prev) =>
        prev.map((a) => (a._id === id ? { ...a, isPublic: data.isPublic } : a))
      );
    } catch (err) {
      console.error("Share toggle failed:", err);
    }
  };

  return (
    <div className="page fade-in">
      <div className="page__header">
        <h1 className="page__title">My Gallery</h1>
        <p className="page__subtitle">
          {pagination.total} animation{pagination.total !== 1 ? "s" : ""} created
        </p>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", paddingTop: "3rem" }}>
          <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
        </div>
      ) : animations.length === 0 ? (
        <div className="gallery__empty">
          <p>No animations yet</p>
          <p className="gallery__empty-sub">
            Go to the Home page and create your first animation!
          </p>
        </div>
      ) : (
        <>
          <div className="gallery__grid">
            {animations.map((anim) => (
              <AnimationCard
                key={anim._id}
                animation={anim}
                showActions={true}
                onDelete={handleDelete}
                onToggleShare={handleToggleShare}
              />
            ))}
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="gallery__pagination">
              {Array.from({ length: pagination.pages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  className={`btn btn--sm ${p === pagination.page ? "btn--primary" : "btn--ghost"}`}
                  onClick={() => loadAnimations(p)}
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
