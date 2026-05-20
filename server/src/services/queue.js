/**
 * Video Generation Queue (BullMQ)
 * 
 * HOW THE JOB QUEUE WORKS:
 * 
 *   1. User hits POST /api/animations/generate
 *   2. Route handler adds a job to the "video-generation" queue
 *   3. Returns { jobId } immediately (non-blocking!)
 *   4. Worker picks up the job from Redis
 *   5. Worker calls Python pipeline (Step 6) + uploads to Cloudinary (Step 7)
 *   6. Worker updates MongoDB with results
 *   7. Client polls GET /api/jobs/:jobId to check progress
 * 
 * WHY NOT JUST await generateVideo() IN THE ROUTE?
 * Video generation takes 30-120 seconds. If you await in the route:
 * - HTTP connection may timeout
 * - Express thread is blocked — can't serve other users
 * - If server crashes mid-generation, the request is lost
 * 
 * With a queue:
 * - Response is instant (jobId returned in milliseconds)
 * - Worker processes in background
 * - Job survives server restart (persisted in Redis)
 * - Client gets progress updates via polling (or WebSocket in Step 8)
 * 
 * INTERVIEW TIP:
 * "I used BullMQ to decouple the API response from the long-running video
 *  generation. The API returns a jobId instantly, and the client polls for
 *  status. This pattern is called 'async request-reply' — it's how most
 *  production systems handle tasks that take more than a few seconds."
 */

const { Queue, Worker } = require("bullmq");
const { createRedisConnection } = require("../config/redis");
const Animation = require("../models/Animation");
const { generateVideo } = require("./pythonBridge");
const { uploadVideo } = require("./cloudinary");
const { emitToUser } = require("../sockets/progress");

// ── Queue: where jobs wait to be processed ───────────────────────────────────
const videoQueue = new Queue("video-generation", {
  connection: createRedisConnection(),
  defaultJobOptions: {
    attempts: 2,
    backoff: { type: "exponential", delay: 5000 },
    removeOnComplete: { count: 100 },
    removeOnFail: { count: 50 },
  },
});

// ── Worker: processes jobs from the queue ─────────────────────────────────────
const worker = new Worker(
  "video-generation",
  async (job) => {
    const { animationId, prompt, plan, userId } = job.data;
    console.log(`\n[Worker] Processing job ${job.id} for animation ${animationId}`);

    try {
      // Update status to "generating"
      await Animation.findByIdAndUpdate(animationId, { status: "generating" });

      // ── Stage 1: Call Python AI pipeline ────────────────────────────────
      await job.updateProgress(20);
      emitToUser(userId, "job:progress", { animationId, step: "planning", percent: 20 });
      console.log(`[Worker] Job ${job.id}: Calling Python pipeline... (20%)`);

      const result = await generateVideo(prompt, plan || {});

      // ── Stage 2: Check result ──────────────────────────────────────────
      await job.updateProgress(60);
      emitToUser(userId, "job:progress", { animationId, step: "compiling", percent: 60 });

      if (result.status !== "success") {
        throw new Error(result.error || "Python pipeline returned failure");
      }

      console.log(`[Worker] Job ${job.id}: Video generated at ${result.video_path} (60%)`);

      // ── Stage 3: Upload to Cloudinary ─────────────────────────────────
      await job.updateProgress(80);
      emitToUser(userId, "job:progress", { animationId, step: "uploading", percent: 80 });
      console.log(`[Worker] Job ${job.id}: Uploading to Cloudinary... (80%)`);

      let videoUrl = result.video_path; // fallback to local path
      let videoPublicId = null;
      let thumbnailUrl = null;
      let videoDuration = null;
      let videoSizeBytes = null;

      try {
        const cloud = await uploadVideo(result.video_path, animationId);
        videoUrl = cloud.url;
        videoPublicId = cloud.publicId;
        thumbnailUrl = cloud.thumbnailUrl;
        videoDuration = cloud.duration;
        videoSizeBytes = cloud.bytes;
        console.log(`[Worker] Job ${job.id}: Uploaded → ${cloud.url}`);
      } catch (uploadErr) {
        // Non-fatal: video was generated, just couldn't upload to CDN
        console.warn(`[Worker] Job ${job.id}: Cloudinary upload failed (using local path): ${uploadErr.message}`);
      }

      // ── Stage 4: Update MongoDB with results ───────────────────────────
      await Animation.findByIdAndUpdate(animationId, {
        status: "success",
        generatedCode: result.code,
        videoUrl,
        videoPublicId,
        thumbnailUrl,
        videoDuration,
        videoSizeBytes,
        hasAudio: result.has_audio || false,
        attempts: result.attempts || 1,
      });

      await job.updateProgress(100);
      emitToUser(userId, "job:complete", { animationId, videoUrl, thumbnailUrl });
      console.log(`[Worker] Job ${job.id}: COMPLETE`);

      return { animationId, status: "success", videoUrl };

    } catch (err) {
      console.error(`[Worker] Job ${job.id}: FAILED ❌ — ${err.message}`);

      await Animation.findByIdAndUpdate(animationId, {
        status: "failed",
        error: err.message,
      });

      emitToUser(userId, "job:failed", { animationId, error: err.message });

      throw err;
    }
  },
  {
    connection: createRedisConnection(),
    concurrency: 2,
  }
);

// ── Worker Event Listeners ───────────────────────────────────────────────────
worker.on("completed", (job) => {
  console.log(`[Worker] Job ${job.id} completed successfully`);
});

worker.on("failed", (job, err) => {
  console.log(`[Worker] Job ${job?.id} failed: ${err.message}`);
});

// ── Exports ──────────────────────────────────────────────────────────────────
module.exports = { videoQueue, worker };
