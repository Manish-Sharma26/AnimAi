/**
 * Feedback Routes
 * 
 * POST /api/feedback/:animationId → Vote on an animation
 */

const express = require("express");
const router = express.Router();
const auth = require("../middleware/auth");
const { createFeedback } = require("../controllers/feedback.controller");

router.post("/:animationId", auth, createFeedback);

module.exports = router;
