/**
 * AnimationCard — Reusable card for Gallery/Explore grids
 * 
 * Shows thumbnail, title, status, duration, and action buttons.
 */

import { useNavigate } from "react-router-dom";

export default function AnimationCard({
  animation,
  showActions = false,
  onDelete,
  onToggleShare,
  onCardClick,
}) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onCardClick) {
      onCardClick(animation);
    } else {
      navigate(`/studio/${animation._id}`);
    }
  };
  const status = animation.status;
  const prompt = animation.prompt || "Untitled";
  const truncatedPrompt = prompt.length > 80 ? prompt.slice(0, 80) + "..." : prompt;
  const duration = animation.videoDuration
    ? `${Math.round(animation.videoDuration)}s`
    : null;
  const date = new Date(animation.createdAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  const author = animation.userId?.username || null;

  return (
    <div
      className="anim-card"
      onClick={handleClick}
    >
      {/* Thumbnail */}
      <div className="anim-card__thumb">
        {animation.thumbnailUrl ? (
          <img
            src={animation.thumbnailUrl}
            alt={truncatedPrompt}
            loading="lazy"
          />
        ) : (
          <div className="anim-card__thumb-placeholder">
            <span>🎬</span>
          </div>
        )}

        {/* Status badge */}
        <div className="anim-card__badge" data-status={status}>
          {status}
        </div>

        {/* Duration overlay */}
        {duration && <div className="anim-card__duration">{duration}</div>}
      </div>

      {/* Info */}
      <div className="anim-card__body">
        <p className="anim-card__title">{truncatedPrompt}</p>
        <div className="anim-card__meta">
          {author && <span className="anim-card__author">@{author}</span>}
          <span className="anim-card__date">{date}</span>
        </div>
      </div>

      {/* Actions (Gallery only) */}
      {showActions && (
        <div className="anim-card__actions" onClick={(e) => e.stopPropagation()}>
          <button
            className={`btn btn--sm ${animation.isPublic ? "btn--primary" : "btn--ghost"}`}
            onClick={() => onToggleShare?.(animation._id)}
            title={animation.isPublic ? "Make private" : "Share publicly"}
          >
            {animation.isPublic ? "🌐 Public" : "🔒 Private"}
          </button>
          <button
            className="btn btn--danger btn--sm"
            onClick={() => onDelete?.(animation._id)}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}
