/**
 * Feedback Controller — Vote on animations
 */

const Feedback = require("../models/Feedback");
const Animation = require("../models/Animation");
const { validate, createFeedbackSchema } = require("../utils/validators");

// ── POST /api/feedback/:animationId ──────────────────────────────────────────
const createFeedback = async (req, res, next) => {
  try {
    const { vote, comment } = validate(createFeedbackSchema, req.body);
    const { animationId } = req.params;

    // Verify animation exists
    const animation = await Animation.findById(animationId);
    if (!animation) {
      return res.status(404).json({
        error: "Not found",
        message: "Animation not found",
      });
    }

    // Create feedback (compound unique index prevents duplicates)
    const feedback = await Feedback.create({
      animationId,
      userId: req.user.id,
      vote,
      comment: comment || null,
    });

    res.status(201).json({
      message: `Vote "${vote}" recorded`,
      feedback: {
        id: feedback._id,
        vote: feedback.vote,
        comment: feedback.comment,
        createdAt: feedback.createdAt,
      },
    });
  } catch (err) {
    // Handle duplicate vote (compound unique index violation)
    if (err.code === 11000) {
      return res.status(409).json({
        error: "Already voted",
        message: "You have already voted on this animation",
      });
    }
    next(err);
  }
};

module.exports = { createFeedback };
