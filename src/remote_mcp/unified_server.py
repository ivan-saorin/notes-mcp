#!/usr/bin/env python3
"""
Unified server that serves both MCP and Web interface on the same port
Perfect for CapRover deployment
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Import both apps
from remote_mcp.server import app as mcp_app, notes_db, note_counter
from remote_mcp.web_app import (
    render_home_page, 
    create_or_update_note_handler, 
    delete_note_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("unified-server")

# ============================================================================
# Health Check
# ============================================================================

async def health_check(request):
    """Health check endpoint for CapRover"""
    return JSONResponse({
        "status": "healthy",
        "service": "Notes MCP Server with Web UI",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "mcp": "available at /mcp",
            "web": "available at /"
        }
    }, status_code=200)

# ============================================================================
# Unified Routes
# ============================================================================

routes = [
    # Health check
    Route("/health", health_check, methods=["GET"]),
    
    # Web interface routes (must come before MCP catch-all)
    Route("/", render_home_page, methods=["GET"]),
    Route("/notes", create_or_update_note_handler, methods=["POST"]),
    Route("/notes/{id}", delete_note_handler, methods=["DELETE"]),
    
    # MCP routes - mount the MCP app under /mcp
    Mount("/mcp", mcp_app),
]

# ============================================================================
# Create Unified App
# ============================================================================

# Middleware
middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
]

# Create the unified app
app = Starlette(
    routes=routes,
    middleware=middleware
    # MCP app handles its own lifespan internally when mounted
)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Get configuration from environment
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Unified Server (MCP + Web)")
    logger.info(f"{'='*50}")
    logger.info(f"Server: http://{host}:{port}")
    logger.info(f"MCP Endpoint: http://{host}:{port}/mcp")
    logger.info(f"Web Interface: http://{host}:{port}/")
    logger.info(f"Health Check: http://{host}:{port}/health")
    logger.info(f"{'='*50}")
    
    try:
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
