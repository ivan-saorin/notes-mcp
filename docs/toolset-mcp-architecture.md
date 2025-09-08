# Toolset MCP Architecture Guide

## Overview

The `toolset-mcp` project implements a modular Model Context Protocol (MCP) server using FastMCP and a feature-based architecture. This guide explains the core architectural patterns and how to extend the system with new tools.

## Core Architecture

### Directory Structure

```
toolset-mcp/
├── src/
│   └── remote_mcp/
│       ├── server.py          # Main server entry point
│       ├── shared/            # Shared base classes and types
│       │   ├── base.py       # BaseFeature class and ToolResponse
│       │   └── types.py      # Common enums and type definitions
│       └── features/          # Feature implementations
│           ├── calculator/
│           ├── path_converter/
│           ├── search_manager/
│           ├── task_manager/
│           ├── text_analyzer/
│           └── time/
```

### Key Components

#### 1. BaseFeature Class (`shared/base.py`)

All features inherit from `BaseFeature`, which provides:
- Standard initialization with name and version
- Logging setup
- Input validation helpers
- Error handling
- Abstract method `get_tools()` that must be implemented

```python
class BaseFeature(ABC):
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"feature.{name}")
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of tools provided by this feature"""
        pass
```

#### 2. ToolResponse Class (`shared/base.py`)

Standard response structure for all tool methods:

```python
@dataclass
class ToolResponse:
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        # Returns properly formatted response
```

#### 3. Main Server (`server.py`)

The server:
1. Initializes FastMCP instance
2. Creates feature engine instances
3. Exposes tools using `@mcp.tool()` decorator
4. Handles HTTP transport with health checks
5. Manages filesystem operations with path conversion

## Creating a New Feature

### Step 1: Create Feature Directory

```
src/remote_mcp/features/your_feature/
├── __init__.py
└── engine.py
```

### Step 2: Implement Feature Engine

```python
# features/your_feature/engine.py
from typing import Dict, Any, List
from ...shared.base import BaseFeature, ToolResponse

class YourFeatureEngine(BaseFeature):
    """Engine for your feature functionality"""
    
    def __init__(self):
        super().__init__(name="your_feature", version="1.0.0")
        # Initialize any feature-specific configuration
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of tools provided by this feature"""
        return [
            {
                "name": "your_tool_name",
                "description": "What this tool does",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Parameter description"
                        }
                    },
                    "required": ["param1"]
                }
            }
        ]
    
    def your_tool_method(self, param1: str) -> ToolResponse:
        """Implement your tool logic"""
        try:
            # Validate input
            if not param1:
                return ToolResponse(
                    success=False,
                    error="param1 cannot be empty"
                )
            
            # Process the request
            result = self._process_data(param1)
            
            # Return success response
            return ToolResponse(
                success=True,
                data={"result": result}
            )
            
        except Exception as e:
            return self.handle_error("your_tool_method", e)
```

### Step 3: Export from Feature Package

```python
# features/your_feature/__init__.py
from .engine import YourFeatureEngine

__all__ = ['YourFeatureEngine']
```

### Step 4: Update Main Features Export

```python
# features/__init__.py
from .calculator import CalculatorEngine
# ... other imports ...
from .your_feature import YourFeatureEngine

__all__ = [
    'CalculatorEngine',
    # ... other engines ...
    'YourFeatureEngine'
]
```

### Step 5: Integrate into Server

```python
# server.py

# Import the feature
from .features import (
    CalculatorEngine,
    # ... other engines ...
    YourFeatureEngine
)

# Initialize the engine
your_feature = YourFeatureEngine()

# Expose tools using FastMCP decorator
@mcp.tool()
async def your_tool_name(param1: str) -> Dict[str, Any]:
    """
    Tool description for MCP discovery
    
    Args:
        param1: Parameter description
    """
    response = your_feature.your_tool_method(param1)
    return response.to_dict()
```

## Important FastMCP Considerations

### Never Use Optional[] in FastMCP

**❌ DON'T DO THIS:**
```python
@mcp.tool()
async def my_tool(param1: str, param2: Optional[str]) -> Dict[str, Any]:
    # This will cause issues in FastMCP
```

**✅ DO THIS INSTEAD:**
```python
@mcp.tool()
async def my_tool(param1: str, param2: str = None) -> Dict[str, Any]:
    # Use default values instead of Optional
```

### Parameter Type Conversions

FastMCP may pass parameters as strings even when you expect other types. Always handle conversions:

