# Template Usage Guide

This guide will help you transform this template into your own MCP server.

## 🎯 Getting Started

### 1. Create Your Repository

1. Click "Use this template" button on GitHub
2. Name your repository (e.g., `my-awesome-mcp-server`)
3. Choose public or private visibility
4. Click "Create repository from template"

### 2. Clone and Setup

```bash
# Clone your new repository
git clone https://github.com/YOUR_USERNAME/your-repo-name.git
cd your-repo-name

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 3. Customize Your Server

#### Update Metadata

1. Edit `pyproject.toml`:
   - Change `name` to your server name
   - Update `authors` with your information
   - Modify `description`
   - Update all URLs to point to your repository

2. Update `README.md`:
   - Replace all instances of `YOUR_USERNAME`
   - Update the project name and description
   - Modify badges to point to your repository

3. Edit `src/remote_mcp/server.py`:
   - Change the server name in `FastMCP("Your Server Name")`
   - Update the description

#### Remove Example Tools

The template includes example tools. You can:
- Keep them as reference
- Modify them for your needs
- Delete them and add your own

To remove example tools:
1. Delete the tool functions from `server.py`
2. Remove related imports
3. Update tests accordingly

### 4. Add Your Custom Tools

#### Basic Tool Structure

```python
@mcp.tool()
async def your_tool_name(
    required_param: str,
    optional_param: int = 10
) -> Dict[str, Any]:
    """
    Brief description of your tool.
    
    Args:
        required_param: Description of this parameter
        optional_param: Description with default value
    
    Returns:
        Dictionary with results
    """
    try:
        # Your tool logic here
        result = process_something(required_param, optional_param)
        
        return {
            "success": True,
            "data": result,
            "message": "Operation completed successfully"
        }
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

#### Tool Best Practices

1. **Always use type hints** - Makes your API clear
2. **Return consistent structure** - Use success/error pattern
3. **Handle errors gracefully** - Never let exceptions crash the server
4. **Add comprehensive docstrings** - Help users understand your tools
5. **Log important events** - Use the logger for debugging
6. **Validate inputs** - Check parameters before processing

### 5. Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```env
# Your configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Add your API keys
YOUR_API_KEY=your_actual_key_here
```

3. Update `.env.example` with any new variables (without sensitive values)

### 6. Write Tests

Create tests for your tools in `tests/`:

```python
# tests/test_your_tools.py
import pytest
from src.remote_mcp.server import your_tool_name

@pytest.mark.asyncio
async def test_your_tool():
    result = await your_tool_name("test_input")
    assert result["success"] == True
    assert "data" in result
```

Run tests:
```bash
pytest tests/ -v
```

### 7. Update Documentation

1. **Update API.md** with your tool documentation
2. **Modify examples/** to show your tool usage
3. **Update README.md** with:
   - Your tool descriptions
   - Installation instructions
   - Configuration requirements
   - Usage examples

### 8. Set Up CI/CD

The template includes GitHub Actions workflows. Update them:

1. Check `.github/workflows/ci.yml` - adjust Python versions if needed
2. Review `.github/workflows/docker.yml` - update registry settings
3. Add secrets to your GitHub repository:
   - Go to Settings → Secrets and variables → Actions
   - Add any required secrets (API keys, tokens)

### 9. Deploy Your Server

#### Local Testing
```bash
python run_server.py
```

#### Docker Deployment
```bash
# Build
docker build -f deploy/caprover/Dockerfile -t your-server .

# Run
docker run -p 8000:8000 your-server
```

#### CapRover Deployment
1. Set up CapRover app
2. Configure GitHub webhook
3. Push to trigger deployment

## 📋 Checklist

Before going to production, ensure you've:

- [ ] Updated all metadata (name, description, author)
- [ ] Replaced placeholder usernames and URLs
- [ ] Removed or modified example tools
- [ ] Added your custom tools
- [ ] Written tests for your tools
- [ ] Updated documentation
- [ ] Configured environment variables
- [ ] Set up proper error handling
- [ ] Added input validation
- [ ] Implemented logging
- [ ] Tested locally with MCP Inspector
- [ ] Run the test suite
- [ ] Updated CI/CD configuration
- [ ] Added necessary secrets to GitHub
- [ ] Tested Docker build
- [ ] Reviewed security settings

## 🎨 Customization Ideas

### Add Database Support
See `examples/database_tool.py` for SQLite integration

### Integrate External APIs
Check `examples/external_api_tool.py` for patterns

### Implement Authentication
Review `examples/auth_security_tool.py` for security

### Add Caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_operation(param: str):
    # Expensive operation
    return result
```

### Enable CORS for Web Access
```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🆘 Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Port already in use**: Change PORT in .env
3. **Docker build fails**: Check Dockerfile path
4. **MCP Inspector can't connect**: Verify server is running and URL is correct
5. **Tools not showing**: Check @mcp.tool() decorator is applied

### Getting Help

- Check the [MCP Documentation](https://modelcontextprotocol.io/)
- Review [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- Open an issue in your repository
- Ask in MCP community forums

## 🚀 Next Steps

1. **Add more tools** - Expand your server's capabilities
2. **Implement persistence** - Add database for stateful operations
3. **Add authentication** - Secure your server
4. **Set up monitoring** - Track usage and errors
5. **Create client libraries** - Make it easy for others to use your server
6. **Write comprehensive docs** - Help users get the most from your tools

---

Happy building! 🎉
