/**
 * Global error handler middleware.
 *
 * Express calls this when any route does next(err) or throws.
 * Must have exactly 4 parameters — that's how Express knows
 * it's an error handler, not a regular middleware.
 */

// eslint-disable-next-line no-unused-vars
const errorHandler = (err, req, res, next) => {
  console.error(`[Error] ${err.message}`);

  // Log stack trace in development
  if (process.env.NODE_ENV !== "production") {
    console.error(err.stack);
  }

  const statusCode = err.status || err.statusCode || 500;

  res.status(statusCode).json({
    error: err.message || "Internal Server Error",
    ...(process.env.NODE_ENV !== "production" && { stack: err.stack }),
  });
};

module.exports = errorHandler;
