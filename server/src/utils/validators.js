/**
 * Request Validators (Joi)
 * 
 * WHY VALIDATE AT THE ROUTE LEVEL?
 * - Mongoose validation runs DURING save — if data is bad, you've already
 *   hit the database layer. Joi catches it at the HTTP layer — cheaper, faster.
 * - Joi gives much better error messages than Mongoose validation errors.
 * - Think of it as: Joi = bouncer at the door, Mongoose = safety net inside.
 * 
 * INTERVIEW TIP:
 * "I validate at two layers: Joi at the route level for user-facing errors,
 *  and Mongoose schema validation as a safety net at the database level.
 *  This defense-in-depth approach ensures no bad data reaches MongoDB
 *  even if a code path bypasses route validation."
 */

const Joi = require("joi");

// ── Animation Validators ─────────────────────────────────────────────────────

const createAnimationSchema = Joi.object({
  prompt: Joi.string().trim().min(3).max(2000).required().messages({
    "string.min": "Prompt must be at least 3 characters",
    "string.max": "Prompt must be under 2000 characters",
    "any.required": "Prompt is required",
  }),
});

const updatePlanSchema = Joi.object({
  plan: Joi.object().required().messages({
    "any.required": "Plan object is required",
  }),
  status: Joi.string().valid("approved").optional(),
});

// ── Feedback Validators ──────────────────────────────────────────────────────

const createFeedbackSchema = Joi.object({
  vote: Joi.string().valid("up", "down").required().messages({
    "any.only": "Vote must be 'up' or 'down'",
    "any.required": "Vote is required",
  }),
  comment: Joi.string().trim().max(500).optional().allow("", null),
});

// ── Pagination Validator ─────────────────────────────────────────────────────

const paginationSchema = Joi.object({
  page: Joi.number().integer().min(1).default(1),
  limit: Joi.number().integer().min(1).max(50).default(10),
}).unknown(true); // allow other query params

// ── Helper: validate and return clean data or throw ──────────────────────────

const validate = (schema, data) => {
  const { error, value } = schema.validate(data, {
    abortEarly: false, // return ALL errors, not just the first
    stripUnknown: true, // remove fields not in schema
  });

  if (error) {
    const messages = error.details.map((d) => d.message).join("; ");
    const err = new Error(messages);
    err.status = 400;
    throw err;
  }

  return value; // cleaned, validated data
};

module.exports = {
  createAnimationSchema,
  updatePlanSchema,
  createFeedbackSchema,
  paginationSchema,
  validate,
};
