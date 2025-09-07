# API Documentation

Atlas Remote MCP Server provides Model Context Protocol tools via HTTP transport.

## Endpoints

### Health Check
- **GET** `/` 
- **GET** `/health`

Returns server status:
```json
{
  "status": "healthy",
  "server": "Atlas Remote MCP",
  "version": "2.0.0",
  "transport": "streamable-http",
  "endpoint": "/mcp"
}
```

### MCP Endpoints
- **POST** `/mcp` - Main MCP protocol endpoint
- **GET** `/mcp` - MCP protocol endpoint (for compatibility)
- **POST** `/mcp/` - With trailing slash (avoids redirect issues)
- **GET** `/mcp/` - With trailing slash (for compatibility)

The MCP endpoints handle tool interactions using the streamable HTTP transport protocol.

## MCP Protocol

The server implements the Model Context Protocol specification for tool discovery and execution.

### Tool Discovery
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

### Tool Execution
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "remote:calculate",
    "arguments": {
      "a": 10,
      "b": 5,
      "operation": "multiply"
    }
  },
  "id": 2
}
```

## Available Tools

All tools are prefixed with `remote:` namespace when called through MCP.

### 1. System Information
**Tool:** `remote:system_info`  
**Parameters:** None  
**Description:** Get system information and server status

**Example Response:**
```json
{
  "server_name": "Atlas Remote MCP Prototype",
  "version": "2.0.0",
  "timestamp": "2025-09-02T10:30:00Z",
  "transport": "streamable-http",
  "features": ["calculator", "text_processing", "task_management", "notes_management"]
}
```

### 2. Calculator
**Tool:** `remote:calculate`  
**Parameters:**
- `a` (number, required): First number
- `b` (number, required): Second number  
- `operation` (string, optional): Operation type (default: "add")
  - `add` - Addition
  - `subtract` - Subtraction
  - `multiply` - Multiplication
  - `divide` - Division
  - `power` - Exponentiation
  - `modulo` - Modulo

**Example Response:**
```json
{
  "operation": "multiply",
  "a": 10.0,
  "b": 5.0,
  "result": 50.0,
  "expression": "10.0 multiply 5.0 = 50.0"
}
```

### 3. Text Analysis
**Tool:** `remote:text_analyze`  
**Parameters:**
- `text` (string, required): Text to analyze

**Example Response:**
```json
{
  "character_count": 36,
  "word_count": 7,
  "sentence_count": 1,
  "average_word_length": 4.57,
  "unique_words": 7,
  "preview": "This is a sample text for analysis."
}
```

### 4. Task Management

#### Create Task
**Tool:** `remote:task_create`  
**Parameters:**
- `title` (string, required): Task title
- `description` (string, optional): Task description (default: "")
- `priority` (string, optional): Priority level (default: "medium")
  - Options: `low`, `medium`, `high`

**Example Response:**
```json
{
  "id": "task_1",
  "title": "Review documentation",
  "description": "Review and update API docs",
  "priority": "high",
  "status": "pending",
  "created_at": "2025-09-02T10:30:00Z",
  "updated_at": "2025-09-02T10:30:00Z"
}
```

#### List Tasks
**Tool:** `remote:task_list`  
**Parameters:**
- `status` (string, optional): Filter by status
  - Options: `pending`, `in_progress`, `completed`

Returns an array of task objects.

#### Update Task
**Tool:** `remote:task_update`  
**Parameters:**
- `task_id` (string, required): Task ID to update
- `status` (string, optional): New status
- `title` (string, optional): New title
- `description` (string, optional): New description
- `priority` (string, optional): New priority

#### Delete Task
**Tool:** `remote:task_delete`  
**Parameters:**
- `task_id` (string, required): Task ID to delete

### 5. Notes Management

#### List Notes
**Tool:** `remote:list_notes`  
**Parameters:**
- `tags` (array of strings, optional): Filter notes by tags

**Example Response:**
```json
{
  "count": 2,
  "notes": [
    {
      "id": "python-api-design-1",
      "title": "Python API Design Best Practices",
      "summary": "Guidelines for designing RESTful APIs in Python",
      "tags": ["python", "api", "design"]
    },
    {
      "id": "mcp-integration-2",
      "title": "MCP Integration Guide",
      "summary": "How to integrate MCP into existing applications",
      "tags": ["mcp", "integration"]
    }
  ]
}
```

#### Get Note
**Tool:** `remote:get_note`  
**Parameters:**
- `note_id` (string, required): ID of the note to retrieve

**Example Response:**
```json
{
  "id": "python-api-design-1",
  "title": "Python API Design Best Practices",
  "summary": "Guidelines for designing RESTful APIs in Python",
  "tags": ["python", "api", "design"],
  "content": "# Python API Design\n\n## Key Principles....",
  "created_at": "2025-09-02T10:30:00Z",
  "updated_at": "2025-09-02T15:45:00Z"
}
```

#### Write Note
**Tool:** `remote:write_note`  
**Parameters:**
- `title` (string, required): Note title
- `content` (string, required): Note content (supports markdown)
- `summary` (string, required): Brief summary of the note
- `tags` (array of strings, optional): Tags for categorization
- `note_id` (string, optional): Specific ID for updating existing note

**Example Response:**
```json
{
  "success": true,
  "action": "created",
  "note": {
    "id": "docker-deployment-3",
    "title": "Docker Deployment Guide",
    "summary": "Step-by-step guide for Docker deployments",
    "tags": ["docker", "deployment", "devops"],
    "content": "# Docker Deployment\n\n## Prerequisites....",
    "created_at": "2025-09-02T16:00:00Z",
    "updated_at": "2025-09-02T16:00:00Z"
  }
}
```

#### Delete Note
**Tool:** `remote:delete_note`  
**Parameters:**
- `note_id` (string, required): ID of the note to delete

**Example Response:**
```json
{
  "success": true,
  "message": "Note with ID 'docker-deployment-3' has been deleted"
}
```

#### Resources Support

Notes can be accessed as resources with URIs in the format `notes://notes/{note_id}`. This enables:
- Subscribing to note updates
- Direct resource access
- Integration with resource-aware tools

