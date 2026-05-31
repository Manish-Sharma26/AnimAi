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
 *   7. Client gets real-time progress via Socket.io
 * 
 * PROGRESS STAGES (emitted via socket):
 *   planning  → 10%   Job picked up, calling Python AI
 *   coding    → 20%   AI generating Manim code
 *   compiling → 50%   Running Manim sandbox (rendering video)
 *   uploading → 80%   Uploading to Cloudinary CDN
 *   complete  → 100%  Done, video ready
 */

const { Queue, Worker } = require("bullmq");
const path = require("path");
const { createRedisConnection } = require("../config/redis");
const Animation = require("../models/Animation");
const { generateVideo } = require("./pythonBridge");
const { uploadVideo } = require("./cloudinary");
const { emitToUser } = require("../sockets/progress");

// Project root — one level up from server/
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");

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

// Helper: emit progress to user with consistent format
function emitProgress(userId, animationId, step, percent, message) {
  emitToUser(userId, "job:progress", { animationId, step, percent, message });
}

// ── Worker: processes jobs from the queue ─────────────────────────────────────
const worker = new Worker(
  "video-generation",
  async (job) => {
    const { animationId, prompt, plan, userId } = job.data;
    console.log(`\n[Worker] Processing job ${job.id} for animation ${animationId}`);

    try {
      // Update status to "generating"
      await Animation.findByIdAndUpdate(animationId, { status: "generating" });

      // ── Stage 1: Starting ──────────────────────────────────────────────
      await job.updateProgress(10);
      emitProgress(userId, animationId, "planning", 10, "AI is planning your animation...");
      console.log(`[Worker] Job ${job.id}: Starting Python pipeline (10%)`);

      // ── Stage 2: Coding → Compiling (gradual progress) ─────────────────
      await new Promise(r => setTimeout(r, 300));
      await job.updateProgress(15);
      emitProgress(userId, animationId, "coding", 15, "AI is writing Manim code...");
      console.log(`[Worker] Job ${job.id}: Calling Python generate (15%)`);

      // The Python call does coding + compiling + debugging internally.
      // We run a progress ticker in parallel so the bar increases gradually.
      let tickPercent = 15;
      const progressStages = [
        { at: 20, step: "coding",    msg: "Generating animation code..." },
        { at: 28, step: "coding",    msg: "AI writing scene structure..." },
        { at: 35, step: "compiling", msg: "Compiling Manim animation..." },
        { at: 42, step: "compiling", msg: "Rendering video frames..." },
        { at: 50, step: "compiling", msg: "Processing audio & voiceover..." },
        { at: 55, step: "compiling", msg: "Almost there..." },
        { at: 60, step: "compiling", msg: "Finalizing render..." },
      ];
      let stageIdx = 0;
      const ticker = setInterval(() => {
        if (stageIdx < progressStages.length) {
          const s = progressStages[stageIdx];
          tickPercent = s.at;
          emitProgress(userId, animationId, s.step, s.at, s.msg);
          job.updateProgress(s.at).catch(() => {});
          stageIdx++;
        }
      }, 15000); // Tick every 15 seconds

      let result;
      try {
        result = await generateVideo(prompt, plan || {});
      } finally {
        clearInterval(ticker);
      }

      // ── Stage 3: Check Python result ───────────────────────────────────
      if (result.status !== "success") {
        await job.updateProgress(60);
        // Check if debugging happened (attempts > 1 means debugger ran)
        const attempts = result.attempts || 1;
        if (attempts > 1) {
          emitProgress(userId, animationId, "debugging", 55, `Debugging failed after ${attempts} attempts`);
          await new Promise(r => setTimeout(r, 1000));
        }
        emitProgress(userId, animationId, "compiling", 60, "Compilation failed — " + (result.error || "unknown error").slice(0, 100));
        throw new Error(result.error || "Python pipeline returned failure");
      }

      // If pipeline used multiple attempts, briefly show debugging stage
      const attempts = result.attempts || 1;
      if (attempts > 1) {
        await job.updateProgress(62);
        emitProgress(userId, animationId, "debugging", 62, `Fixed issues after ${attempts} attempts`);
        console.log(`[Worker] Job ${job.id}: Used debugger (${attempts} attempts)`);
        await new Promise(r => setTimeout(r, 1500));
      }

      await job.updateProgress(70);
      emitProgress(userId, animationId, "compiling", 70, "Animation compiled successfully!");
      console.log(`[Worker] Job ${job.id}: Video generated at ${result.video_path} (70%)`);

      // ── Stage 4: Upload to Cloudinary ──────────────────────────────────
      await job.updateProgress(80);
      emitProgress(userId, animationId, "uploading", 80, "Uploading video to cloud...");
      console.log(`[Worker] Job ${job.id}: Uploading to Cloudinary (80%)`);

      let videoUrl = result.video_path; // fallback to local path
      let videoPublicId = null;
      let thumbnailUrl = null;
      let videoDuration = null;
      let videoSizeBytes = null;

      try {
        // Python returns relative path like "outputs/animation.mp4" — resolve to absolute
        const absoluteVideoPath = path.isAbsolute(result.video_path)
          ? result.video_path
          : path.join(PROJECT_ROOT, result.video_path);
        console.log(`[Worker] Job ${job.id}: Resolved video path → ${absoluteVideoPath}`);

        const cloud = await uploadVideo(absoluteVideoPath, animationId);
        videoUrl = cloud.url;
        videoPublicId = cloud.publicId;
        thumbnailUrl = cloud.thumbnailUrl;
        videoDuration = cloud.duration;
        videoSizeBytes = cloud.bytes;
        console.log(`[Worker] Job ${job.id}: Uploaded → ${cloud.url}`);
      } catch (uploadErr) {
        // Non-fatal: video was generated, just couldn't upload to CDN
        // Convert local path to a URL the browser can access via Express static serving
        console.warn(`[Worker] Job ${job.id}: Cloudinary upload failed (serving locally): ${uploadErr.message}`);
        emitProgress(userId, animationId, "uploading", 85, "Cloud upload failed, serving video locally...");

        // result.video_path is like "outputs/animation.mp4" or "d:\...\outputs\animation.mp4"
        // Extract just the filename and serve via /api/videos/
        const path = require("path");
        const filename = path.basename(result.video_path);
        videoUrl = `http://localhost:${process.env.PORT || 3001}/api/videos/${filename}`;
      }

      // ── Stage 5: Save to DB ────────────────────────────────────────────
      await job.updateProgress(95);
      emitProgress(userId, animationId, "uploading", 95, "Saving results...");

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

      // ── Stage 6: Complete ──────────────────────────────────────────────
      await job.updateProgress(100);
      emitToUser(userId, "job:complete", { animationId, videoUrl, thumbnailUrl });
      console.log(`[Worker] Job ${job.id}: COMPLETE ✅`);

      return { animationId, status: "success", videoUrl };

    } catch (err) {
      const maxAttempts = job.opts?.attempts || 2;
      const attemptsMade = job.attemptsMade + 1; // current attempt (0-indexed in catch)

      if (attemptsMade < maxAttempts) {
        // Will be retried — tell the user, don't mark as failed
        console.warn(`[Worker] Job ${job.id}: Attempt ${attemptsMade}/${maxAttempts} failed — retrying...`);
        emitToUser(userId, "job:retrying", {
          animationId,
          attempt: attemptsMade,
          maxAttempts,
          error: err.message,
        });
        // Keep status as "generating" so the UI stays in progress mode
      } else {
        // Final attempt — mark as truly failed
        console.error(`[Worker] Job ${job.id}: FAILED ❌ (all ${maxAttempts} attempts exhausted)`);
        await Animation.findByIdAndUpdate(animationId, {
          status: "failed",
          error: err.message,
        });
        emitToUser(userId, "job:failed", {
          animationId,
          error: err.message,
        });
      }

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
  const maxAttempts = job.opts?.attempts || 2;
  console.log(`[Worker] Job ${job?.id} failed (attempt ${job.attemptsMade}/${maxAttempts}): ${err.message}`);
});

// ── Exports ──────────────────────────────────────────────────────────────────
module.exports = { videoQueue, worker };
