#!/usr/bin/env python3
"""
Remote MCP Server v2 - Using FastMCP like Akasha
FIXED: No more 307 redirects
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("remote-mcp")

# Initialize MCP server
mcp = FastMCP("Atlas Remote MCP")
mcp.description = "Remote MCP server with calculator, text processing, task management, and notes management"

# Simple task database
tasks_db = {}
task_counter = 0

# Simple notes database
notes_db = {}
note_counter = 0

# ============================================================================
# SYSTEM INFO
# ============================================================================

@mcp.tool()
async def system_info() -> Dict[str, Any]:
    """Get system information and server status"""
    return {
        "server_name": "Atlas Remote MCP Prototype",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "transport": "streamable-http",
        "features": ["calculator", "text_processing", "task_management", "notes_management"]
    }

# ============================================================================
# CALCULATOR TOOLS
# ============================================================================

@mcp.tool()
async def calculate(
    a: float,
    b: float,
    operation: str = "add"
) -> Dict[str, Any]:
    """
    Perform mathematical calculations
    
    Args:
        a: First number
        b: Second number
        operation: One of add, subtract, multiply, divide, power, modulo
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float('inf'),
        "power": lambda x, y: x ** y,
        "modulo": lambda x, y: x % y if y != 0 else None
    }
    
    if operation in operations:
        result = operations[operation](a, b)
        return {
            "operation": operation,
            "a": a,
            "b": b,
            "result": result,
            "expression": f"{a} {operation} {b} = {result}"
        }
    else:
        return {
            "error": f"Unknown operation: {operation}",
            "valid_operations": list(operations.keys())
        }

# ============================================================================
# TEXT ANALYSIS
# ============================================================================

@mcp.tool()
async def text_analyze(text: str) -> Dict[str, Any]:
    """Analyze text and return statistics"""
    words = text.split()
    sentences = text.split('.')
    
    return {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "unique_words": len(set(words)),
        "preview": text[:100] + "..." if len(text) > 100 else text
    }

# ============================================================================
# TASK MANAGEMENT
# ============================================================================

