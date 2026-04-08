#!/bin/bash
# Build Docker image for Budgie web app (FastAPI backend + React frontend)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE_NAME="budgie-web"
IMAGE_TAG="${1:-latest}"

echo "======================================"
echo "Building Budgie Web Docker Image"
echo "======================================"

# Check for docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

cd "$PROJECT_DIR"

echo "Building image: ${IMAGE_NAME}:${IMAGE_TAG}"
DOCKER_BUILDKIT=0 docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo ""
echo "======================================"
echo "Build complete!"
echo "======================================"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Run locally:"
echo "  docker-compose up -d"
echo ""
echo "Or standalone:"
echo "  docker run -d -p 8000:8000 -v \$(pwd)/budgie.db:/app/budgie.db ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Access at: http://localhost:8000"
echo "======================================"
