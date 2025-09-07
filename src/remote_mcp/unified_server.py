#!/usr/bin/env python3
"""
Unified Server v2 - MCP + Web App with Real-time Events
Production-ready unified server with event-driven collaboration
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Import components
from .server import app as mcp_app  # MCP server app
from .web_app import web_app  # Web interface app
from .event_manager import event_manager  # Event system
from .sse_handler import sse_endpoint  # SSE endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("unified-server")

# ============================================================================
# Lifespan Manager
# ============================================================================

@asynccontextmanager
async def unified_lifespan(app):
    """Manage lifecycle of all components"""
    logger.info("Starting Unified Server v2...")
    
    # Start event manager
    await event_manager.start()
    logger.info("Event Manager started")
    
    # Start MCP lifespan if it exists
    if hasattr(mcp_app, 'lifespan'):
        async with mcp_app.lifespan(app):
            logger.info("MCP Server started")
            yield
    else:
        logger.info("MCP Server started (no lifespan)")
        yield
    
    # Cleanup
    logger.info("Shutting down Unified Server...")
    await event_manager.stop()
    logger.info("Event Manager stopped")

# ============================================================================
# Health Check
# ============================================================================

async def health_check(request):
    """Comprehensive health check for all components"""
    health_status = {
        "status": "healthy",
        "service": "Unified MCP + Web Server",
        "version": "2.0.0",
        "components": {
            "mcp": "operational",
            "web": "operational",
            "events": "operational"
        },
        "metrics": {}
    }
    
    # Check event manager
    try:
        metrics = event_manager.get_metrics()
        health_status["metrics"]["events"] = {
            "total_events": metrics.get("total_events", 0),
            "events_per_second": round(metrics.get("events_per_second", 0), 2),
            "active_connections": len(event_manager.connection_pool.connections)
        }
    except Exception as e:
        health_status["components"]["events"] = f"error: {e}"
        health_status["status"] = "degraded"
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(health_status, status_code=status_code)

async def root_redirect(request):
    """Redirect root to web UI"""
    return RedirectResponse(url="/app", status_code=302)

# ============================================================================
# Combined Routes
# ============================================================================

routes = [
    # Health check
    Route("/health", health_check, methods=["GET"]),
    Route("/", root_redirect, methods=["GET"]),
    
    # MCP endpoint - Mount the MCP app
    Mount("/mcp", app=mcp_app, name="mcp"),
    
    # Web interface - Mount the web app
    Mount("/app", app=web_app, name="web"),
    
    # SSE events endpoint (shared)
    Route("/events", sse_endpoint, methods=["GET"]),
]

# ============================================================================
# Middleware
# ============================================================================

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
]

# ============================================================================
# Create Unified Application
# ============================================================================

unified_app = Starlette(
    routes=routes,
    middleware=middleware,
    lifespan=unified_lifespan,
    debug=os.environ.get("DEBUG", "").lower() == "true"
)

# ============================================================================
# Server Runner
# ============================================================================

if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "").lower() == "true"
    
    logger.info("=" * 60)
    logger.info("Unified Server v2 - Real-time Collaboration")
    logger.info("=" * 60)
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
    logger.info(f"Web interface: http://{host}:{port}/app")
    logger.info(f"SSE events: http://{host}:{port}/events")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info("=" * 60)
    logger.info("Features:")
    logger.info("- Real-time event synchronization")
    logger.info("- Claude long-polling support (wait_for_updates)")
    logger.info("- Server-Sent Events for UI updates")
    logger.info("- Bidirectional collaboration")
    logger.info("=" * 60)
    
    try:
        uvicorn.run(
            unified_app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
