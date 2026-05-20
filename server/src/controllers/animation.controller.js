/**
 * Animation Controller — CRUD operations for animations
 * 
 * CRUD = Create, Read, Update, Delete — the four basic database operations.
 * Every REST API maps HTTP methods to CRUD:
 *   POST   → Create
 *   GET    → Read
 *   PUT    → Update
 *   DELETE → Delete
 * 
 * OWNERSHIP:
 * Every query filters by userId so users can only see/modify their own data.
 * This is a fundamental security pattern — never trust the client.
 */

const Animation = require("../models/Animation");
const { validate, createAnimationSchema, updatePlanSchema, paginationSchema } = require("../utils/validators");
const { videoQueue } = require("../services/queue");

// ── POST /api/animations ─────────────────────────────────────────────────────
// Create a new animation with a prompt (status starts as "planning")
const createAnimation = async (req, res, next) => {
  try {
    const { prompt } = validate(createAnimationSchema, req.body);

    const animation = await Animation.create({
      userId: req.user.id,
      prompt,
      status: "planning",
    });

    res.status(201).json({
      message: "Animation created",
      animation: {
        id: animation._id,
        prompt: animation.prompt,
        status: animation.status,
        createdAt: animation.createdAt,
      },
    });
  } catch (err) {
    next(err);
  }
};

// ── GET /api/animations ──────────────────────────────────────────────────────
// List current user's animations (paginated, newest first)
const listAnimations = async (req, res, next) => {
  try {
    const { page, limit } = validate(paginationSchema, req.query);
    const skip = (page - 1) * limit;

    // Run count and find in parallel for better performance
    const [animations, total] = await Promise.all([
      Animation.find({ userId: req.user.id })
        .sort({ createdAt: -1 })   // newest first
        .skip(skip)
        .limit(limit)
        .select("-generatedCode"),  // exclude large code field from list view
      Animation.countDocuments({ userId: req.user.id }),
    ]);

    res.json({
      animations,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (err) {
    next(err);
  }
};

// ── GET /api/animations/:id ──────────────────────────────────────────────────
// Get full details of a single animation (including code)
const getAnimation = async (req, res, next) => {
  try {
    const animation = await Animation.findOne({
      _id: req.params.id,
      userId: req.user.id, // ownership check — only your animations
    });

    if (!animation) {
      return res.status(404).json({
        error: "Not found",
        message: "Animation not found or you don't have access",
      });
    }

    res.json({ animation });
  } catch (err) {
    next(err);
  }
};

// ── PUT /api/animations/:id ──────────────────────────────────────────────────
// Update animation plan and/or status (used when user approves/edits the plan)
const updateAnimation = async (req, res, next) => {
  try {
    const { plan, status } = validate(updatePlanSchema, req.body);

    const animation = await Animation.findOneAndUpdate(
      { _id: req.params.id, userId: req.user.id },
      {
        plan,
        ...(status && { status }),  // only update status if provided
      },
      { new: true } // return the updated document, not the old one
    );

    if (!animation) {
      return res.status(404).json({
        error: "Not found",
        message: "Animation not found or you don't have access",
      });
    }

    res.json({
      message: "Animation updated",
      animation,
    });
  } catch (err) {
    next(err);
  }
};

// ── DELETE /api/animations/:id ───────────────────────────────────────────────
// Delete an animation (later: also delete from Cloudinary in Step 7)
const deleteAnimation = async (req, res, next) => {
  try {
    const animation = await Animation.findOneAndDelete({
      _id: req.params.id,
      userId: req.user.id, // ownership check
    });

    if (!animation) {
      return res.status(404).json({
        error: "Not found",
        message: "Animation not found or you don't have access",
      });
    }

    // TODO (Step 7): Delete video from Cloudinary using animation.videoPublicId

    res.json({
      message: "Animation deleted",
      id: animation._id,
    });
  } catch (err) {
    next(err);
  }
};

// ── POST /api/animations/generate ────────────────────────────────────────────
// Queue a video generation job — returns jobId instantly (non-blocking)
const generateAnimation = async (req, res, next) => {
  try {
    const { animationId } = req.body;

    if (!animationId) {
      return res.status(400).json({
        error: "Missing field",
        message: "animationId is required",
      });
    }

    // Verify animation exists and belongs to user
    const animation = await Animation.findOne({
      _id: animationId,
      userId: req.user.id,
    });

    if (!animation) {
      return res.status(404).json({
        error: "Not found",
        message: "Animation not found or you don't have access",
      });
    }

    if (animation.status === "generating") {
      return res.status(409).json({
        error: "Already generating",
        message: "This animation is already being generated",
      });
    }

    // Add job to the BullMQ queue
    const job = await videoQueue.add("generate-video", {
      animationId: animation._id.toString(),
      prompt: animation.prompt,
      plan: animation.plan,
      userId: req.user.id,
    });

    // Update status immediately
    await Animation.findByIdAndUpdate(animationId, { status: "generating" });

    res.status(202).json({
      message: "Video generation queued",
      jobId: job.id,
      animationId,
    });
  } catch (err) {
    next(err);
  }
};

// ── GET /api/jobs/:jobId ─────────────────────────────────────────────────────
// Poll job status — client calls this to check progress
const getJobStatus = async (req, res, next) => {
  try {
    const job = await videoQueue.getJob(req.params.jobId);

    if (!job) {
      return res.status(404).json({
        error: "Not found",
        message: "Job not found",
      });
    }

    const state = await job.getState(); // "waiting" | "active" | "completed" | "failed"
    const progress = job.progress || 0;

    res.json({
      jobId: job.id,
      state,
      progress,
      data: job.data,
      result: job.returnvalue,       // set when job completes
      failedReason: job.failedReason, // set when job fails
    });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  createAnimation,
  listAnimations,
  getAnimation,
  updateAnimation,
  deleteAnimation,
  generateAnimation,
  getJobStatus,
};
