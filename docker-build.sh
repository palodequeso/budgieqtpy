#!/bin/bash
# Build script for Budgie Docker container

echo "================================================"
echo "Building Budgie Docker Container"
echo "================================================"

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: docker-compose is not installed"
    echo "Using docker build instead..."
    docker build -t budgie-app .
else
    echo "Using docker-compose to build..."
    docker-compose build
fi

echo ""
echo "================================================"
echo "Build complete!"
echo "================================================"
echo ""
echo "To start the application:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "Access the app at: http://localhost:8000"
echo "================================================"
