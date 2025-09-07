#!/usr/bin/env python3
"""
Notes Web Server - A web-based note-taking service
Port of MCPNotes web interface to Python
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Import shared notes database from server
from .server import notes_db, note_counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("notes-web")

# ============================================================================
# HTML Utilities
# ============================================================================

def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))

# ============================================================================
# Service Layer - Same as MCPNotes
# ============================================================================

async def get_all_notes() -> List[Dict[str, Any]]:
    """Get all notes from the database"""
    return list(notes_db.values())

async def create_or_update_note(note: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a note"""
    global note_counter
    
    note_id = note.get("id")
    
    if not note_id or note_id not in notes_db:
        # Create new note - ensure unique ID
        if not note_id:
            note_counter += 1
            base_id = note["title"].lower().replace(" ", "-")[:30]
            note_id = f"{base_id}-{note_counter}"
        note["id"] = note_id
        note["created_at"] = datetime.now().isoformat()
    
    note["updated_at"] = datetime.now().isoformat()
    notes_db[note_id] = note
    
    return note

async def delete_note(note_id: str) -> bool:
    """Delete a note by ID"""
    if note_id in notes_db:
        del notes_db[note_id]
        return True
    return False

# ============================================================================
# Controllers - Same as MCPNotes
# ============================================================================

async def render_home_page(request: Request) -> HTMLResponse:
    """Render the home page with all notes"""
    try:
        notes = await get_all_notes()
        
        header = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Notes App</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
      <div class="container mx-auto p-4">
        <div class="flex justify-between items-center mb-4">
          <h1 class="text-2xl font-bold">Notes</h1>
          <button id="createBtn" class="px-4 py-2 bg-blue-500 text-white rounded">Create Note</button>
        </div>
        <div id="notesList">
    """
        
        footer = """
        </div>
      </div>

      <!-- Native Modal -->
      <dialog id="modal" class="p-4 rounded bg-white w-1/2">

        <form method="POST" action="/notes" class="flex flex-col space-y-4">
          <h2 id="modalTitle" class="text-xl font-semibold">Create Note</h2>
          <input type="text" name="id" id="id" placeholder="Id" required class="border p-2 rounded">
          <input type="text" name="title" id="title" placeholder="Title" required class="border p-2 rounded">
          <input type="text" name="summary" id="summary" placeholder="Summary" required class="border p-2 rounded">
          <input type="text" name="tags" id="tags" placeholder="Tags (comma separated)" class="border p-2 rounded">
          <textarea name="content" id="content" rows="25" placeholder="Content" required class="border p-2 rounded"></textarea>
          <div class="flex justify-end space-x-2">
            <button type="submit" class="px-4 py-2 bg-green-500 text-white rounded">Save</button>
            <button type="button" id="cancelBtn" class="px-4 py-2 bg-gray-300 rounded">Cancel</button>
          </div>
        </form>
      </dialog>

      <script>
        const createBtn = document.getElementById('createBtn');
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const cancelBtn = document.getElementById('cancelBtn');

        createBtn.addEventListener('click', () => {
          modalTitle.textContent = 'Create Note';
          document.getElementById('id').value = '';
          document.getElementById('title').value = '';
          document.getElementById('summary').value = '';
          document.getElementById('tags').value = '';
          document.getElementById('content').value = '';
          modal.showModal();
        });

        cancelBtn.addEventListener('click', () => {
          modal.close();
        });

        function openEditModal(note) {
          modalTitle.textContent = 'Edit Note';
          document.getElementById('id').value = note.id;
          document.getElementById('title').value = note.title;
          document.getElementById('summary').value = note.summary;
          document.getElementById('tags').value = note.tags.join(',');
          document.getElementById('content').value = note.content;
          modal.showModal();
        }

        function confirmDelete(id) {
          if (confirm('Are you sure you want to delete this note?')) {
            fetch('/notes/' + id, { method: 'DELETE' })
              .then(() => location.reload());
          }
        }
      </script>
    </body>
    </html>
    """
        
        notes_html = ""
        for note in notes:
            note_json = escape_html(json.dumps(note))
            notes_html += f"""
      <div class="bg-white p-4 rounded shadow mb-2">
        <h2 class="text-xl font-sembold">{escape_html(note['title'])}</h2>
        <p class="text-gray-600">{escape_html(note['summary'])}</p>
        <div class="mt-2">
          <button onclick='openEditModal({note_json})' class="px-3 py-1 bg-yellow-500 text-white rounded mr-2">Edit</button>
          <button onclick="confirmDelete('{escape_html(note['id'])}')" class="px-3 py-1 bg-red-500 text-white rounded">Delete</button>
        </div>
      </div>
    """
        
        return HTMLResponse(header + notes_html + footer)
        
    except Exception as e:
        logger.error(f"Error rendering home page: {e}")
        return HTMLResponse("Internal Server Error", status_code=500)

async def create_or_update_note_handler(request: Request) -> HTMLResponse:
    """Handle note creation/update"""
    try:
        form_data = await request.form()
        
        # Parse tags from comma-separated string
        tags_str = form_data.get("tags", "")
        tags = []
        if tags_str and tags_str.strip():
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        # Create note object
        note = {
            "id": form_data.get("id", ""),
            "title": form_data.get("title", ""),
            "summary": form_data.get("summary", ""),
            "content": form_data.get("content", ""),
            "tags": tags
        }
        
        # Validate required fields
        if not note["title"] or not note["summary"] or not note["content"]:
            return HTMLResponse("Missing required fields", status_code=400)
        
        await create_or_update_note(note)
        
        # Redirect to home page
        return HTMLResponse(
            content="",
            status_code=303,
            headers={"Location": "/"}
        )
        
    except Exception as e:
        logger.error(f"Error creating/updating note: {e}")
        return HTMLResponse("Internal Server Error", status_code=500)

async def delete_note_handler(request: Request) -> JSONResponse:
    """Handle note deletion"""
    try:
        note_id = request.path_params.get("id")
        if not note_id:
            return JSONResponse({"error": "Note ID required"}, status_code=400)
        
        deleted = await delete_note(note_id)
        if deleted:
            return JSONResponse({"status": "Deleted"})
        else:
            return JSONResponse({"error": "Note not found"}, status_code=404)
            
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        return JSONResponse({"error": "Internal Server Error"}, status_code=500)

# ============================================================================
# Routes
# ============================================================================

routes = [
    Route("/", render_home_page, methods=["GET"]),
    Route("/notes", create_or_update_note_handler, methods=["POST"]),
    Route("/notes/{id}", delete_note_handler, methods=["DELETE"]),
]

# ============================================================================
# Application
# ============================================================================

# Create web app with CORS middleware
middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
]

web_app = Starlette(routes=routes, middleware=middleware)

# ============================================================================
# Standalone Server
# ============================================================================

if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.environ.get("WEB_PORT", 3100))
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    
    logger.info(f"Starting Notes Web Server on {host}:{port}")
    logger.info("Access the web interface at http://localhost:3100/")
    
    try:
        uvicorn.run(web_app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
    except Exception as e:
        logger.error(f"Web server error: {e}")
