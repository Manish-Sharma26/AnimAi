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

// ── Queue: where jobs wait to be processed ───────────────────────────────────
const videoQueue = new Queue("video-generation", {
  connection: createRedisConnection(),
  defaultJobOptions: {
    attempts: 2,        // retry once if worker crashes
    backoff: {
      type: "exponential",
      delay: 5000,      // wait 5s before first retry, 10s before second
    },
    removeOnComplete: { count: 100 },  // keep last 100 completed jobs
    removeOnFail: { count: 50 },       // keep last 50 failed jobs
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

      // ── Stage 1: Planning (simulated for now) ──────────────────────────
      await job.updateProgress(20);
      console.log(`[Worker] Job ${job.id}: Planning... (20%)`);
      await sleep(2000);

      // ── Stage 2: Generating code (simulated) ──────────────────────────
      await job.updateProgress(40);
      console.log(`[Worker] Job ${job.id}: Generating code... (40%)`);
      await sleep(2000);

      // ── Stage 3: Compiling video (simulated) ──────────────────────────
      await job.updateProgress(60);
      console.log(`[Worker] Job ${job.id}: Compiling video... (60%)`);
      await sleep(3000);

      // ── Stage 4: Uploading (simulated) ─────────────────────────────────
      await job.updateProgress(80);
      console.log(`[Worker] Job ${job.id}: Uploading... (80%)`);
      await sleep(1000);

      // ── Complete ───────────────────────────────────────────────────────
      // In Step 6+7: this will call Python pipeline + Cloudinary upload
      // For now: mark as success with dummy data
      await Animation.findByIdAndUpdate(animationId, {
        status: "success",
        videoUrl: "https://placeholder.com/video.mp4",  // Real URL in Step 7
        attempts: 1,
        hasAudio: true,
      });

      await job.updateProgress(100);
      console.log(`[Worker] Job ${job.id}: COMPLETE ✅`);

      return { animationId, status: "success" };

    } catch (err) {
      console.error(`[Worker] Job ${job.id}: FAILED ❌ — ${err.message}`);

      await Animation.findByIdAndUpdate(animationId, {
        status: "failed",
        error: err.message,
      });

      throw err; // BullMQ will retry if attempts remain
    }
  },
  {
    connection: createRedisConnection(),
    concurrency: 2, // process max 2 jobs at a time
  }
);

// ── Worker Event Listeners ───────────────────────────────────────────────────
worker.on("completed", (job) => {
  console.log(`[Worker] Job ${job.id} completed successfully`);
});

worker.on("failed", (job, err) => {
  console.log(`[Worker] Job ${job?.id} failed: ${err.message}`);
});

// ── Helper ───────────────────────────────────────────────────────────────────
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── Exports ──────────────────────────────────────────────────────────────────
module.exports = { videoQueue, worker };
