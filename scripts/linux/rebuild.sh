#!/bin/bash
# Rebuild script for Remote MCP Server v2

set -e

echo "🔨 Rebuilding Remote MCP Server v2..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project root (v2) - script is in v2/scripts/linux/
cd "$SCRIPT_DIR/../.."

echo "Building from: $(pwd)"
echo ""

# Clean up old containers
echo "🧹 Cleaning up old containers..."
docker-compose -f deploy/docker/docker-compose.yml down 2>/dev/null || true

# Remove old image
echo "🗑️  Removing old image..."
docker rmi atlas-remote-mcp:v2 2>/dev/null || true

# Rebuild image
echo "🏗️  Building new image..."
docker build -f deploy/docker/Dockerfile -t atlas-remote-mcp:v2 .

# Start services
echo "🚀 Starting services..."
docker-compose -f deploy/docker/docker-compose.yml up -d

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
sleep 5

# Check health
echo "❤️  Checking health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health check endpoint not ready yet"

echo "✅ Rebuild complete!"
echo ""
echo "Service is running at: http://localhost:8000"
echo "MCP endpoint: http://localhost:8000/mcp"
echo ""
echo "Run 'docker-compose -f deploy/docker/docker-compose.yml logs -f' to see logs"
