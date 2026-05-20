/**
 * JWT Authentication Middleware
 * 
 * HOW IT WORKS:
 * 1. Client sends request with header: Authorization: Bearer <token>
 * 2. This middleware extracts the token from the header
 * 3. Verifies the token using the JWT_SECRET
 * 4. If valid → attaches decoded payload to req.user → calls next()
 * 5. If invalid/missing → returns 401 Unauthorized
 * 
 * USAGE IN ROUTES:
 *   router.get("/protected", auth, (req, res) => {
 *     // req.user.id is available here
 *   });
 * 
 * INTERVIEW TIP:
 * "JWT is stateless — the server doesn't store sessions. The token itself 
 *  contains the user ID and expiry. The server just verifies the signature
 *  using the secret key. This means any server instance can verify any token
 *  without a shared session store — perfect for horizontal scaling."
 */

const jwt = require("jsonwebtoken");
const config = require("../config/env");

const auth = (req, res, next) => {
  // Step 1: Extract token from "Authorization: Bearer <token>" header
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Access denied",
      message: "No token provided. Send Authorization: Bearer <token>",
    });
  }

  const token = authHeader.split(" ")[1]; // "Bearer xyz123" → "xyz123"

  try {
    // Step 2: Verify token — checks signature + expiry
    // jwt.verify() throws if token is invalid, expired, or tampered with
    const decoded = jwt.verify(token, config.JWT_SECRET);

    // Step 3: Attach user info to request object
    // Now every route handler can access req.user.id
    req.user = { id: decoded.id, email: decoded.email };

    next(); // Continue to the route handler
  } catch (err) {
    // Token is invalid, expired, or was tampered with
    if (err.name === "TokenExpiredError") {
      return res.status(401).json({
        error: "Token expired",
        message: "Your session has expired. Please log in again.",
      });
    }

    return res.status(401).json({
      error: "Invalid token",
      message: "The provided token is not valid.",
    });
  }
};

module.exports = auth;