@mcp.tool()
async def task_create(
    title: str,
    description: str = "",
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Create a new task
    
    Args:
        title: Task title
        description: Task description
        priority: One of low, medium, high
    """
    global task_counter, tasks_db
    
    task_counter += 1
    task_id = f"task_{task_counter}"
    
    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    tasks_db[task_id] = task
    logger.info(f"Created task: {task_id}")
    return task

@mcp.tool()
async def task_list(
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all tasks
    
    Args:
        status: Optional filter - pending, in_progress, or completed
    """
    tasks = list(tasks_db.values())
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return tasks

@mcp.tool()
async def task_update(
    task_id: str,
    status: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update a task
    
    Args:
        task_id: Task ID to update
        status: New status (pending, in_progress, completed)
        title: New title
        description: New description
        priority: New priority
    """
    if task_id not in tasks_db:
        return {"error": f"Task {task_id} not found"}
    
    task = tasks_db[task_id]
    
    if status:
        task["status"] = status
    if title:
        task["title"] = title
    if description:
        task["description"] = description
    if priority:
        task["priority"] = priority
    
    task["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Updated task: {task_id}")
    return task

@mcp.tool()
async def task_delete(task_id: str) -> Dict[str, Any]:
    """
    Delete a task
    
    Args:
        task_id: Task ID to delete
    """
    if task_id not in tasks_db:
        return {"error": f"Task {task_id} not found"}
    
    del tasks_db[task_id]
    logger.info(f"Deleted task: {task_id}")
    return {"success": True, "message": f"Task {task_id} deleted"}

# ============================================================================
# NOTES MANAGEMENT
# ============================================================================

@mcp.tool()
async def list_notes(tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Lists all notes, or search notes with tags
    
    Args:
        tags: Optional tags to filter notes
    """
    notes = list(notes_db.values())
    
    # Filter by tags if provided
    if tags:
        notes = [n for n in notes if any(tag in n.get("tags", []) for tag in tags)]
    
    # Return simplified list for overview
    simplified_notes = [{
        "id": n["id"],
        "title": n["title"],
        "summary": n["summary"],
        "tags": n["tags"]
    } for n in notes]
    
    return {
        "count": len(notes),
        "notes": simplified_notes
    }

@mcp.tool()
async def get_note(note_id: str) -> Dict[str, Any]:
    """
    Retrieves a specific note by its ID
    
    Args:
        note_id: ID of the note to retrieve
    """
    if note_id not in notes_db:
        return {"error": f"Note with ID '{note_id}' not found"}
    
    return notes_db[note_id]

@mcp.tool()
async def write_note(
    title: str,
    content: str,
    summary: str,
    tags: Optional[List[str]] = None,
    note_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates or updates a note
    
    Args:
        title: Title of the note
        content: Content of the note
        summary: Short summary of the note
        tags: Tags for the note
        note_id: Optional ID for updating existing note
    """
    global note_counter, notes_db
    
    if not note_id:
        # Create new note ID
        note_counter += 1
        # Generate ID similar to MCPNotes format
        base_id = title.lower().replace(" ", "-")[:30]
        note_id = f"{base_id}-{note_counter}"
    
    note = {
        "id": note_id,
        "title": title,
        "summary": summary,
        "tags": tags or [],
        "content": content,
        "created_at": notes_db.get(note_id, {}).get("created_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat()
    }
    
    is_update = note_id in notes_db
    notes_db[note_id] = note
    
    action = "updated" if is_update else "created"
    logger.info(f"{action.capitalize()} note: {note_id}")
    
    return {
        "success": True,
        "action": action,
        "note": note
    }

@mcp.tool()
async def delete_note(note_id: str) -> Dict[str, Any]:
    """
    Deletes a specific note by its ID
    
    Args:
        note_id: ID of the note to delete
    """
    if note_id not in notes_db:
        return {"error": f"Note with ID '{note_id}' not found"}
    
    del notes_db[note_id]
    logger.info(f"Deleted note: {note_id}")
    return {"success": True, "message": f"Note with ID '{note_id}' has been deleted"}

# ============================================================================
# RESOURCES - For notes subscription support
# ============================================================================

@mcp.resource("notes://notes/{note_id}")
async def get_note_resource(note_id: str) -> str:
    """
    Get note content as a resource
    
    Args:
        note_id: Note identifier
    """
    if note_id not in notes_db:
        return f"Note not found: {note_id}"
    
    note = notes_db[note_id]
    # Return note as formatted JSON string
    return json.dumps(note, indent=2)

# ============================================================================
# ASGI APPLICATION WITH HEALTH CHECK
# ============================================================================

async def health_check(request):
    """Health check endpoint for CapRover"""
    return JSONResponse(
        {"status": "healthy", "service": "Atlas Remote MCP", "version": "2.0.0"},
        status_code=200
    )

# Create MCP app with path="/mcp" - this tells FastMCP where to expect requests
try:
    if hasattr(mcp, 'http_app'):
        # THIS IS THE KEY: Tell FastMCP to expect requests at /mcp
        mcp_app = mcp.http_app()
        logger.info("Created MCP app with /mcp path")
    elif hasattr(mcp, 'streamable_http_app'):
        mcp_app = mcp.streamable_http_app()
        logger.warning("Using older streamable_http_app() - path parameter may not be supported")
    else:
        raise AttributeError("No HTTP app method found in FastMCP")
    
except Exception as e:
    logger.error(f"Failed to create MCP HTTP app: {e}")
    raise

# Create main Starlette app with health check
app = Starlette(
    lifespan=mcp_app.lifespan,
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/", health_check, methods=["GET"]),  # Root health check
        Route("/mcp", mcp_app, methods=["POST", "GET"]),  # MCP endpoint
        Route("/mcp/", mcp_app, methods=["POST", "GET"]),  # MCP endpoint
    ]
)

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Get configuration from environment
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Atlas Remote MCP Server v2.0.0")
    logger.info(f"Server will be available at {host}:{port}/mcp")
    logger.info(f"Health check at {host}:{port}/health (if supported by FastMCP)")
    

    # FastMCP's StreamableHTTPSessionManager task group was not initialized. 
    # This commonly occurs when the FastMCP application's lifespan is not passed to the parent ASGI application (e.g., FastAPI or Starlette). 
    # Please ensure you are setting `lifespan=mcp_app.lifespan` in your parent app's constructor, where `mcp_app` is the application instance returned by `fastmcp_instance.http_app()`. 
    # For more details, see the FastMCP ASGI integration documentation: https://gofastmcp.com/deployment/asgi\nOriginal error: Task group is not initialized. 
    # Make sure to use run().

    try:
        # Run the HTTP server directly with the MCP app
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
