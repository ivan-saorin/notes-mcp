# Toolset MCP Quick Reference

## FastMCP Gotchas & Best Practices

### ❌ NEVER Use Optional[] in FastMCP

```python
# WRONG - This will break in FastMCP
from typing import Optional

@mcp.tool()
async def my_tool(required_param: str, optional_param: Optional[str]) -> Dict[str, Any]:
    pass

# CORRECT - Use default values instead
@mcp.tool()
async def my_tool(required_param: str, optional_param: str = None) -> Dict[str, Any]:
    pass
```

### String Parameter Conversions

FastMCP may pass all parameters as strings. Always handle conversions:

```python
@mcp.tool()
async def calculate_something(
    value: str,  # Accept as string even if you need float
    count: str = None  # Accept as string even if you need int
) -> Dict[str, Any]:
    # Convert internally
    try:
        value = float(value)
        if count is not None:
            count = int(count)
    except (ValueError, TypeError):
        return {"error": "Invalid numeric input"}
```

### List Parameters

Accept lists as comma-separated strings:

```python
@mcp.tool()
async def process_items(
    items: str  # Accept as "item1,item2,item3"
) -> Dict[str, Any]:
    # Parse the list
    items_list = [item.strip() for item in items.split(',') if item.strip()]
```

## Quick Feature Template

```python
# features/my_feature/engine.py
from typing import Dict, Any, List
from ...shared.base import BaseFeature, ToolResponse

class MyFeatureEngine(BaseFeature):
    def __init__(self):
        super().__init__("my_feature", "1.0.0")
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "my_tool",
            "description": "Tool description",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "Param desc"}
                },
                "required": ["param"]
            }
        }]
    
    def my_tool_method(self, param: str) -> ToolResponse:
        try:
            # Your logic here
            result = process_something(param)
            return ToolResponse(success=True, data={"result": result})
        except Exception as e:
            return self.handle_error("my_tool_method", e)
```

## Server Integration Steps

1. **Import Feature**:
```python
from .features import MyFeatureEngine
```

2. **Initialize Engine**:
```python
my_feature = MyFeatureEngine()
```

3. **Create Tool**:
```python
@mcp.tool()
async def my_tool(param: str) -> Dict[str, Any]:
    """Tool description"""
    response = my_feature.my_tool_method(param)
    return response.to_dict()  # Always convert to dict!
```

4. **Update system_info**:
```python
"features": {
    "my_feature": {
        "version": my_feature.version,
        "capabilities": ["list", "of", "capabilities"]
    }
}
```

## Path Handling

Paths are automatically converted between Windows and Linux:

```python
# User provides: "M:\projects\myfile.txt"
# Automatically converted to: "/mcp/projects/myfile.txt"

# Just use the validation function:
file_path = validate_fs_path(user_path)  # Returns Path object
```

## Common Patterns

### Async Tools with Multiple Operations

```python
@mcp.tool()
async def search_all(query: str) -> Dict[str, Any]:
    """Search multiple sources in parallel"""
    response = await search_manager.search_all(query)
    return response.to_dict()
```

### Tools with Complex Parameters

```python
@mcp.tool()
async def complex_tool(
    data: str,  # JSON string
    options: str = None  # Comma-separated options
) -> Dict[str, Any]:
    # Parse JSON
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data"}
    
    # Parse options
    options_list = []
    if options:
        options_list = [opt.strip() for opt in options.split(',')]
    
    response = my_feature.process(data_dict, options_list)
    return response.to_dict()
```

### Environment Variables

```python
class MyFeatureEngine(BaseFeature):
    def __init__(self):
        super().__init__("my_feature", "1.0.0")
        
        # Read configuration from environment
        self.api_key = os.environ.get("MY_FEATURE_API_KEY")
        self.timeout = int(os.environ.get("MY_FEATURE_TIMEOUT", "30"))
        
        if not self.api_key:
            self.logger.warning("API key not configured")
```

## Testing Commands

```bash
# Run server locally
python run_server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector --url http://localhost:8000/mcp

# Run tests
python -m pytest tests/

# Check specific feature
python test_features.py
```

## Debugging Tips

1. **Enable Debug Logging**:
```python
logging.basicConfig(level=logging.DEBUG)
```

2. **Log Tool Inputs**:
```python
@mcp.tool()
async def my_tool(param: str) -> Dict[str, Any]:
    logger.debug(f"my_tool called with param: {param}")
    response = my_feature.my_method(param)
    logger.debug(f"my_tool response: {response}")
    return response.to_dict()
```

3. **Check Parameter Types**:
```python
@mcp.tool()
async def my_tool(param: str) -> Dict[str, Any]:
    logger.debug(f"param type: {type(param)}, value: {param}")
    # FastMCP might send strings even for numeric types!
```

## Response Format

Always return a dictionary from tools:

```python
# Feature method returns ToolResponse
response = my_feature.method(param)

# Tool must convert to dict
return response.to_dict()

# Direct dictionary also works
return {
    "success": True,
    "data": {"key": "value"},
    "error": None,
    "metadata": {"timestamp": datetime.now().isoformat()}
}
```

## Remember

- ✅ Use `param: str = None` instead of `Optional[str]`
- ✅ Convert string inputs to expected types
- ✅ Always call `.to_dict()` on ToolResponse
- ✅ Handle lists as comma-separated strings
- ✅ Log important operations for debugging
- ✅ Validate inputs before processing
- ✅ Use try/except with `handle_error()`
- ✅ Update system_info when adding features

This architecture makes it easy to add new tools while maintaining consistency!
