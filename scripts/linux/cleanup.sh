#!/bin/bash
# Cleanup script for Remote MCP Server v2

set -e

echo "🧹 Cleaning up Remote MCP Server v2..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project root (v2) - script is in v2/scripts/linux/
cd "$SCRIPT_DIR/../.."

echo "Cleaning from: $(pwd)"
echo ""

# Stop and remove Docker containers
echo "🐳 Stopping Docker containers..."
docker-compose -f deploy/docker/docker-compose.yml down 2>/dev/null || true
docker-compose -f deploy/docker/docker-compose.https.yml down 2>/dev/null || true

# Remove Docker images
echo "🖼️  Removing Docker images..."
docker rmi atlas-remote-mcp:v2 2>/dev/null || true

# Clean Python cache
echo "🐍 Cleaning Python cache..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache

# Clean certificates (but ask first)
if [ -d "deploy/ssl/self-signed-working/certs" ] || [ -d "deploy/ssl/letsencrypt/config/certs" ]; then
    read -p "❓ Remove SSL certificates? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf deploy/ssl/*/certs
        rm -rf deploy/ssl/*/config/certs
        echo "  ✅ Certificates removed"
    fi
fi

# Clean logs
if [ -d "logs" ]; then
    echo "📝 Cleaning logs..."
    rm -rf logs
fi

# Clean temp files
echo "📁 Cleaning temporary files..."
find . -name "*.log" -delete 2>/dev/null || true
find . -name "*.pid" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true

echo "✨ Cleanup complete!"
echo ""
echo "Note: Virtual environments and installed packages were preserved."
echo "Run 'rm -rf venv' to remove virtual environment if needed."
