/**
 * Redis Connection (for BullMQ)
 * 
 * WHY REDIS?
 * BullMQ needs Redis as its backing store. When you add a job to the queue,
 * BullMQ writes it to Redis. Workers poll Redis for new jobs. This means:
 * - Jobs survive server restarts (persisted in Redis)
 * - Multiple workers can process jobs from the same queue
 * - Job status is always queryable
 * 
 * INTERVIEW TIP:
 * "I chose BullMQ + Redis over FastAPI BackgroundTasks because:
 *  1. Jobs persist — if the server crashes, queued jobs aren't lost
 *  2. Horizontal scaling — multiple worker instances can process jobs
 *  3. Built-in retry with backoff — failed jobs retry automatically
 *  4. Job status tracking — clients can poll job progress"
 */

const IORedis = require("ioredis");
const config = require("./env");

// Create a Redis connection factory
// BullMQ requires a NEW connection for each Queue and Worker
const createRedisConnection = () => {
  return new IORedis({
    host: config.REDIS_HOST,
    port: config.REDIS_PORT,
    maxRetriesPerRequest: null, // Required by BullMQ
  });
};

module.exports = { createRedisConnection };
