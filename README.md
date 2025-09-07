# 🚀 Python Remote MCP Server Template

[![CI](https://github.com/ivan-saorin/notes-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ivan-saorin/notes-mcp/actions/workflows/ci.yml)
[![Docker Build](https://github.com/ivan-saorin/notes-mcp/actions/workflows/docker.yml/badge.svg)](https://github.com/ivan-saorin/notes-mcp/actions/workflows/docker.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A production-ready template for building and deploying Model Context Protocol (MCP) servers remotely via HTTP transport. Get your MCP tools accessible from anywhere in minutes!

## ✨ Features

- **🎯 Ready-to-Deploy**: Pre-configured for local development, Docker, and CapRover deployment
- **🔧 Sample Tools**: Calculator, text analyzer, task manager, and notes management examples included
- **🐳 Docker Support**: Multi-stage Dockerfile for optimized container builds
- **⚡ FastMCP Integration**: Built on FastMCP for high-performance async operations
- **🔒 Security Examples**: Authentication, rate limiting, and input sanitization templates
- **📊 Database Examples**: SQLite integration with async support
- **🌐 API Integration**: External API call examples with proper error handling
- **🧪 Testing Suite**: Comprehensive test setup with pytest and coverage
- **📝 Full Documentation**: Detailed guides for every deployment scenario
- **🔄 CI/CD Ready**: GitHub Actions workflows for testing and deployment

## 🚀 Quick Start

### Use this Template

1. Click the "Use this template" button at the top of this repository
2. Create a new repository from this template
3. Clone your new repository:
```bash
git clone https://github.com/YOUR_USERNAME/your-mcp-server.git
cd your-mcp-server
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run MCP server only
python run_server.py

# Run Web UI only (for notes management)
python run_web_server.py

# Run both servers
python run_both.py
# Or on Windows: run_both.bat

# Test with MCP Inspector
npx @modelcontextprotocol/inspector --url http://localhost:8000/mcp
```

### Web Interface

The Notes Management features include a web interface (similar to MCPNotes) available at:
- **Web UI**: http://localhost:3100/
- **Features**: Create, edit, view, and delete notes through a browser
- **Port Configuration**: Set `WEB_PORT` environment variable (default: 3100)

## 📁 Project Structure

```
.
├── src/remote_mcp/        # Main server implementation
│   ├── __init__.py
│   └── server.py          # MCP server with FastMCP
├── examples/              # Example tool implementations
│   ├── database_tool.py   # Database integration example
│   ├── external_api_tool.py # API integration example
│   └── auth_security_tool.py # Security implementation
├── deploy/                # Deployment configurations
│   └── caprover/
│       └── Dockerfile     # Production Docker image
├── tests/                 # Test suite
├── scripts/               # Helper scripts
│   ├── linux/            # Linux/Mac scripts
│   └── windows/          # Windows scripts
├── docs/                  # Documentation
├── .github/              # GitHub Actions workflows
└── requirements.txt      # Python dependencies
```

## 🛠️ Customization Guide

### Adding Your Own Tools

1. Open `src/remote_mcp/server.py`
2. Add your tool using the `@mcp.tool()` decorator:

```python
@mcp.tool()
async def your_custom_tool(
    param1: str,
    param2: int = 10
) -> Dict[str, Any]:
    """Your tool description"""
    # Your implementation
    return {"result": "success"}
```

3. Test with MCP Inspector
4. Deploy your changes

### Configuration

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Configure your environment variables:
- Server settings (HOST, PORT)
- API keys for external services
- Database connections
- Authentication tokens

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build the image
docker build -f deploy/caprover/Dockerfile -t mcp-server .

# Run the container
docker run -p 8000:8000 mcp-server

# With environment variables
docker run -p 8000:8000 --env-file .env mcp-server
```

### Push to Registry

```bash
# Tag for your registry
docker tag mcp-server your-registry/mcp-server:latest

# Push to registry
docker push your-registry/mcp-server:latest
```

## ⚓ CapRover Deployment

### Prerequisites
- CapRover instance running
- GitHub account for webhooks
- Domain configured (optional)

### Step-by-Step Guide

1. **Create GitHub Personal Access Token**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate token with `repo` and `admin:repo_hook` scopes

2. **Configure CapRover App**
   - Create new app in CapRover
   - Enable GitHub deployment
   - Add webhook URL to your repository

3. **Deploy**
   - Push to your repository
   - CapRover automatically builds and deploys

See [full CapRover guide](docs/CAPROVER_DEPLOYMENT.md) for detailed instructions.

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=src/remote_mcp --cov-report=html

# Run linting
black src/
isort src/
flake8 src/
```

## 📚 Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Deployment Guide](docs/DEPLOYMENT.md) - All deployment options
- [Security Guide](docs/SECURITY.md) - Security best practices
- [Examples](examples/) - Sample tool implementations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-tool`)
3. Commit your changes (`git commit -m 'Add amazing tool'`)
4. Push to the branch (`git push origin feature/amazing-tool`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Special Thanks to MCPNotes

**A huge thank you to the creator of [MCPNotes](https://github.com/Tomatio13/MCPNotes)** for the excellent notes management implementation that inspired the notes features in this template! 🌟

The notes management functionality (both MCP tools and web interface) in this template is a Python port of the original MCPNotes project. We've maintained the same user experience and functionality while adapting it to Python and the FastMCP framework.

If you find the notes features useful, please also check out and star the original [MCPNotes repository](https://github.com/Tomatio13/MCPNotes)!

### Other Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) for high-performance MCP implementation
- Deployed with [CapRover](https://caprover.com/) for easy container management
- Tested with [MCP Inspector](https://github.com/modelcontextprotocol/inspector) & [Claude Desktop](https://claude.ai/download) & [Claude Desktop](https://claude.ai/download)
- Based on the [Model Context Protocol](https://modelcontextprotocol.io/) specification

## 💬 Support

- 📖 [Documentation](https://github.com/ivan-saorin/notes-mcp/wiki)
- 💬 [Discussions](https://github.com/ivan-saorin/notes-mcp/discussions)
- 🐛 [Issue Tracker](https://github.com/ivan-saorin/notes-mcp/issues)

## 🚦 Status

- ✅ Production Ready
- ✅ Docker Support
- ✅ CapRover Integration
- ✅ CI/CD Pipeline
- ✅ Security Examples
- ✅ Database Integration
- ✅ External API Examples
- 🚧 Kubernetes Helm Chart (Coming Soon)
- 🚧 AWS Lambda Deployment (Coming Soon)

---

**Made with ❤️ for the MCP community**

*If this template helps you, please consider giving it a ⭐!*
