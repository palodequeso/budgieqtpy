#!/bin/bash
# Deploy Budgie web Docker image to a remote server
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE_NAME="budgie-web"
IMAGE_TAG="${2:-latest}"
CONTAINER_NAME="budgie-app"
REMOTE_DATA_DIR="/home/\${REMOTE_USER}/budgie"

usage() {
    echo "Usage: $0 <user@host> [image-tag]"
    echo ""
    echo "Deploys the Budgie web app Docker image to a remote server."
    echo ""
    echo "Arguments:"
    echo "  user@host   SSH destination (e.g., deploy@192.168.1.50)"
    echo "  image-tag   Docker image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0 douglas@192.168.1.4"
    echo "  $0 deploy@myserver.local v1.2.0"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

SSH_TARGET="$1"
REMOTE_USER="${SSH_TARGET%%@*}"
REMOTE_HOST="${SSH_TARGET##*@}"

echo "======================================"
echo "Deploying Budgie Web to $SSH_TARGET"
echo "======================================"

# Check that the image exists locally (try with sg docker for group perms)
DOCKER_CMD="docker"
if ! $DOCKER_CMD image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null 2>&1; then
    if sg docker -c "docker image inspect ${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null 2>&1; then
        DOCKER_CMD="sg docker -c docker"
    else
        echo "Image ${IMAGE_NAME}:${IMAGE_TAG} not found locally."
        echo "Run scripts/build-web.sh first."
        exit 1
    fi
fi

echo ""
echo "Saving Docker image..."
ARCHIVE="$HOME/budgie-web-${IMAGE_TAG}.tar.gz"
rm -f "$ARCHIVE"
sg docker -c "docker save ${IMAGE_NAME}:${IMAGE_TAG} -o ${ARCHIVE%.gz}"
gzip -f "${ARCHIVE%.gz}"
ARCHIVE_SIZE=$(du -h "$ARCHIVE" | cut -f1)
echo "Image archive: $ARCHIVE ($ARCHIVE_SIZE)"

echo ""
echo "Uploading to $SSH_TARGET... (you may be prompted for your password)"
scp "$ARCHIVE" "${SSH_TARGET}:/tmp/budgie-web-${IMAGE_TAG}.tar.gz"

echo ""
echo "Deploying on remote server... (you may be prompted for your password again)"
ssh -t "$SSH_TARGET" bash -s <<REMOTE_SCRIPT
set -e

REMOTE_DATA_DIR="/home/${REMOTE_USER}/budgie"

echo "Loading Docker image..."
docker load < /tmp/budgie-web-${IMAGE_TAG}.tar.gz
rm -f /tmp/budgie-web-${IMAGE_TAG}.tar.gz

# Ensure data directory exists
mkdir -p "\${REMOTE_DATA_DIR}"
touch "\${REMOTE_DATA_DIR}/budgie.db"
mkdir -p "\${REMOTE_DATA_DIR}/schedule-spreadsheets"

# Stop and remove existing container if present
if docker ps -aq -f name=${CONTAINER_NAME} | grep -q .; then
    echo "Stopping existing container..."
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
fi

echo "Starting new container..."
docker run -d \\
    --name ${CONTAINER_NAME} \\
    --restart unless-stopped \\
    --network host \\
    -v "\${REMOTE_DATA_DIR}/budgie.db:/app/budgie.db:rw" \\
    -v "\${REMOTE_DATA_DIR}/schedule-spreadsheets:/app/schedule-spreadsheets:rw" \\
    -e DATABASE_PATH=/app/budgie.db \\
    -e PYTHONUNBUFFERED=1 \\
    -e PORT=8002 \\
    ${IMAGE_NAME}:${IMAGE_TAG}

echo ""
echo "Container status:"
docker ps -f name=${CONTAINER_NAME} --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
REMOTE_SCRIPT

# Clean up local archive
rm -f "$ARCHIVE"

echo ""
echo "======================================"
echo "Deployment complete!"
echo "======================================"
echo "App running at: http://${REMOTE_HOST}:8002"
echo ""
echo "Manage remotely:"
echo "  ssh $SSH_TARGET 'docker logs -f $CONTAINER_NAME'"
echo "  ssh $SSH_TARGET 'docker restart $CONTAINER_NAME'"
echo "  ssh $SSH_TARGET 'docker stop $CONTAINER_NAME'"
echo "======================================"
