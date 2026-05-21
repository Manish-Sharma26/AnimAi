/**
 * Animation Routes
 * 
 * All routes are protected (auth middleware) — users must be logged in.
 * 
 * POST   /api/animations           → Create animation with prompt
 * GET    /api/animations           → List my animations (paginated)
 * GET    /api/animations/:id       → Get single animation details
 * PUT    /api/animations/:id       → Update plan/status
 * DELETE /api/animations/:id       → Delete animation
 * POST   /api/animations/generate  → Queue video generation (returns jobId)
 * GET    /api/animations/jobs/:jobId → Poll job status
 */

const express = require("express");
const router = express.Router();
const auth = require("../middleware/auth");
const {
  createAnimation,
  listAnimations,
  getAnimation,
  updateAnimation,
  deleteAnimation,
  generateAnimation,
  getJobStatus,
  toggleShare,
} = require("../controllers/animation.controller");

// All animation routes require authentication
router.use(auth);

router.post("/", createAnimation);
router.get("/", listAnimations);
router.post("/generate", generateAnimation);   // Must be before /:id
router.get("/jobs/:jobId", getJobStatus);       // Must be before /:id
router.get("/:id", getAnimation);
router.put("/:id", updateAnimation);
router.patch("/:id/share", toggleShare);
router.delete("/:id", deleteAnimation);

module.exports = router;
