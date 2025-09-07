#!/usr/bin/env python3
"""
Notes Web Server v2 - With Real-time Event Integration
Production-ready web interface with SSE support
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

# Import event system
from .event_manager import (
    event_manager,
    EventType,
    EventPriority,
    emit_event
)

# Import SSE handler
from .sse_handler import sse_endpoint, SSE_CLIENT_JS

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
# Service Layer - With Event Emission
# ============================================================================

async def get_all_notes() -> List[Dict[str, Any]]:
    """Get all notes from the database"""
    return list(notes_db.values())

async def create_or_update_note(note: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a note with event emission"""
    global note_counter
    
    note_id = note.get("id")
    is_update = note_id and note_id in notes_db
    
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
    
    # Emit event
    event_type = EventType.UPDATE if is_update else EventType.CREATE
    ui_hint = None if is_update else "navigate_to"
    
    await event_manager.emit(
        event_type=event_type,
        source="ui",
        target="note",
        action=f"{'update' if is_update else 'create'}_note_ui",
        data=note,
        metadata={
            "ui_hint": ui_hint,
            "user": "web_user"
        },
        priority=EventPriority.HIGH
    )
    
    logger.info(f"{'Updated' if is_update else 'Created'} note: {note_id}")
    return note

async def delete_note(note_id: str) -> bool:
    """Delete a note by ID with event emission"""
    if note_id in notes_db:
        note = notes_db[note_id]
        del notes_db[note_id]
        
        # Emit delete event
        await event_manager.emit(
            event_type=EventType.DELETE,
            source="ui",
            target="note",
            action="delete_note_ui",
            data={"id": note_id, "title": note.get("title", "")},
            metadata={"user": "web_user"},
            priority=EventPriority.HIGH
        )
        
        logger.info(f"Deleted note: {note_id}")
        return True
    return False

# ============================================================================
# Controllers - Enhanced with Real-time Features
# ============================================================================

