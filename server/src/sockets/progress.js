/**
 * Socket.io — Real-Time Progress Events
 * 
 * HOW IT WORKS:
 * 
 *   POLLING (old way):
 *     Client: "Are we there yet?"  →  Server: "No"
 *     Client: "Are we there yet?"  →  Server: "No"
 *     Client: "Are we there yet?"  →  Server: "Yes!"
 *     (Wastes requests, delayed updates)
 * 
 *   WEBSOCKET (our way):
 *     Client: "Tell me when something happens"
 *     Server: "Planning... 20%"
 *     Server: "Coding... 40%"
 *     Server: "Compiling... 60%"
 *     Server: "Uploading... 80%"
 *     Server: "Done! Here's the video URL"
 *     (Instant, no wasted requests)
 * 
 * ROOM STRATEGY:
 * Each user joins a room named `user:<userId>`. When the worker has a progress
 * update, it emits to that room. This means:
 * - User A only sees their own job progress (not User B's)
 * - If user has multiple tabs, ALL tabs get the update
 * - If user is offline, events are just dropped (no queue needed)
 * 
 * INTERVIEW TIP:
 * "I used Socket.io rooms to scope events per user. The worker emits to
 *  room user:123, so only that user's connected clients receive it. This
 *  is more efficient than broadcasting to all clients and filtering on
 *  the client side."
 */

const { Server } = require("socket.io");
const jwt = require("jsonwebtoken");
const config = require("../config/env");

let io = null;

/**
 * Initialize Socket.io and attach to the HTTP server.
 * @param {http.Server} httpServer - The Node HTTP server (not Express app)
 */
function initSocket(httpServer) {
  io = new Server(httpServer, {
    cors: {
      origin: config.CLIENT_URL || "http://localhost:5173",
      methods: ["GET", "POST"],
    },
  });

  // ── Authentication middleware ────────────────────────────────────────────
  // Verify JWT before allowing WebSocket connection
  io.use((socket, next) => {
    const token = socket.handshake.auth?.token;

    if (!token) {
      return next(new Error("Authentication required"));
    }

    try {
      const decoded = jwt.verify(token, config.JWT_SECRET);
      socket.userId = decoded.id;
      next();
    } catch (err) {
      next(new Error("Invalid token"));
    }
  });

  // ── Connection handler ──────────────────────────────────────────────────
  io.on("connection", (socket) => {
    const userId = socket.userId;
    const room = `user:${userId}`;

    // Join user-specific room
    socket.join(room);
    console.log(`[Socket] User ${userId} connected (room: ${room})`);

    socket.on("disconnect", () => {
      console.log(`[Socket] User ${userId} disconnected`);
    });
  });

  console.log("[Socket] Socket.io initialized");
  return io;
}

/**
 * Emit a job progress event to a specific user.
 * @param {string} userId - The user who owns the job
 * @param {string} event - Event name ("job:progress", "job:complete", "job:failed")
 * @param {Object} data - Event payload
 */
function emitToUser(userId, event, data) {
  if (!io) return;
  io.to(`user:${userId}`).emit(event, data);
}

/**
 * Get the Socket.io server instance.
 */
function getIO() {
  return io;
}

module.exports = { initSocket, emitToUser, getIO };
