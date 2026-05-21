# ── AnimAI React Client Dockerfile ────────────────────────────────────────
# Dev server for development. For production, build static files and
# serve with nginx instead.
#
# Build:  docker build -t animai-client ./client
# Run:    docker run -p 5173:5173 animai-client

FROM node:22-alpine
WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start Vite with host flag so it's accessible outside container
CMD ["npx", "vite", "--host", "0.0.0.0"]
