#!/bin/bash
# Create clean directory structure for v2

# Main directories
mkdir -p src/remote_mcp
mkdir -p deploy/ngrok/config
mkdir -p deploy/self-signed/config  
mkdir -p deploy/letsencrypt/config
mkdir -p docker
mkdir -p config
mkdir -p scripts
mkdir -p tests
mkdir -p docs

echo "Directory structure created successfully!"
