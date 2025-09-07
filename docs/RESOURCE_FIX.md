# Fixed: Resource Decorator Error

## Issue
The server was failing to start with the error:
```
ValueError: URI template must contain at least one parameter
```

## Root Cause
FastMCP's `@mcp.resource()` decorator expects a URI template with named parameters (like `{note_id}`), not wildcard patterns like `notes://notes/*`.

## Solution
Changed from:
```python
@mcp.resource(f"notes://notes/*")
async def get_note_resource(uri: str) -> str:
    # Manual URI parsing
```

To:
```python
@mcp.resource("notes://notes/{note_id}")
async def get_note_resource(note_id: str) -> str:
    # Direct parameter access
```

FastMCP automatically handles the URI parsing and passes the `note_id` as a parameter to the function.

## Additional Fixes
1. Moved `import json` to the top of the file with other imports
2. Removed duplicate import from within the function

The server should now start successfully. You can test it with:
```bash
python run_server.py
```
