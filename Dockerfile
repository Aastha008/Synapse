# ── Multi-Stage Dockerfile for Synapse ──────────────────────────────
# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend & Runtime
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source code
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["python", "backend/run.py"]
