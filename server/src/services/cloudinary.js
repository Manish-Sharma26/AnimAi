/**
 * Cloudinary Service — Upload, delete, and manage video assets
 * 
 * WHY CLOUDINARY?
 * - CDN delivery — videos load fast from edge servers worldwide
 * - Auto-transcoding — converts to web-optimized formats
 * - Thumbnail generation — auto-generates poster images
 * - Transformations — resize, crop, add overlays via URL params
 * - Free tier — 25GB storage, 25GB bandwidth/month
 * 
 * HOW IT WORKS:
 * 1. Worker generates video locally (via Python pipeline)
 * 2. This service uploads the .mp4 to Cloudinary
 * 3. Cloudinary returns a secure URL + public_id
 * 4. We store the URL in MongoDB (Animation model)
 * 5. Frontend loads video directly from Cloudinary CDN
 * 
 * INTERVIEW TIP:
 * "Instead of serving videos from our Express server (which would block the
 *  event loop), I upload to Cloudinary and store the CDN URL. The frontend
 *  loads videos directly from Cloudinary's edge network. This offloads
 *  bandwidth from our server and reduces latency for users worldwide."
 */

const cloudinary = require("cloudinary").v2;
const config = require("../config/env");

// Configure Cloudinary with credentials
cloudinary.config({
  cloud_name: config.CLOUDINARY_CLOUD_NAME,
  api_key: config.CLOUDINARY_API_KEY,
  api_secret: config.CLOUDINARY_API_SECRET,
});

/**
 * Upload a video file to Cloudinary.
 * @param {string} filePath - Absolute path to the local .mp4 file
 * @param {string} animationId - Used as folder name for organization
 * @returns {Object} { url, publicId, thumbnailUrl, duration, bytes }
 */
async function uploadVideo(filePath, animationId) {
  const result = await cloudinary.uploader.upload(filePath, {
    resource_type: "video",        // "video" for .mp4 files
    folder: "animai/videos",       // organize in a folder
    public_id: animationId,        // use animationId as filename
    overwrite: true,               // replace if re-generated
    eager: [                       // auto-generate thumbnail
      { width: 640, height: 360, crop: "fill", format: "jpg" },
    ],
    eager_async: false,            // wait for thumbnail to be ready
  });

  return {
    url: result.secure_url,
    publicId: result.public_id,
    thumbnailUrl: result.eager?.[0]?.secure_url || null,
    duration: result.duration || null,
    bytes: result.bytes || null,
  };
}

/**
 * Delete a video from Cloudinary.
 * @param {string} publicId - The public_id stored in the Animation model
 */
async function deleteVideo(publicId) {
  if (!publicId) return;

  await cloudinary.uploader.destroy(publicId, {
    resource_type: "video",
  });
}

module.exports = { uploadVideo, deleteVideo };
