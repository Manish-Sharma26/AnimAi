/**
 * Environment variable loader.
 * 
 * Loads variables from the server/.env file using dotenv.
 * All env vars are accessed through this module so there's
 * one place to check what the server needs to run.
 */

const dotenv = require("dotenv");
const path = require("path");

// Load .env from the server/ directory
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const config = {
  // Server
  PORT: process.env.PORT || 3001,
  NODE_ENV: process.env.NODE_ENV || "development",

  // MongoDB
  MONGO_URI: process.env.MONGO_URI,

  // JWT
  JWT_SECRET: process.env.JWT_SECRET,
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || "7d",

  // Redis
  REDIS_HOST: process.env.REDIS_HOST || "localhost",
  REDIS_PORT: parseInt(process.env.REDIS_PORT) || 6379,

  // Python AI Service
  PYTHON_API_URL: process.env.PYTHON_API_URL || "http://localhost:8000",

  // Cloudinary
  CLOUDINARY_CLOUD_NAME: process.env.CLOUDINARY_CLOUD_NAME,
  CLOUDINARY_API_KEY: process.env.CLOUDINARY_API_KEY,
  CLOUDINARY_API_SECRET: process.env.CLOUDINARY_API_SECRET,
};

module.exports = config;
