# Contributing to Python Remote MCP Template

First off, thank you for considering contributing to this project! 

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible using our issue template.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please use the feature request template and include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Examples of how it would be used
- Any potential drawbacks or considerations

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Make sure your code follows the existing style
5. Issue that pull request!

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/your-username/python-remote-mcp-template.git
   cd python-remote-mcp-template
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Run tests:
   ```bash
   pytest tests/
   ```

## Style Guide

### Python Style

- Follow PEP 8
- Use black for formatting: `black src/`
- Use isort for imports: `isort src/`
- Use type hints where appropriate
- Document all public functions with docstrings

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add calculator tool with advanced operations

- Implement power and modulo operations
- Add comprehensive error handling
- Include unit tests for all operations

Fixes #123
```

## Testing

- Write tests for all new functionality
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Use pytest for testing

## Documentation

- Update README.md if you change functionality
- Add docstrings to all public functions
- Update API.md for any tool changes
- Include examples in docstrings

## Project Structure

When adding new tools, follow this pattern:

```python
@mcp.tool()
async def your_tool_name(
    param1: str,
    param2: int = 10
) -> Dict[str, Any]:
    """
    Brief description of what the tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
    
    Returns:
        Dictionary containing the result with keys:
        - success: Whether operation succeeded
        - data: The actual result data
        - message: Human-readable message
    
    Example:
        >>> await your_tool_name("test", 20)
        {"success": True, "data": {...}, "message": "Operation completed"}
    """
    # Implementation
    pass
```

## Questions?

Feel free to open an issue with the question tag or start a discussion in the GitHub Discussions tab.

Thank you for contributing! 🎉
