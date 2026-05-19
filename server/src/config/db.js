/**
 * MongoDB Connection (Mongoose)
 * 
 * HOW MONGOOSE WORKS:
 * - mongoose.connect() opens a connection pool (not just one connection)
 * - Mongoose buffers operations — you can define models before connecting
 * - Once connected, all buffered operations execute automatically
 * 
 * WHY CONNECTION POOLING?
 * - MongoDB driver maintains multiple connections (default: 5)
 * - When one request is waiting for DB response, another can use a different connection
 * - This is how Node handles concurrent users efficiently
 * 
 * INTERVIEW TIP:
 * "Mongoose maintains a connection pool. I call connect() once at startup,
 *  and all subsequent queries reuse connections from the pool."
 */

const mongoose = require("mongoose");

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGO_URI);

    console.log(`✅ MongoDB connected: ${conn.connection.host}`);
    console.log(`   Database: ${conn.connection.name}`);
  } catch (err) {
    console.error(`❌ MongoDB connection failed: ${err.message}`);
    // Exit process — no point running an API that can't reach the database
    process.exit(1);
  }
};

module.exports = connectDB;