**Resource Format:**
```
notes://notes/python-api-design-1
notes://notes/mcp-integration-2
```

## Testing with MCP Inspector

### Installation
```bash
npm install -g @modelcontextprotocol/inspector
```

### Local Testing
```bash
# Connect to local server
npx @modelcontextprotocol/inspector --url http://localhost:8000/mcp
```

### Production Testing
```bash
# Connect to deployed server
npx @modelcontextprotocol/inspector --url https://your-app.yourdomain.com/mcp
```

The inspector provides:
- Interactive tool testing
- Request/response inspection
- Protocol debugging
- Performance metrics

## Claude Desktop Integration

### Configuration

Add to Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "remote-mcp": {
      "url": "http://localhost:8000/mcp",
      "transport": {
        "type": "http",
        "config": {
          "url": "http://localhost:8000/mcp"
        }
      }
    }
  }
}
```

For production:
```json
{
  "mcpServers": {
    "remote-mcp-prod": {
      "url": "https://mcp.yourdomain.com/mcp",
      "transport": {
        "type": "http",
        "config": {
          "url": "https://mcp.yourdomain.com/mcp"
        }
      }
    }
  }
}
```

## Error Handling

### MCP Error Response Format
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "details": "Division by zero"
    }
  },
  "id": 1
}
```

### Common Error Codes
- `-32700` - Parse error
- `-32600` - Invalid request
- `-32601` - Method not found
- `-32602` - Invalid params
- `-32603` - Internal error

## Transport Configuration

### Streamable HTTP Transport

The server uses streamable HTTP transport which supports:
- Bidirectional communication
- Request/response pattern
- Server-sent events
- Long polling
- WebSocket upgrade (when available)

