# Project Structure

## Overview

The Remote MCP Prototype is organized in a clean, modular structure optimized for both local development and containerized deployment.

```
remote-mcp-prototype/
├── src/                        # Source code
│   └── remote_mcp/            # Main package
│       ├── __init__.py        # Package initialization
│       ├── server.py          # MCP server implementation
│       └── web_app.py         # Web interface for notes
│
├── deploy/                    # Deployment configurations
│   └── caprover/             # CapRover specific files
│       └── Dockerfile        # Container definition
│
├── scripts/                   # Utility scripts
│   ├── linux/                # Linux/Mac scripts
│   │   ├── cleanup.sh       # Clean build artifacts
│   │   ├── rebuild.sh       # Full rebuild
│   │   └── setup_dirs.sh    # Initialize directories
│   │
│   └── windows/              # Windows scripts
│       ├── build.bat/.ps1   # Build scripts
│       ├── install.bat/.ps1 # Install dependencies
│       ├── rebuild.bat/.ps1 # Clean rebuild
│       ├── run.bat          # Quick run
│       └── setup.bat/.ps1   # Initial setup
│
├── tests/                     # Test suite
│   └── test_local.py         # Local server tests
│
├── docs/                      # Documentation
│   └── API.md                # API reference
│
├── run_server.py             # MCP server entry point
├── run_web_server.py         # Web server entry point
├── run_both.py               # Run both servers
├── run_web.bat               # Windows: web server
├── run_both.bat              # Windows: both servers
├── test_notes.py             # Test script for notes
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── PROJECT_STRUCTURE.md      # This file
├── .gitignore               # Git exclusions
└── .dockerignore            # Docker exclusions
```

## Key Components

### Core Server (`src/remote_mcp/`)

**server.py**
- MCP server implementation using FastMCP
- Tool definitions (calculator, text analyzer, task manager, notes management)
- HTTP transport configuration
- Critical lifespan management

**web_app.py**
- Web interface for notes management
- Same UI/UX as MCPNotes
- Create, edit, delete functionality
- Shares notes database with MCP server

**Key Features:**
- Streamable HTTP transport
- Multiple tool implementations
- Proper error handling
- Health check endpoints
- Web UI on port 3100
- Synchronized data between MCP and Web

### Entry Point (`run_server.py`)

Simple entry point that:
- Configures host and port
- Initializes the Starlette app
- Starts the Uvicorn server
- Handles graceful shutdown

### Deployment (`deploy/`)

**caprover/Dockerfile**
- Multi-stage build for optimization
- Python 3.11 slim base image
- Non-root user for security
- Health check configuration
- Exposes port 8000

### Scripts (`scripts/`)

Platform-specific helper scripts for:
- **Setup**: Initialize environment
- **Install**: Install dependencies
- **Build**: Build the project
- **Run**: Quick server start
- **Rebuild**: Clean and rebuild
- **Cleanup**: Remove artifacts

### Tests (`tests/`)

**test_local.py**
- Unit tests for all tools
- Integration tests for MCP protocol
- HTTP endpoint tests
- Error handling validation

## Configuration Files

### requirements.txt
```
mcp>=0.1.0
starlette>=0.31.0
uvicorn[standard]>=0.24.0
```

### .gitignore
- Python artifacts (`__pycache__`, `*.pyc`)
- Virtual environments (`venv/`, `.env`)
- IDE files (`.vscode/`, `.idea/`)
- Build artifacts (`dist/`, `build/`)

### .dockerignore
- Git files (`.git/`, `.gitignore`)
- Documentation (`*.md`)
- Development files (`tests/`, `scripts/`)
- Python artifacts

## Data Flow

```
1. Request arrives at HTTP endpoint
   ↓
2. Starlette routes to MCP handler
   ↓
3. MCP processes tool invocation
   ↓
4. Tool executes and returns result
   ↓
5. Response sent via HTTP transport
```

## Tool Architecture

Each tool follows this pattern:

```python
@mcp.tool()
async def tool_name(param1: Type1, param2: Type2) -> ReturnType:
    """Tool description for discovery"""
    # Validation
    # Processing
    # Return structured result
```

## Deployment Architecture

```
GitHub Repository
    ↓ (webhook)
CapRover
    ↓ (build)
Docker Container
    ↓ (deploy)
Production Server
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | MCP server bind address | `0.0.0.0` |
| `PORT` | MCP server port | `8000` |
| `WEB_HOST` | Web server bind address | `0.0.0.0` |
| `WEB_PORT` | Web server port | `3100` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

## API Endpoints

### MCP Server (Port 8000)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Health check |
| `/mcp` | POST, GET | MCP protocol endpoint |
| `/mcp/` | POST, GET | MCP protocol endpoint (with trailing slash) |

### Web Server (Port 3100)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface home page |
| `/notes` | POST | Create or update note |
| `/notes/{id}` | DELETE | Delete note by ID |

## Security Considerations

1. **Container Security**
   - Non-root user execution
   - Minimal base image
   - No unnecessary packages

2. **Network Security**
   - HTTPS in production (via CapRover)
   - Input validation on all tools
   - Error message sanitization

3. **Code Security**
   - Type hints for validation
   - Async/await for non-blocking operations
   - Proper exception handling

## Development Workflow

1. **Local Development**
   ```bash
   python run_server.py
   ```

2. **Testing**
   ```bash
   npx @modelcontextprotocol/inspector --url http://localhost:8000/mcp
   ```

3. **Commit & Push**
   ```bash
   git add .
   git commit -m "Feature: description"
   git push origin master
   ```

4. **Automatic Deployment**
   - GitHub webhook triggers CapRover
   - CapRover builds Docker image
   - New container deployed with zero downtime

## Extending the Project

### Adding New Tools

1. Define tool in `src/remote_mcp/server.py`
2. Add tests in `tests/test_local.py`
3. Update API documentation in `docs/API.md`
4. Test with MCP Inspector

### Adding New Endpoints

1. Add route in server configuration
2. Implement handler function
3. Update documentation
4. Add tests

### Customizing Deployment

1. Modify `deploy/caprover/Dockerfile`
2. Update environment variables
3. Configure CapRover settings
4. Test deployment pipeline

## Performance Considerations

- **Async Operations**: All tools use async/await
- **Connection Pooling**: Reuse HTTP connections
- **Minimal Dependencies**: Only essential packages
- **Optimized Docker Image**: Multi-stage build, slim base

## Monitoring

- Health checks via `/health` endpoint
- CapRover built-in monitoring
- Application logs via `uvicorn`
- Error tracking in production

## Maintenance

- Regular dependency updates
- Security patches
- Performance monitoring
- Log rotation
- Backup strategies

---

*Last Updated: 2025-09-02*
