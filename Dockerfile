# Multi-stage build for React frontend + Python backend

# ===== Stage 1: Build React Frontend =====
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build the React app
RUN npm run build

# ===== Stage 2: Python Backend =====
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python application code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
COPY --from=frontend-builder /app/frontend/index.html ./frontend/index.html
COPY --from=frontend-builder /app/frontend/index.scss ./frontend/index.scss

# Expose port
EXPOSE 8000

# Create directory for database (will be mounted as volume)
RUN mkdir -p /app/data

# Run the server
CMD ["python", "serve.py"]
