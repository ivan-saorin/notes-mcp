"""
Example: Database Integration Tool

This example shows how to integrate a database with your MCP server.
"""

from typing import Dict, Any, List, Optional
import asyncio
import aiosqlite
from datetime import datetime

# Add this to your server.py

# Initialize database connection
DATABASE_PATH = "data/mcp.db"

async def init_database():
    """Initialize the database with required tables"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# Add these tools to your MCP server

# @mcp.tool()
async def db_item_create(
    name: str,
    description: str = None,
    category: str = None
) -> Dict[str, Any]:
    """
    Create a new item in the database
    
    Args:
        name: Item name
        description: Item description
        category: Item category
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO items (name, description, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, description, category, datetime.now(), datetime.now())
        )
        await db.commit()
        
        return {
            "id": cursor.lastrowid,
            "name": name,
            "description": description,
            "category": category,
            "created_at": datetime.now().isoformat()
        }

# @mcp.tool()
async def db_item_search(
    query: str = None,
    category: str = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for items in the database
    
    Args:
        query: Search query for name/description
        category: Filter by category
        limit: Maximum results to return
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        sql = "SELECT * FROM items WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        sql += f" ORDER BY created_at DESC LIMIT {limit}"
        
        async with db.execute(sql, params) as cursor:
            columns = [desc[0] for desc in cursor.description]
            results = []
            async for row in cursor:
                results.append(dict(zip(columns, row)))
            
            return results

# @mcp.tool()
async def db_item_update(
    item_id: int,
    name: str = None,
    description: str = None,
    category: str = None
) -> Dict[str, Any]:
    """
    Update an existing item
    
    Args:
        item_id: ID of item to update
        name: New name
        description: New description
        category: New category
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Build dynamic update query
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        
        if not updates:
            return {"error": "No fields to update"}
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(item_id)
        
        sql = f"UPDATE items SET {', '.join(updates)} WHERE id = ?"
        
        await db.execute(sql, params)
        await db.commit()
        
        # Fetch and return updated item
        async with db.execute("SELECT * FROM items WHERE id = ?", (item_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return {"error": f"Item {item_id} not found"}

# @mcp.tool()
async def db_item_delete(item_id: int) -> Dict[str, Any]:
    """
    Delete an item from the database
    
    Args:
        item_id: ID of item to delete
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM items WHERE id = ?", (item_id,))
        await db.commit()
        
        if cursor.rowcount > 0:
            return {"success": True, "message": f"Item {item_id} deleted"}
        return {"error": f"Item {item_id} not found"}

# Don't forget to add to your server startup:
# asyncio.create_task(init_database())
