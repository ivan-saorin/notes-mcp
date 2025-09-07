#!/usr/bin/env python3
"""
Run the Notes Web Server
"""

import sys
import os
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from remote_mcp.web_app import web_app
import uvicorn

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    port = int(os.environ.get("WEB_PORT", 3100))
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    
    print(f"\n{'='*60}")
    print("Starting Notes Web Server")
    print(f"{'='*60}")
    print(f"Web UI available at: http://localhost:{port}/")
    print(f"Listening on: {host}:{port}")
    print(f"{'='*60}\n")
    
    try:
        uvicorn.run(web_app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\nWeb server stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Web server error: {e}")
        sys.exit(1)
