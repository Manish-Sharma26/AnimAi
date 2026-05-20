/**
 * Auth Controller — Business logic for register, login, me
 * 
 * WHY SEPARATE CONTROLLER FROM ROUTES?
 * - Routes define WHAT URL maps WHERE (thin layer)
 * - Controllers define WHAT HAPPENS (business logic)
 * - This separation makes testing easier — you can test controllers
 *   without spinning up Express
 * 
 * PASSWORD FLOW:
 * Register: plain password → bcrypt.hash() → store hash in DB
 * Login:    plain password → bcrypt.compare(plain, hash) → true/false
 * 
 * INTERVIEW TIP:
 * "bcrypt adds a random salt before hashing, so even if two users have
 *  the same password, their hashes are different. The salt is stored
 *  inside the hash string itself. The cost factor (10) means 2^10 = 1024
 *  iterations — slow enough to resist brute force, fast enough for UX."
 */

const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const User = require("../models/User");
const config = require("../config/env");

// ── Helper: Generate JWT ─────────────────────────────────────────────────────
const generateToken = (user) => {
  return jwt.sign(
    { id: user._id, email: user.email },  // payload — data stored IN the token
    config.JWT_SECRET,                      // secret — used to sign (never expose this)
    { expiresIn: config.JWT_EXPIRES_IN }    // options — token dies after 7 days
  );
};

// ── POST /api/auth/register ──────────────────────────────────────────────────
const register = async (req, res, next) => {
  try {
    const { email, username, password } = req.body;

    // Validate input
    if (!email || !username || !password) {
      return res.status(400).json({
        error: "Missing fields",
        message: "Email, username, and password are required",
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        error: "Weak password",
        message: "Password must be at least 6 characters",
      });
    }

    // Check if email or username already exists
    const existingUser = await User.findOne({
      $or: [{ email: email.toLowerCase() }, { username }],
    });

    if (existingUser) {
      const field = existingUser.email === email.toLowerCase() ? "Email" : "Username";
      return res.status(409).json({
        error: "Already exists",
        message: `${field} is already registered`,
      });
    }

    // Hash password — cost factor 10 means 2^10 = 1024 hashing rounds
    // Higher = more secure but slower. 10 is the sweet spot.
    const salt = await bcrypt.genSalt(10);
    const passwordHash = await bcrypt.hash(password, salt);

    // Create user
    const user = await User.create({ email, username, passwordHash });

    // Generate JWT
    const token = generateToken(user);

    res.status(201).json({
      message: "Account created successfully",
      token,
      user: {
        id: user._id,
        email: user.email,
        username: user.username,
        settings: user.settings,
        createdAt: user.createdAt,
      },
    });
  } catch (err) {
    next(err);
  }
};

// ── POST /api/auth/login ─────────────────────────────────────────────────────
const login = async (req, res, next) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: "Missing fields",
        message: "Email and password are required",
      });
    }

    // Find user by email
    const user = await User.findOne({ email: email.toLowerCase() });

    if (!user) {
      // Don't reveal whether email exists — same message for both cases
      return res.status(401).json({
        error: "Invalid credentials",
        message: "Email or password is incorrect",
      });
    }

    // Compare provided password with stored hash
    const isMatch = await bcrypt.compare(password, user.passwordHash);

    if (!isMatch) {
      return res.status(401).json({
        error: "Invalid credentials",
        message: "Email or password is incorrect",
      });
    }

    // Generate JWT
    const token = generateToken(user);

    res.json({
      message: "Login successful",
      token,
      user: {
        id: user._id,
        email: user.email,
        username: user.username,
        settings: user.settings,
        createdAt: user.createdAt,
      },
    });
  } catch (err) {
    next(err);
  }
};

// ── GET /api/auth/me ─────────────────────────────────────────────────────────
// Protected route — requires valid JWT (auth middleware runs first)
const getMe = async (req, res, next) => {
  try {
    // req.user.id was set by the auth middleware after verifying the JWT
    const user = await User.findById(req.user.id).select("-passwordHash");
    // .select("-passwordHash") excludes the hash from the response

    if (!user) {
      return res.status(404).json({
        error: "User not found",
        message: "The user associated with this token no longer exists",
      });
    }

    res.json({
      user: {
        id: user._id,
        email: user.email,
        username: user.username,
        settings: user.settings,
        createdAt: user.createdAt,
      },
    });
  } catch (err) {
    next(err);
  }
};

module.exports = { register, login, getMe };
