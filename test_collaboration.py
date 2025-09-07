#!/usr/bin/env python3
"""
Test Real-time Collaboration Features
Demonstrates Claude watching for updates and collaborating with UI users
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("collaboration-test")

# Server configuration
MCP_URL = "http://localhost:8000/mcp"
WEB_URL = "http://localhost:8000/app"

class CollaborationTester:
    """Test real-time collaboration features"""
    
    def __init__(self):
        self.session = None
        self.last_event_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_mcp_tool(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        payload = {
            "jsonrpc": "2.0",
            "method": f"tools/{tool}",
            "params": params,
            "id": 1
        }
        
        async with self.session.post(MCP_URL, json=payload) as response:
            result = await response.json()
            return result.get("result", result)
    
    async def test_claude_creates_note(self):
        """Test Claude creating a note that appears in UI"""
        logger.info("=" * 60)
        logger.info("TEST 1: Claude creates a note")
        logger.info("=" * 60)
        
        # Claude creates a note
        note = await self.call_mcp_tool("write_note", {
            "title": f"Claude's Note - {datetime.now().strftime('%H:%M:%S')}",
            "content": "This is a note created by Claude through MCP.\n\nIt should appear instantly in the web UI!",
            "summary": "Real-time collaboration test",
            "tags": ["ai-generated", "test", "real-time"]
        })
        
        logger.info(f"✓ Created note: {note.get('note', {}).get('id')}")
        logger.info("→ Check the web UI - the note should appear immediately!")
        return note
    
    async def test_claude_watches_for_updates(self):
        """Test Claude watching for user updates"""
        logger.info("=" * 60)
        logger.info("TEST 2: Claude watches for user updates")
        logger.info("=" * 60)
        logger.info("Claude is now watching for 30 seconds...")
        logger.info("→ Go to the web UI and create or edit a note!")
        logger.info("→ URL: http://localhost:8000/app")
        logger.info("-" * 60)
        
        # Claude waits for updates
        result = await self.call_mcp_tool("wait_for_updates", {
            "targets": ["note"],
            "timeout": 30,
            "since": self.last_event_id
        })
        
        if result["status"] == "updates":
            logger.info(f"✓ Received {len(result['events'])} updates!")
            for event in result["events"]:
                logger.info(f"  - {event['type'].upper()}: {event['data'].get('title', event['data'].get('id'))}")
                logger.info(f"    Source: {event['source']}")
                logger.info(f"    Action: {event['action']}")
            
            self.last_event_id = result.get("last_event_id")
            return result["events"]
        else:
            logger.info("✗ No updates received (timeout)")
            return []
    
    async def test_claude_reacts_to_changes(self):
        """Test Claude reacting to user changes"""
        logger.info("=" * 60)
        logger.info("TEST 3: Claude reacts to user changes")
        logger.info("=" * 60)
        logger.info("Claude will watch and enhance any notes you create...")
        logger.info("→ Create a simple note in the web UI")
        logger.info("-" * 60)
        
        # Watch for new notes
        result = await self.call_mcp_tool("wait_for_updates", {
            "targets": ["note"],
            "timeout": 60,
            "since": self.last_event_id
        })
        
        if result["status"] == "updates":
            for event in result["events"]:
                if event["type"] == "create" and event["source"] == "ui":
                    note_id = event["data"]["id"]
                    logger.info(f"✓ Detected new note: {event['data']['title']}")
                    
                    # Claude enhances the note
                    logger.info("  → Claude is enhancing the note...")
                    
                    enhanced_content = event["data"]["content"] + "\n\n---\n**AI Enhancement:**\n"
                    enhanced_content += f"- Created at: {event['timestamp']}\n"
                    enhanced_content += f"- Word count: {len(event['data']['content'].split())}\n"
                    enhanced_content += f"- Character count: {len(event['data']['content'])}\n"
                    enhanced_content += f"- AI reviewed: ✓\n"
                    
                    # Update the note
                    await self.call_mcp_tool("write_note", {
                        "note_id": note_id,
                        "title": event["data"]["title"] + " [AI Enhanced]",
                        "content": enhanced_content,
                        "summary": event["data"]["summary"] + " (reviewed by AI)",
                        "tags": event["data"].get("tags", []) + ["ai-enhanced"]
                    })
                    
                    logger.info("  ✓ Note enhanced by Claude!")
                    logger.info("  → Check the web UI - the note should be updated!")
    
    async def test_concurrent_editing(self):
        """Test handling concurrent edits"""
        logger.info("=" * 60)
        logger.info("TEST 4: Concurrent editing simulation")
        logger.info("=" * 60)
        
        # Create a note
        note = await self.call_mcp_tool("write_note", {
            "title": "Concurrent Edit Test",
            "content": "Original content",
            "summary": "Testing concurrent edits",
            "tags": ["test"]
        })
        
        note_id = note["note"]["id"]
        logger.info(f"✓ Created test note: {note_id}")
        
        # Start watching for changes
        logger.info("→ Claude is watching for changes...")
        logger.info(f"→ Go edit the note '{note['note']['title']}' in the UI")
        
        # Watch for updates with quick check
        result = await self.call_mcp_tool("wait_for_updates", {
            "targets": ["note"],
            "timeout": 30,
            "since": self.last_event_id
        })
        
        if result["status"] == "updates":
            # Check if our note was edited
            for event in result["events"]:
                if event["data"].get("id") == note_id and event["type"] == "update":
                    logger.info("✓ Detected concurrent edit!")
                    logger.info(f"  - User updated: {event['data']['title']}")
                    
                    # Claude makes a non-conflicting update
                    await self.call_mcp_tool("write_note", {
                        "note_id": note_id,
                        "title": event["data"]["title"],
                        "content": event["data"]["content"] + "\n\n[Claude was here too!]",
                        "summary": event["data"]["summary"],
                        "tags": event["data"].get("tags", [])
                    })
                    
                    logger.info("  ✓ Claude added non-conflicting update")
    
    async def test_performance(self):
        """Test performance with multiple rapid updates"""
        logger.info("=" * 60)
        logger.info("TEST 5: Performance test")
        logger.info("=" * 60)
        
        # Create multiple notes rapidly
        logger.info("Creating 10 notes rapidly...")
        
        tasks = []
        for i in range(10):
            task = self.call_mcp_tool("write_note", {
                "title": f"Performance Test Note {i+1}",
                "content": f"Content for note {i+1}",
                "summary": f"Test note #{i+1}",
                "tags": ["performance-test"]
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        logger.info(f"✓ Created {len(results)} notes")
        logger.info("→ Check the web UI - all notes should appear!")
        
        # Clean up
        logger.info("Cleaning up test notes...")
        for result in results:
            if result.get("note", {}).get("id"):
                await self.call_mcp_tool("delete_note", {
                    "note_id": result["note"]["id"]
                })
        
        logger.info("✓ Cleanup complete")
    
    async def run_all_tests(self):
        """Run all collaboration tests"""
        try:
            # Test 1: Claude creates note
            await self.test_claude_creates_note()
            await asyncio.sleep(2)
            
            # Test 2: Claude watches for updates
            await self.test_claude_watches_for_updates()
            await asyncio.sleep(2)
            
            # Test 3: Claude reacts to changes
            await self.test_claude_reacts_to_changes()
            await asyncio.sleep(2)
            
            # Test 4: Concurrent editing
            await self.test_concurrent_editing()
            await asyncio.sleep(2)
            
            # Test 5: Performance
            await self.test_performance()
            
            logger.info("=" * 60)
            logger.info("ALL TESTS COMPLETE!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise

async def main():
    """Main test runner"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     Real-time Collaboration Test Suite                   ║
    ╠══════════════════════════════════════════════════════════╣
    ║ This test demonstrates the real-time collaboration       ║
    ║ features between Claude (MCP) and the Web UI.           ║
    ║                                                          ║
    ║ Prerequisites:                                           ║
    ║ 1. Start the unified server:                           ║
    ║    python run_unified_server.py                        ║
    ║                                                          ║
    ║ 2. Open the web UI in your browser:                    ║
    ║    http://localhost:8000/app                           ║
    ║                                                          ║
    ║ 3. Run this test script                                ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    input("Press Enter to start the tests...")
    
    async with CollaborationTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
