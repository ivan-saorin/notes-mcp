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
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Import event system first
from .event_manager import event_manager

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
    
    # Import server components AFTER event manager is ready
    from .server import app as mcp_app
    
    # Start MCP lifespan if it exists
    if hasattr(mcp_app, 'lifespan'):
        async with mcp_app.lifespan(app):
            logger.info("MCP Server started with lifespan")
            yield
    else:
        logger.info("MCP Server started")
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
# Import Components (delayed to avoid circular imports)
# ============================================================================

def get_app_components():
    """Import app components after event manager is initialized"""
    from .server import app as mcp_app
    from .web_app import routes as web_routes, render_home_page, create_or_update_note_handler, delete_note_handler, get_notes_api, get_note_api
    from .sse_handler import sse_endpoint
    
    return mcp_app, web_routes, sse_endpoint, render_home_page, create_or_update_note_handler, delete_note_handler, get_notes_api, get_note_api

async def handle_mcp_endpoint(request):
    """Handle MCP endpoint requests"""
    from .server import app as mcp_app
    
    # Forward the request to the MCP app
    if hasattr(mcp_app, '__call__'):
        # The MCP app should handle the request
        return await mcp_app(request.scope, request.receive, request._send)
    else:
        # If not callable, return error
        from starlette.responses import JSONResponse
        return JSONResponse({"error": "MCP endpoint not available"}, status_code=503)

# ============================================================================
# Create Unified Application
# ============================================================================

def create_unified_app():
    """Create the unified application with all components"""
    
    # Import components
    mcp_app, web_routes, sse_endpoint, render_home_page, create_or_update_note_handler, delete_note_handler, get_notes_api, get_note_api = get_app_components()
    
    # Combined routes
    routes = [
        # Health check
        Route("/health", health_check, methods=["GET"]),
        Route("/", root_redirect, methods=["GET"]),
        
        # SSE events endpoint
        Route("/events", sse_endpoint, methods=["GET"]),
        
        # Web interface routes
        Route("/app", render_home_page, methods=["GET"]),
        Route("/app/", render_home_page, methods=["GET"]),
        Route("/notes", create_or_update_note_handler, methods=["POST"]),
        Route("/notes/{id}", delete_note_handler, methods=["DELETE"]),
        Route("/api/notes", get_notes_api, methods=["GET"]),
        Route("/api/notes/{id}", get_note_api, methods=["GET"]),
        
        # MCP endpoint - Mount the MCP app properly
        Route("/mcp", mcp_app, methods=["POST", "GET"]),
        Route("/mcp/", mcp_app, methods=["POST", "GET"]),
    ]
    
    # Middleware
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
    
    # Create app
    app = Starlette(
        routes=routes,
        middleware=middleware,
        lifespan=unified_lifespan,
        debug=os.environ.get("DEBUG", "").lower() == "true"
    )
    
    return app

# Create the app
unified_app = create_unified_app()

# Export as 'app' for compatibility
app = unified_app

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
    logger.info(f"Web interface (alt): http://{host}:{port}/")
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
