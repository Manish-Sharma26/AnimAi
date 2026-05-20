/**
 * Auth Routes
 * 
 * Maps URL paths to controller functions.
 * Routes are THIN — they only define the URL, HTTP method, and middleware chain.
 * All business logic lives in the controller.
 * 
 * POST /api/auth/register  → Create account
 * POST /api/auth/login     → Get JWT token
 * GET  /api/auth/me        → Get current user (protected)
 */

const express = require("express");
const router = express.Router();
const { register, login, getMe } = require("../controllers/auth.controller");
const auth = require("../middleware/auth");

// Public routes — no token needed
router.post("/register", register);
router.post("/login", login);

// Protected route — auth middleware verifies JWT first
router.get("/me", auth, getMe);

module.exports = router;
