/**
 * Feedback Model (Mongoose Schema)
 * 
 * Stores thumbs up/down votes on animations.
 * Compound index on (animationId + userId) prevents duplicate votes.
 * 
 * INTERVIEW TIP:
 * "I used a compound unique index on {animationId, userId} so each user
 *  can only vote once per animation. If they vote again, MongoDB throws
 *  a duplicate key error, which I catch and return a friendly 409."
 */

const mongoose = require("mongoose");

const feedbackSchema = new mongoose.Schema(
  {
    animationId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Animation",
      required: true,
    },

    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },

    vote: {
      type: String,
      enum: ["up", "down"],
      required: [true, "Vote is required (up or down)"],
    },

    comment: {
      type: String,
      trim: true,
      maxlength: [500, "Comment must be under 500 characters"],
      default: null,
    },
  },
  {
    timestamps: true,
  }
);

// One vote per user per animation
feedbackSchema.index({ animationId: 1, userId: 1 }, { unique: true });

module.exports = mongoose.model("Feedback", feedbackSchema);
