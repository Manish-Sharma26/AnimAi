/**
 * Seed Script — Upload local videos to Cloudinary and populate MongoDB Gallery
 * 
 * Run: node scripts/seed-gallery.js
 * 
 * This script:
 * 1. Reads all .mp4 files from anim_videos/
 * 2. Uploads each to Cloudinary (with auto-thumbnail)
 * 3. Creates Animation records in MongoDB (status: "success", isPublic: true)
 * 4. Links them to the existing user account
 */

require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });

const path = require("path");
const fs = require("fs");
const mongoose = require("mongoose");
const config = require("../src/config/env");
const { uploadVideo } = require("../src/services/cloudinary");
const Animation = require("../src/models/Animation");
const User = require("../src/models/User");

// ── Video → Prompt mapping ──────────────────────────────────────────────────
// Create meaningful prompts from filenames
const VIDEO_PROMPTS = {
  "BERT.mp4": "Explain how BERT (Bidirectional Encoder Representations from Transformers) works",
  "CNN.mp4": "Explain Convolutional Neural Networks (CNN) architecture",
  "GRU.mp4": "How do Gated Recurrent Units (GRU) work?",
  "Gradient_descent.mp4": "Explain gradient descent optimization algorithm",
  "LSTM.mp4": "How do Long Short-Term Memory (LSTM) networks work?",
  "RNN.mp4": "Explain Recurrent Neural Networks (RNN) and sequence processing",
  "VIT2.mp4": "How does a Vision Transformer (ViT) process images?",
  "animai_showcase_video.mp4": "AnimAI Studio — Full feature showcase",
  "animation.mp4": "Introduction to mathematical animations with Manim",
  "binarysearch.mp4": "Explain binary search algorithm step by step",
  "bubble.mp4": "How does bubble sort algorithm work?",
  "bubblesort.mp4": "Visualize the bubble sort algorithm with comparisons",
  "descent.mp4": "How gradient descent finds the minimum of a function",
  "final_gradient.mp4": "Gradient descent — learning rate and convergence",
  "linearequation.mp4": "Solving linear equations visually",
  "neural.mp4": "How neural networks learn — forward and backward propagation",
  "photosynthesis.mp4": "Explain the process of photosynthesis",
  "quick.mp4": "How does quicksort algorithm work?",
  "redis_animation.mp4": "How Redis works — in-memory data store explained",
  "rnn2.mp4": "Recurrent Neural Networks — hidden state and memory",
  "transformers.mp4": "The Transformer architecture — attention is all you need",
  "tree.mp4": "Binary tree data structure explained",
  "treetraversal.mp4": "Tree traversal algorithms — inorder, preorder, postorder",
};

async function seed() {
  // 1. Connect to MongoDB
  console.log("🔗 Connecting to MongoDB...");
  await mongoose.connect(config.MONGO_URI);
  console.log("✅ Connected to MongoDB\n");

  // 2. Find the user
  const user = await User.findOne({ email: "manish@animai.com" });
  if (!user) {
    console.error("❌ User not found. Please create the user first.");
    process.exit(1);
  }
  console.log(`👤 Using user: ${user.username} (${user._id})\n`);

  // 3. Read video files
  const videoDir = path.resolve(__dirname, "../../anim_videos");
  const files = fs.readdirSync(videoDir).filter((f) => f.endsWith(".mp4"));
  console.log(`📁 Found ${files.length} videos in anim_videos/\n`);

  let uploaded = 0;
  let skipped = 0;

  for (const file of files) {
    const filePath = path.join(videoDir, file);
    const prompt = VIDEO_PROMPTS[file] || file.replace(/\.mp4$/, "").replace(/[_-]/g, " ");

    // Check if already uploaded (avoid duplicates)
    const existing = await Animation.findOne({
      userId: user._id,
      prompt,
      status: "success",
    });

    if (existing) {
      console.log(`⏭  SKIP: "${prompt}" (already exists)`);
      skipped++;
      continue;
    }

    try {
      // Create animation record first to get an ID
      const animation = await Animation.create({
        userId: user._id,
        prompt,
        status: "generating",
        isPublic: true,
      });

      console.log(`📤 Uploading: ${file} (${(fs.statSync(filePath).size / 1024 / 1024).toFixed(1)}MB)...`);

      // Upload to Cloudinary
      const result = await uploadVideo(filePath, animation._id.toString());

      // Update animation with Cloudinary data
      await Animation.findByIdAndUpdate(animation._id, {
        status: "success",
        videoUrl: result.url,
        videoPublicId: result.publicId,
        thumbnailUrl: result.thumbnailUrl,
        videoDuration: result.duration,
        videoSizeBytes: result.bytes,
        isPublic: true,
      });

      uploaded++;
      console.log(`   ✅ Done! Duration: ${result.duration?.toFixed(1)}s | Thumb: ${result.thumbnailUrl ? "✓" : "✗"}\n`);

    } catch (err) {
      console.error(`   ❌ FAILED: ${err.message}\n`);
    }
  }

  console.log("\n" + "═".repeat(50));
  console.log(`🎉 Seeding complete!`);
  console.log(`   Uploaded: ${uploaded}`);
  console.log(`   Skipped:  ${skipped}`);
  console.log(`   Total:    ${files.length}`);
  console.log("═".repeat(50));

  await mongoose.disconnect();
  process.exit(0);
}

seed().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
