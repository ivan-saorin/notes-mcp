# Notes Web Interface

The Python Remote MCP Server now includes a full web interface for notes management, ported from the MCPNotes project.

## Features

- **Create Notes**: Add new notes with title, summary, content, and tags
- **Edit Notes**: Update existing notes through a modal dialog
- **Delete Notes**: Remove notes with confirmation
- **Tag Support**: Organize notes with comma-separated tags
- **Responsive Design**: Built with Tailwind CSS for a modern UI
- **Shared Database**: Notes are synchronized between MCP server and Web UI

## Running the Web Interface

### Option 1: Run Both Servers (Recommended)
```bash
python run_both.py
# Or on Windows:
run_both.bat
```

This starts:
- MCP Server on http://localhost:8000/mcp
- Web UI on http://localhost:3100/

### Option 2: Run Web Server Only
```bash
python run_web_server.py
# Or on Windows:
run_web.bat
```

### Option 3: Run Servers Separately
```bash
# Terminal 1
python run_server.py

# Terminal 2
python run_web_server.py
```

## Usage

1. Open http://localhost:3100/ in your browser
2. Click "Create Note" to add a new note
3. Click "Edit" on any note to modify it
4. Click "Delete" to remove a note (with confirmation)

## Architecture

The web interface shares the same notes database with the MCP server, meaning:
- Notes created via MCP tools are visible in the web UI
- Notes created in the web UI are accessible via MCP tools
- All changes are synchronized in real-time

## Customization

### Change Port
Set the `WEB_PORT` environment variable:
```bash
WEB_PORT=3200 python run_web_server.py
```

### Styling
The UI uses Tailwind CSS via CDN. To customize styling, modify the HTML template in `src/remote_mcp/web_app.py`.

## API Endpoints

- `GET /` - Home page with notes list
- `POST /notes` - Create or update a note
- `DELETE /notes/{id}` - Delete a note

## Notes Structure

Each note contains:
- `id`: Unique identifier
- `title`: Note title
- `summary`: Brief summary
- `content`: Full content (supports multiline text)
- `tags`: Array of tags for categorization
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Comparison with MCPNotes

This implementation maintains feature parity with the original MCPNotes web interface:
- Same UI layout and styling
- Same modal-based editing
- Same form fields and validation
- Same delete confirmation flow

The main difference is the backend:
- Original: TypeScript/Express + DynamoDB
- This port: Python/Starlette + In-memory storage

For persistent storage, you can easily modify the implementation to use SQLite, PostgreSQL, or any other database.
