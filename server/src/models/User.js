/**
 * User Model (Mongoose Schema)
 * 
 * SCHEMA vs MODEL:
 * - Schema = the SHAPE of data (what fields, what types, what rules)
 * - Model  = the CLASS you use to create/read/update/delete documents
 * 
 * Think of it like: Schema is the blueprint, Model is the constructor.
 * 
 * KEY CONCEPTS:
 * - `unique: true`   → Mongoose creates a unique INDEX in MongoDB
 * - `required: true`  → Validation runs before saving — throws error if missing
 * - `timestamps: true` → Auto-adds createdAt and updatedAt fields
 * - `trim: true`      → Strips whitespace from start/end before saving
 * - `lowercase: true`  → Converts to lowercase before saving ("Test@Gmail.COM" → "test@gmail.com")
 * 
 * INTERVIEW TIP:
 * "I use Mongoose schema-level validation as the first line of defense.
 *  Route-level validation (Joi) catches bad input before it hits the DB,
 *  but schema validation is the safety net in case something bypasses the route."
 */

const mongoose = require("mongoose");

const userSchema = new mongoose.Schema(
  {
    email: {
      type: String,
      required: [true, "Email is required"],
      unique: true,         // Creates a unique index — no two users can have same email
      lowercase: true,      // "Test@Gmail.COM" → "test@gmail.com"
      trim: true,
      match: [              // Regex validation for email format
        /^[\w.-]+@[\w.-]+\.\w{2,}$/,
        "Please provide a valid email",
      ],
    },

    username: {
      type: String,
      required: [true, "Username is required"],
      unique: true,
      trim: true,
      minlength: [3, "Username must be at least 3 characters"],
      maxlength: [30, "Username must be at most 30 characters"],
    },

    // Password hash — NEVER store plain text passwords
    // We'll add bcrypt hashing in Step 3
    passwordHash: {
      type: String,
      required: [true, "Password is required"],
    },

    // User preferences — will be used by the animation pipeline
    settings: {
      defaultTtsProvider: {
        type: String,
        enum: ["azure", "gtts"],
        default: "azure",
      },
      preferredVisualStyle: {
        type: String,
        enum: ["diagram", "graph", "flowchart", "animation"],
        default: "diagram",
      },
    },
  },
  {
    // timestamps: true adds two fields automatically:
    // - createdAt: Date — set once when document is first created
    // - updatedAt: Date — updated every time document is modified
    timestamps: true,
  }
);

// ── Indexes ──────────────────────────────────────────────────────────────────
// `unique: true` above already creates indexes on email and username.
// If you needed a compound index: userSchema.index({ email: 1, username: 1 });

// ── Export Model ─────────────────────────────────────────────────────────────
// mongoose.model("User", userSchema) does two things:
// 1. Creates a model class called "User"
// 2. Tells Mongoose to use the "users" collection (auto-pluralizes)
module.exports = mongoose.model("User", userSchema);
