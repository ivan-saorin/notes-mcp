#!/usr/bin/env python3
"""
Run both MCP server and Web server
"""

import sys
import os
import asyncio
import threading
import logging
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from remote_mcp.server import app as mcp_app
from remote_mcp.web_app import web_app
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_mcp_server():
    """Run the MCP server in a thread"""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting MCP Server on {host}:{port}/mcp")
    uvicorn.run(mcp_app, host=host, port=port, log_level="info")

def run_web_server():
    """Run the web server in a thread"""
    port = int(os.environ.get("WEB_PORT", 3100))
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    
    print(f"Starting Web Server on {host}:{port}")
    uvicorn.run(web_app, host=host, port=port, log_level="info")

def main():
    print(f"\n{'='*60}")
    print("Starting Notes Management System")
    print(f"{'='*60}")
    print("MCP Server: http://localhost:8000/mcp")
    print("Web UI:     http://localhost:3100/")
    print(f"{'='*60}\n")
    
    # Create threads for both servers
    mcp_thread = threading.Thread(target=run_mcp_server)
    web_thread = threading.Thread(target=run_web_server)
    
    # Start both servers
    mcp_thread.start()
    time.sleep(1)  # Small delay to ensure MCP starts first
    web_thread.start()
    
    try:
        # Wait for both threads
        mcp_thread.join()
        web_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()
