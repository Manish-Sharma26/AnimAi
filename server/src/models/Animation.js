/**
 * Animation Model (Mongoose Schema)
 * 
 * This is the CORE model — every animation a user generates lives here.
 * 
 * LIFECYCLE:
 *   1. User submits prompt         → status: "planning"
 *   2. Plan generated & approved   → status: "approved"
 *   3. Video generation queued     → status: "generating"
 *   4. Success                     → status: "success", videoUrl set
 *   5. Failure                     → status: "failed", error set
 * 
 * SCHEMA DESIGN DECISIONS:
 * - plan is Mixed (flexible JSON) because plan structure may evolve
 * - videoUrl/thumbnailUrl will be Cloudinary CDN URLs (Step 7)
 * - userId is indexed for fast "list my animations" queries
 * - isPublic enables the community gallery feature
 * 
 * INTERVIEW TIP:
 * "I chose to embed the plan JSON directly in the Animation document 
 *  rather than creating a separate Plans collection. Since a plan always 
 *  belongs to exactly one animation and is always read together with it, 
 *  embedding avoids an extra query (join). If plans were shared across 
 *  animations, I'd use a reference instead."
 */

const mongoose = require("mongoose");

const animationSchema = new mongoose.Schema(
  {
    // Owner — indexed for fast "list my animations" queries
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      index: true,
    },

    // Original user prompt
    prompt: {
      type: String,
      required: [true, "Prompt is required"],
      trim: true,
      maxlength: [2000, "Prompt must be under 2000 characters"],
    },

    // Query intent detected by the agent
    intent: {
      type: String,
      enum: ["bare_topic", "simple_explanation", "detailed"],
    },

    // Full plan JSON — flexible schema (Mixed allows any structure)
    plan: {
      type: mongoose.Schema.Types.Mixed,
      default: null,
    },

    // Teacher agent's explanation
    teacherExplanation: {
      type: mongoose.Schema.Types.Mixed,
      default: null,
    },

    // Generated Manim Python code
    generatedCode: {
      type: String,
      default: null,
    },

    // ── Cloudinary fields (populated in Step 7) ──────────────────────────────
    videoUrl: { type: String, default: null },
    videoPublicId: { type: String, default: null },
    thumbnailUrl: { type: String, default: null },
    videoDuration: { type: Number, default: null },
    videoSizeBytes: { type: Number, default: null },

    // ── Status tracking ──────────────────────────────────────────────────────
    status: {
      type: String,
      enum: ["planning", "approved", "generating", "success", "failed"],
      default: "planning",
    },

    attempts: { type: Number, default: 0 },
    hasAudio: { type: Boolean, default: false },
    isPublic: { type: Boolean, default: false },
    error: { type: String, default: null },
  },
  {
    timestamps: true, // createdAt, updatedAt
  }
);

// ── Indexes ──────────────────────────────────────────────────────────────────
// Compound index for gallery: find public animations, newest first
animationSchema.index({ isPublic: 1, createdAt: -1 });

module.exports = mongoose.model("Animation", animationSchema);
