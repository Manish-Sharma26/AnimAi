/**
 * VideoPlayer — Plays the generated Cloudinary video
 * Shows video with controls, download button, and thumbnail fallback.
 */

export default function VideoPlayer({ videoUrl, thumbnailUrl }) {
  if (!videoUrl) return null;

  return (
    <div className="video-player">
      <video
        className="video-player__video"
        src={videoUrl}
        poster={thumbnailUrl || undefined}
        controls
        autoPlay
        playsInline
      />
      <div className="video-player__actions">
        <a
          href={videoUrl}
          download
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn--ghost btn--sm"
        >
          ⬇ Download
        </a>
      </div>
    </div>
  );
}
