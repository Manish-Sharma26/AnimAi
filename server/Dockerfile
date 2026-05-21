# ── AnimAI API Server Dockerfile ──────────────────────────────────────────
# Multi-stage build: install deps → copy code → run
#
# Build:  docker build -t animai-api ./server
# Run:    docker run -p 3001:3001 animai-api

FROM node:22-alpine AS base
WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy source code
COPY . .

# Expose port
EXPOSE 3001

# Start server
CMD ["node", "src/index.js"]