```python
@mcp.tool()
async def task_create(
    title: str,
    estimated_hours: str = None  # Accept as string
) -> Dict[str, Any]:
    # Convert internally
    if estimated_hours is not None:
        try:
            estimated_hours = float(estimated_hours)
        except (ValueError, TypeError):
            estimated_hours = None
    
    response = task_manager.task_create(title, estimated_hours=estimated_hours)
    return response.to_dict()
```

### List Parameters

For list parameters, accept as string and parse:

```python
@mcp.tool()
async def task_create(
    title: str,
    tags: str = None  # Accept comma-separated string
) -> Dict[str, Any]:
    # Parse tags from string
    if tags is not None and isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    else:
        tags = None
```

## Path Conversion Integration

The server automatically converts Windows paths to Linux format for filesystem operations:

```python
def convert_to_linux_path(path_str: str) -> str:
    """Convert path to Linux format if needed"""
    detected_type = path_converter._detect_path_type(path_str)
    if detected_type == "linux":
        return path_str
    return path_converter._windows_to_linux(path_str)
```

This is transparent to features - they can work with either format.

## Best Practices

### 1. Always Use ToolResponse

Return `ToolResponse` from all feature methods for consistency:

```python
def my_method(self, param: str) -> ToolResponse:
    return ToolResponse(
        success=True,
        data={"result": "value"},
        metadata={"operation": "my_method", "feature": self.name}
    )
```

### 2. Implement Proper Error Handling

Use the inherited `handle_error` method:

```python
try:
    # Your logic
    pass
except Exception as e:
    return self.handle_error("operation_name", e)
```

### 3. Log Important Operations

Use the feature logger:

```python
self.logger.info(f"Processing request with param: {param}")
self.logger.error(f"Failed to process: {error}")
```

### 4. Validate Inputs

Use the `validate_input` helper or implement custom validation:

```python
error = self.validate_input({"param1": param1}, required=["param1"])
if error:
    return ToolResponse(success=False, error=error)
```

### 5. Document Tool Schemas

Provide clear `inputSchema` in `get_tools()`:

```python
"inputSchema": {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum results (1-100)",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        }
    },
    "required": ["query"]
}
```

## Adding to System Info

Update the `system_info` tool to include your feature:

```python
@mcp.tool()
async def system_info() -> Dict[str, Any]:
    return {
        # ... existing info ...
        "features": {
            # ... other features ...
            "your_feature": {
                "version": your_feature.version,
                "capabilities": ["capability1", "capability2"]
            }
        }
    }
```

## Testing Your Feature

1. **Unit Tests**: Test the engine methods directly
2. **Integration Tests**: Test through the MCP interface
3. **Manual Testing**: Use MCP Inspector

```bash
# Test with MCP Inspector
npx @modelcontextprotocol/inspector --url http://localhost:8000/mcp
```

## Example: Search Manager Feature

The search manager demonstrates advanced patterns:

1. **Multiple Provider Support**: Manages different search providers
2. **Async Operations**: Uses `async/await` for parallel searches
3. **Configuration**: Uses environment variables for API keys
4. **Complex Responses**: Returns structured data with metadata

```python
class SearchManagerEngine(BaseFeature):
    def __init__(self):
        super().__init__("search_manager", "1.2.0")
        self._init_providers()
    
    async def web_search(self, query: str, providers: List[str] = None, 
                        max_results: int = 10) -> ToolResponse:
        # Parallel search across providers
        results = await asyncio.gather(
            *[provider.search(query, max_results) 
              for provider in selected_providers],
            return_exceptions=True
        )
        # Process and deduplicate results
        return ToolResponse(success=True, data=processed_results)
```

## Deployment Considerations

1. **Environment Variables**: Features can use env vars for configuration
2. **Resource Limits**: Consider memory/CPU usage for feature operations
3. **Error Recovery**: Implement graceful degradation
4. **Logging**: Use appropriate log levels for production

## Summary

The toolset-mcp architecture provides:
- Clean separation of concerns through features
- Consistent response handling with ToolResponse
- Easy extensibility through BaseFeature
- Proper error handling and logging
- Type safety with proper parameter handling

Remember:
- Never use `Optional[]` in FastMCP parameters
- Always convert string inputs to expected types
- Return ToolResponse from feature methods
- Convert responses to dict in server methods
- Handle path conversions transparently

This modular architecture makes it easy to add new capabilities while maintaining consistency across the entire system.