async def render_home_page(request: Request) -> HTMLResponse:
    """Render the home page with real-time event support"""
    try:
        notes = await get_all_notes()
        
        header = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Notes App - Real-time Collaboration</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        @keyframes pulse-green {{
          0%, 100% {{ background-color: rgb(34 197 94); }}
          50% {{ background-color: rgb(74 222 128); }}
        }}
        .live-indicator {{
          animation: pulse-green 2s infinite;
        }}
        .note-updating {{
          opacity: 0.7;
          transition: opacity 0.3s;
        }}
        .note-flash {{
          animation: flash 0.5s;
        }}
        @keyframes flash {{
          0%, 100% {{ background-color: white; }}
          50% {{ background-color: #fef3c7; }}
        }}
      </style>
    </head>
    <body class="bg-gray-100">
      <div class="container mx-auto p-4">
        <div class="flex justify-between items-center mb-4">
          <h1 class="text-2xl font-bold">Notes - Real-time Collaboration</h1>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div id="connectionStatus" class="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span id="connectionText" class="text-sm">Connecting...</span>
            </div>
            <button id="createBtn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Create Note</button>
          </div>
        </div>
        
        <!-- Real-time notifications -->
        <div id="notifications" class="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
        </div>
        
        <div id="notesList" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
    """
        
        footer = f"""
        </div>
      </div>

      <!-- Native Modal -->
      <dialog id="modal" class="p-4 rounded-lg bg-white shadow-xl max-w-2xl w-full">
        <form method="POST" action="/notes" class="flex flex-col space-y-4">
          <h2 id="modalTitle" class="text-xl font-semibold">Create Note</h2>
          <input type="text" name="id" id="id" placeholder="Id (auto-generated if empty)" class="border p-2 rounded">
          <input type="text" name="title" id="title" placeholder="Title" required class="border p-2 rounded">
          <input type="text" name="summary" id="summary" placeholder="Summary" required class="border p-2 rounded">
          <input type="text" name="tags" id="tags" placeholder="Tags (comma separated)" class="border p-2 rounded">
          <textarea name="content" id="content" rows="20" placeholder="Content" required class="border p-2 rounded font-mono text-sm"></textarea>
          <div class="flex justify-end space-x-2">
            <button type="submit" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">Save</button>
            <button type="button" id="cancelBtn" class="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400">Cancel</button>
          </div>
        </form>
      </dialog>

      <!-- Real-time Event Manager -->
      <script>
        {SSE_CLIENT_JS}
        
        // Initialize Event Manager
        const eventManager = new EventManagerClient('/events', {{
            channels: ['note:*', 'task:*'],
            reconnectInterval: 3000,
            maxReconnectAttempts: 20
        }});
        
        // Connection status
        eventManager.on('connected', (data) => {{
            document.getElementById('connectionStatus').className = 'w-3 h-3 bg-green-500 rounded-full live-indicator';
            document.getElementById('connectionText').textContent = 'Live';
            showNotification('Connected to real-time updates', 'success');
        }});
        
        eventManager.on('disconnected', (data) => {{
            document.getElementById('connectionStatus').className = 'w-3 h-3 bg-red-500 rounded-full';
            document.getElementById('connectionText').textContent = 'Disconnected';
        }});
        
        eventManager.on('error', (data) => {{
            document.getElementById('connectionStatus').className = 'w-3 h-3 bg-yellow-500 rounded-full';
            document.getElementById('connectionText').textContent = 'Reconnecting...';
        }});
        
        // Note events
        eventManager.on('note:create', (event) => {{
            if (event.source !== 'ui') {{
                // Note created by Claude or API
                addNoteToList(event.data);
                showNotification(`Claude created: ${{event.data.title}}`, 'info');
                
                if (event.metadata?.ui_hint === 'navigate_to') {{
                    // Flash the new note
                    setTimeout(() => {{
                        const noteEl = document.querySelector(`[data-note-id="${{event.data.id}}"]`);
                        if (noteEl) {{
                            noteEl.classList.add('note-flash');
                            noteEl.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}
                    }}, 100);
                }}
            }}
        }});
        
        eventManager.on('note:update', (event) => {{
            if (event.source !== 'ui') {{
                // Note updated by Claude or API
                updateNoteInList(event.data);
                showNotification(`Claude updated: ${{event.data.title}}`, 'info');
            }}
        }});
        
        eventManager.on('note:delete', (event) => {{
            if (event.source !== 'ui') {{
                // Note deleted by Claude or API
                removeNoteFromList(event.data.id);
                showNotification(`Claude deleted: ${{event.data.title || event.data.id}}`, 'warning');
            }}
        }});
        
        // UI Functions
        function showNotification(message, type = 'info') {{
            const colors = {{
                'info': 'bg-blue-500',
                'success': 'bg-green-500',
                'warning': 'bg-yellow-500',
                'error': 'bg-red-500'
            }};
            
            const notification = document.createElement('div');
            notification.className = `${{colors[type]}} text-white px-4 py-2 rounded shadow-lg transform transition-all duration-300 translate-x-full`;
            notification.textContent = message;
            
            document.getElementById('notifications').appendChild(notification);
            
            // Animate in
            setTimeout(() => {{
                notification.classList.remove('translate-x-full');
            }}, 10);
            
            // Remove after 3 seconds
            setTimeout(() => {{
                notification.classList.add('translate-x-full');
                setTimeout(() => notification.remove(), 300);
            }}, 3000);
        }}
        
        function addNoteToList(note) {{
            const notesList = document.getElementById('notesList');
            
            // Check if note already exists
            if (document.querySelector(`[data-note-id="${{note.id}}"]`)) {{
                updateNoteInList(note);
                return;
            }}
            
            const noteHtml = createNoteElement(note);
            notesList.insertAdjacentHTML('afterbegin', noteHtml);
        }}
        
        function updateNoteInList(note) {{
            const noteEl = document.querySelector(`[data-note-id="${{note.id}}"]`);
            if (noteEl) {{
                noteEl.classList.add('note-updating');
                const newNoteHtml = createNoteElement(note);
                const temp = document.createElement('div');
                temp.innerHTML = newNoteHtml;
                noteEl.replaceWith(temp.firstElementChild);
            }} else {{
                addNoteToList(note);
            }}
        }}
        
        function removeNoteFromList(noteId) {{
            const noteEl = document.querySelector(`[data-note-id="${{noteId}}"]`);
            if (noteEl) {{
                noteEl.style.opacity = '0';
                noteEl.style.transform = 'scale(0.9)';
                setTimeout(() => noteEl.remove(), 300);
            }}
        }}
        
        function createNoteElement(note) {{
            const noteJson = JSON.stringify(note).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
            return `
                <div data-note-id="${{note.id}}" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition-all duration-300">
                    <h2 class="text-xl font-semibold mb-2">${{escapeHtml(note.title)}}</h2>
                    <p class="text-gray-600 mb-3">${{escapeHtml(note.summary)}}</p>
                    <div class="flex flex-wrap gap-1 mb-3">
                        ${{(note.tags || []).map(tag => `<span class="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded">${{escapeHtml(tag)}}</span>`).join('')}}
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-xs text-gray-400">${{new Date(note.updated_at).toLocaleString()}}</span>
                        <div class="space-x-2">
                            <button onclick='openEditModal(${{noteJson}})' class="px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600">Edit</button>
                            <button onclick="confirmDelete('${{note.id}}')" class="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        // Modal handling
        const createBtn = document.getElementById('createBtn');
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const cancelBtn = document.getElementById('cancelBtn');

        createBtn.addEventListener('click', () => {{
            modalTitle.textContent = 'Create Note';
            document.getElementById('id').value = '';
            document.getElementById('title').value = '';
            document.getElementById('summary').value = '';
            document.getElementById('tags').value = '';
            document.getElementById('content').value = '';
            modal.showModal();
        }});

        cancelBtn.addEventListener('click', () => {{
            modal.close();
        }});

        function openEditModal(note) {{
            modalTitle.textContent = 'Edit Note';
            document.getElementById('id').value = note.id;
            document.getElementById('title').value = note.title;
            document.getElementById('summary').value = note.summary;
            document.getElementById('tags').value = (note.tags || []).join(', ');
            document.getElementById('content').value = note.content;
            modal.showModal();
        }}

        function confirmDelete(id) {{
            if (confirm('Are you sure you want to delete this note?')) {{
                fetch('/notes/' + id, {{ method: 'DELETE' }})
                    .then(() => {{
                        removeNoteFromList(id);
                        showNotification('Note deleted', 'success');
                    }});
            }}
        }}
      </script>
    </body>
    </html>
    """
        
        notes_html = ""
        for note in reversed(notes):  # Show newest first
            tags_html = "".join([
                f'<span class="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded">{escape_html(tag)}</span>'
                for tag in note.get("tags", [])
            ])
            
            note_json = escape_html(json.dumps(note))
            notes_html += f"""
      <div data-note-id="{escape_html(note['id'])}" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition-all duration-300">
        <h2 class="text-xl font-semibold mb-2">{escape_html(note['title'])}</h2>
        <p class="text-gray-600 mb-3">{escape_html(note['summary'])}</p>
        <div class="flex flex-wrap gap-1 mb-3">
          {tags_html}
        </div>
        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-400">{datetime.fromisoformat(note.get('updated_at', datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M')}</span>
          <div class="space-x-2">
            <button onclick='openEditModal({note_json})' class="px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600">Edit</button>
            <button onclick="confirmDelete('{escape_html(note['id'])}')" class="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">Delete</button>
          </div>
        </div>
      </div>
    """
        
        return HTMLResponse(header + notes_html + footer)
        
    except Exception as e:
        logger.error(f"Error rendering home page: {e}")
        return HTMLResponse("Internal Server Error", status_code=500)

async def create_or_update_note_handler(request: Request) -> HTMLResponse:
    """Handle note creation/update with event emission"""
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
    """Handle note deletion with event emission"""
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
# API Endpoints for Real-time Features
# ============================================================================

async def get_notes_api(request: Request) -> JSONResponse:
    """API endpoint to get all notes"""
    notes = await get_all_notes()
    return JSONResponse({"notes": notes})

async def get_note_api(request: Request) -> JSONResponse:
    """API endpoint to get a specific note"""
    note_id = request.path_params.get("id")
    if note_id in notes_db:
        return JSONResponse(notes_db[note_id])
    return JSONResponse({"error": "Note not found"}, status_code=404)

# ============================================================================
# Routes
# ============================================================================

routes = [
    # Web UI
    Route("/", render_home_page, methods=["GET"]),
    Route("/notes", create_or_update_note_handler, methods=["POST"]),
    Route("/notes/{id}", delete_note_handler, methods=["DELETE"]),
    
    # API
    Route("/api/notes", get_notes_api, methods=["GET"]),
    Route("/api/notes/{id}", get_note_api, methods=["GET"]),
    
    # SSE endpoint for real-time events
    Route("/events", sse_endpoint, methods=["GET"]),
]

# ============================================================================
# Application
# ============================================================================

# Create web app with CORS middleware
middleware = [
    Middleware(CORSMiddleware, 
               allow_origins=["*"], 
               allow_methods=["*"],
               allow_headers=["*"],
               expose_headers=["*"])
]

web_app = Starlette(routes=routes, middleware=middleware)

# ============================================================================
# Standalone Server
# ============================================================================

if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.environ.get("WEB_PORT", 3100))
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    
    logger.info(f"Starting Notes Web Server v2 on {host}:{port}")
    logger.info("Real-time collaboration enabled via SSE")
    logger.info("Access the web interface at http://localhost:3100/")
    
    try:
        # Start event manager
        asyncio.run(event_manager.start())
        
        # Run web server
        uvicorn.run(web_app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
    except Exception as e:
        logger.error(f"Web server error: {e}")
    finally:
        # Stop event manager
        asyncio.run(event_manager.stop())