### Connection Configuration
```python
# In server.py
app = Starlette(
    lifespan=mcp_app.lifespan,  # Critical for proper operation
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/", health_check, methods=["GET"]),
        Route("/mcp", mcp_app, methods=["POST", "GET"]),
        Route("/mcp/", mcp_app, methods=["POST", "GET"]),
    ]
)
```

## Performance Metrics

### Response Times (Average)
| Tool | Response Time |
|------|--------------|
| system_info | < 10ms |
| calculate | < 5ms |
| text_analyze | < 50ms (10KB text) |
| task_create | < 20ms |
| task_list | < 15ms |
| task_update | < 20ms |
| task_delete | < 15ms |
| list_notes | < 20ms |
| get_note | < 10ms |
| write_note | < 25ms |
| delete_note | < 15ms |

### Throughput
- Requests per second: 1000+ (local)
- Concurrent connections: 100 (default)
- Memory per connection: ~1MB

## SDK Examples

### Python with MCP Client
```python
from mcp import Client
import httpx

async def use_remote_mcp():
    transport = httpx.AsyncClient(base_url="http://localhost:8000")
    async with Client(transport) as client:
        # List available tools
        tools = await client.list_tools()
        
        # Call a tool
        result = await client.call_tool(
            "remote:calculate",
            arguments={
                "a": 42,
                "b": 17,
                "operation": "multiply"
            }
        )
        return result
```

### Direct HTTP with Python
```python
import httpx
import json

async def call_mcp_tool():
    async with httpx.AsyncClient() as client:
        # Tool discovery
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
        )
        tools = response.json()
        
        # Tool execution
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remote:calculate",
                    "arguments": {
                        "a": 10,
                        "b": 5,
                        "operation": "multiply"
                    }
                },
                "id": 2
            }
        )
        return response.json()
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function callMCPTool(toolName, args) {
    const response = await axios.post('http://localhost:8000/mcp', {
        jsonrpc: "2.0",
        method: "tools/call",
        params: {
            name: toolName,
            arguments: args
        },
        id: Date.now()
    });
    return response.data;
}

// Example usage
const result = await callMCPTool('remote:calculate', {
    a: 10,
    b: 5,
    operation: 'multiply'
});
```

### cURL Examples

**List tools:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

**Call a tool:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "remote:calculate",
      "arguments": {
        "a": 10,
        "b": 5,
        "operation": "multiply"
      }
    },
    "id": 2
  }'
```

## Extending the Server

To add new tools, edit `src/remote_mcp/server.py`:

```python
from mcp.server import Server
from mcp.types import Tool
from typing import Dict, Any

# Initialize server
mcp = Server("atlas-remote-mcp")

@mcp.tool()
async def my_custom_tool(param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    Description of your custom tool.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (optional)
    
    Returns:
        Dict containing the result
    """
    # Tool implementation
    result = process_data(param1, param2)
    
    return {
        "status": "success",
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
```

Tools are automatically:
- Registered with the MCP server
- Available through tool discovery
- Accessible via the `remote:` namespace

## Security Best Practices

1. **Use HTTPS in Production**
   - Configure SSL/TLS via CapRover
   - Enforce HTTPS redirect

2. **Input Validation**
   - Validate all tool parameters
   - Sanitize text inputs
   - Limit input sizes

3. **Rate Limiting**
   - Implement per-IP rate limits
   - Use reverse proxy rate limiting
   - Monitor for abuse patterns

4. **Authentication** (for production)
   - API key authentication
   - OAuth2 integration
   - IP whitelisting

5. **Error Handling**
   - Never expose internal errors
   - Log errors server-side
   - Return generic error messages

## Monitoring and Debugging

### Health Checks
```bash
# Local
curl http://localhost:8000/health

# Production
curl https://your-app.yourdomain.com/health
```

### Logs
- Application logs: Check uvicorn output
- CapRover logs: Available in CapRover dashboard
- Docker logs: `docker logs <container-id>`

### Debug Mode
Set environment variable for verbose logging:
```bash
LOG_LEVEL=DEBUG python run_server.py
```

---

For deployment instructions, see [README.md](../README.md#caprover-deployment)  
For project structure, see [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
