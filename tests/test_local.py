#!/usr/bin/env python3
"""
Quick test to verify MCP server can be imported and run
"""

import sys
import os

# Add src to path (go up one level from tests/ to v2/, then into src/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    # Test standard library
    try:
        import json
        import asyncio
        from datetime import datetime
        print("  ✓ Standard library imports OK")
    except ImportError as e:
        print(f"  ✗ Standard library error: {e}")
        return False
    
    # Test web framework
    try:
        from starlette.applications import Starlette
        from starlette.responses import StreamingResponse, JSONResponse
        import uvicorn
        print("  ✓ Starlette/Uvicorn imports OK")
    except ImportError as e:
        print(f"  ✗ Web framework error: {e}")
        print("    Fix: pip install starlette uvicorn[standard]")
        return False
    
    # Test FastMCP
    try:
        from fastmcp import FastMCP
        print("  ✓ FastMCP imports OK")
    except ImportError as e:
        print(f"  ✗ FastMCP error: {e}")
        print("    Fix: pip install fastmcp")
        return False
    
    # Test our server
    try:
        from remote_mcp.server import mcp, app
        print("  ✓ Remote MCP server imports OK")
    except ImportError as e:
        print(f"  ✗ Server import error: {e}")
        return False
    
    return True

def test_server_creation():
    """Test server components"""
    print("\nTesting server components...")
    try:
        from remote_mcp.server import mcp, tasks_db, task_counter
        print(f"  ✓ MCP server created: {mcp.name}")
        print(f"  ✓ Task counter initialized: {task_counter}")
        print(f"  ✓ Tasks database ready: {len(tasks_db)} tasks")
        return True
    except Exception as e:
        print(f"  ✗ Server components error: {e}")
        return False

def test_web_app():
    """Test web application"""
    print("\nTesting web application...")
    try:
        from remote_mcp.server import app
        print(f"  ✓ Starlette app created")
        print(f"  ✓ Routes configured: {len(app.routes)} routes")
        return True
    except Exception as e:
        print(f"  ✗ Web app error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Remote MCP Server v2 - Local Test")
    print("=" * 50)
    
    all_ok = True
    
    # Test imports
    if not test_imports():
        all_ok = False
    
    # Test server
    if not test_server_creation():
        all_ok = False
    
    # Test web app
    if not test_web_app():
        all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ All tests passed!")
        print("\nYou can now run the server locally with:")
        print("  cd ..")
        print("  python run_server.py")
        print("\nOr use Docker:")
        print("  cd ..")
        print("  scripts\\windows\\build.bat")
    else:
        print("❌ Some tests failed")
        print("\nTo fix:")
        print("1. Install all dependencies:")
        print("   cd ..")
        print("   pip install -r requirements.txt")
        print("\n2. Make sure FastMCP is installed:")
        print("   pip install fastmcp")
        print("\n3. For Docker deployment (recommended):")
        print("   cd ..")
        print("   scripts\\windows\\build.bat")
    
    print("=" * 50)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
