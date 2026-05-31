/**
 * AnimAI Studio — Express API Server (Entry Point)
 * 
 * This is the main file that sets up Express with all middleware
 * and starts listening for requests.
 * 
 * Middleware order matters:
 * 1. helmet()       → Sets security HTTP headers (prevents XSS, clickjacking, etc.)
 * 2. cors()         → Allows React frontend (different port) to call this API
 * 3. morgan("dev")  → Logs every request: "GET /api/health 200 3ms"
 * 4. express.json() → Parses JSON request bodies (so req.body works)
 * 5. Routes         → Your actual endpoint handlers
 * 6. errorHandler   → Catches any errors thrown in routes
 */

const express = require("express");
const http = require("http");
const path = require("path");
const cors = require("cors");
const helmet = require("helmet");
const morgan = require("morgan");
const config = require("./config/env");
const connectDB = require("./config/db");
const errorHandler = require("./middleware/errorHandler");
const { initSocket } = require("./sockets/progress");

// ── Create Express app ──────────────────────────────────────────────────────
const app = express();

// ── Middleware Stack ─────────────────────────────────────────────────────────

// Security headers — protects against common web vulnerabilities
app.use(helmet());

// CORS — allows the React frontend (port 5173) to call this API (port 3001)
// Without this, the browser blocks cross-origin requests
app.use(cors({
  origin: process.env.CLIENT_URL || "http://localhost:5173",
  credentials: true, // Allow cookies/auth headers
}));

// Request logging — shows each request in the terminal
// "dev" format: GET /api/health 200 2.531 ms
app.use(morgan("dev"));

// JSON body parser — converts request body from JSON string to JS object
// Without this, req.body would be undefined
app.use(express.json({ limit: "10mb" }));

// URL-encoded body parser — for form submissions
app.use(express.urlencoded({ extended: true }));

// ── Static file serving for local videos ─────────────────────────────────────
// When Cloudinary upload fails, videos are served from the local outputs/ folder
// URL: /api/videos/animation.mp4 → d:\animai-studio\outputs\animation.mp4
const outputsDir = path.join(__dirname, "..", "..", "outputs");
app.use("/api/videos", express.static(outputsDir));

// ── Routes ───────────────────────────────────────────────────────────────────

// Health check — use this to verify the server is running
// Try it: GET http://localhost:3001/api/health
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    service: "AnimAI Studio API",
    timestamp: new Date().toISOString(),
    uptime: `${Math.floor(process.uptime())}s`,
  });
});

// ── Auth Routes ──────────────────────────────────────────────────────────────
app.use("/api/auth", require("./routes/auth.routes"));

// ── Animation Routes ─────────────────────────────────────────────────────────
app.use("/api/animations", require("./routes/animation.routes"));

// ── Feedback Routes ──────────────────────────────────────────────────────────
app.use("/api/feedback", require("./routes/feedback.routes"));

// ── Public Gallery (no auth required) ────────────────────────────────────────
const { getPublicGallery, getPublicAnimation } = require("./controllers/animation.controller");
app.get("/api/gallery", getPublicGallery);
app.get("/api/gallery/:id", getPublicAnimation);

// ── 404 Handler ──────────────────────────────────────────────────────────────
// If no route matched, return a helpful 404
app.use((req, res) => {
  res.status(404).json({
    error: "Not Found",
    message: `Route ${req.method} ${req.originalUrl} does not exist`,
    hint: "Try GET /api/health to check if the server is running",
  });
});

// ── Global Error Handler ─────────────────────────────────────────────────────
// Must be registered LAST — catches errors from all routes above
app.use(errorHandler);

// ── Start Server ─────────────────────────────────────────────────────────────
// Connect to MongoDB FIRST, then start listening.
// Why? If DB is unreachable, we fail fast instead of serving broken endpoints.
const PORT = config.PORT;

const startServer = async () => {
  await connectDB();

  // Create HTTP server (needed for Socket.io to piggyback on)
  const httpServer = http.createServer(app);

  // Attach Socket.io to the HTTP server
  initSocket(httpServer);

  httpServer.listen(PORT, () => {
    console.log(`\n${"=".repeat(50)}`);
    console.log(`🚀 AnimAI Studio API Server`);
    console.log(`${"=".repeat(50)}`);
    console.log(`→ Environment : ${config.NODE_ENV}`);
    console.log(`→ Port        : ${PORT}`);
    console.log(`→ Health      : http://localhost:${PORT}/api/health`);
    console.log(`→ WebSocket   : ws://localhost:${PORT}`);
    console.log(`${"=".repeat(50)}\n`);
  });
};

startServer();

module.exports = app;
