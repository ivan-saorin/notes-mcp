"""
Quick test script for notes management functionality
Run this after starting the server with: python run_server.py
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_notes():
    """Test notes management via MCP protocol"""
    base_url = "http://localhost:8000/mcp"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Create a note
        print("\n1. Creating a note...")
        response = await client.post(base_url, json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "remote:write_note",
                "arguments": {
                    "title": "Test Note",
                    "content": "This is test content for notes management.",
                    "summary": "Testing notes functionality",
                    "tags": ["test", "demo"]
                }
            },
            "id": 1
        })
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Test 2: List all notes
        print("\n2. Listing all notes...")
        response = await client.post(base_url, json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "remote:list_notes",
                "arguments": {}
            },
            "id": 2
        })
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Extract note ID from list
        if "result" in result and "notes" in result["result"] and len(result["result"]["notes"]) > 0:
            note_id = result["result"]["notes"][0]["id"]
            
            # Test 3: Get specific note
            print(f"\n3. Getting note with ID: {note_id}")
            response = await client.post(base_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remote:get_note",
                    "arguments": {
                        "note_id": note_id
                    }
                },
                "id": 3
            })
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Test 4: Update note
            print(f"\n4. Updating note with ID: {note_id}")
            response = await client.post(base_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remote:write_note",
                    "arguments": {
                        "title": "Updated Test Note",
                        "content": "This content has been updated!",
                        "summary": "Updated test note",
                        "tags": ["test", "updated"],
                        "note_id": note_id
                    }
                },
                "id": 4
            })
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Test 5: Create another note with different tags
            print("\n5. Creating another note...")
            response = await client.post(base_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remote:write_note",
                    "arguments": {
                        "title": "Python Guide",
                        "content": "Python programming guide content.",
                        "summary": "Guide for Python programming",
                        "tags": ["python", "programming", "guide"]
                    }
                },
                "id": 5
            })
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Test 6: List notes by tag
            print("\n6. Listing notes with tag 'python'...")
            response = await client.post(base_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remote:list_notes",
                    "arguments": {
                        "tags": ["python"]
                    }
                },
                "id": 6
            })
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Test 7: Delete a note
            print(f"\n7. Deleting note with ID: {note_id}")
            response = await client.post(base_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remote:delete_note",
                    "arguments": {
                        "note_id": note_id
                    }
                },
                "id": 7
            })
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Test 8: List remaining notes
            print("\n8. Listing remaining notes...")
            response = await client.post(base_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remote:list_notes",
                    "arguments": {}
                },
                "id": 8
            })
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")


async def test_system_info():
    """Test system info endpoint"""
    base_url = "http://localhost:8000/mcp"
    
    async with httpx.AsyncClient() as client:
        print("\nTesting system info...")
        response = await client.post(base_url, json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "remote:system_info",
                "arguments": {}
            },
            "id": 0
        })
        result = response.json()
        print(f"System Info: {json.dumps(result, indent=2)}")


async def main():
    """Run all tests"""
    print("=== MCP Notes Management Test ===")
    print(f"Started at: {datetime.now().isoformat()}")
    
    # First check system info
    await test_system_info()
    
    # Then run notes tests
    await test_notes()
    
    print(f"\n=== Tests completed at: {datetime.now().isoformat()} ===")


if __name__ == "__main__":
    asyncio.run(main())
