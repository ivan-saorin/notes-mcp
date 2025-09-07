#!/usr/bin/env python3
"""
Direct runner for the remote MCP server
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the server
if __name__ == "__main__":
    from remote_mcp.server import app
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Atlas Remote MCP Server v2.0.0")
    print("-" * 60)
    print(f"Server endpoints:")
    print(f"  Health check: http://{host}:{port}/")
    print(f"  Health check: http://{host}:{port}/health")
    print(f"  MCP endpoint: http://{host}:{port}/mcp")
    print(f"")
    print(f"Transport: streamable-http")
    print(f"Test with: npx @modelcontextprotocol/inspector --url http://localhost:{port}/mcp")
    print("-" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")
