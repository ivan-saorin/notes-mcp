#!/usr/bin/env python3
"""
Unified server runner for CapRover deployment
Serves both MCP and Web interface on the same port
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from remote_mcp.unified_server import app
import uvicorn

if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"\n{'='*60}")
    print("Starting Unified Server (MCP + Web Interface)")
    print(f"{'='*60}")
    print(f"Server URL: http://{host}:{port}")
    print(f"Web Interface: http://{host}:{port}/")
    print(f"MCP Endpoint: http://{host}:{port}/mcp")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"{'='*60}\n")
    
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)
