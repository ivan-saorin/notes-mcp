# Real-Time Collaboration Framework

## Overview

This production-ready event-driven framework enables seamless real-time collaboration between Claude (via MCP) and users (via Web UI). Any action on either side triggers instant updates on the other, creating a truly collaborative environment.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Claude (MCP)  │────▶│Event Manager │◀────│   Web UI        │
│                 │◀────│              │────▶│                 │
│ wait_for_updates│     │ - Queues     │ SSE │ Auto-updates    │
└─────────────────┘     │ - Routing    │     └─────────────────┘
                        │ - History    │
                        └──────────────┘
```

## Key Features

### 1. **Event Manager** (Production-Ready)
- Singleton pattern with thread-safe operations
- Connection pooling with automatic cleanup
- Rate limiting (1000 events/minute per connection)
- Event prioritization (LOW, NORMAL, HIGH, CRITICAL)
- Metrics and monitoring
- Retry logic with exponential backoff
- Event TTL and expiration
- Correlation IDs for tracking related events

### 2. **Long-Polling for Claude** (`wait_for_updates`)
Claude can actively watch for changes:

```python
# Claude watches for updates
result = await wait_for_updates(
    targets=["note", "task"],  # What to watch
    timeout=30,                # Max wait time
    since=last_event_id        # Get events after this ID
)

if result["status"] == "updates":
    for event in result["events"]:
        # Process each update
        print(f"{event['type']}: {event['data']}")
```

### 3. **Server-Sent Events (SSE) for UI**
Real-time push updates to the browser:

```javascript
// UI automatically receives updates
eventManager.on('note:create', (event) => {
    // Note was created (by Claude or another user)
    addNoteToList(event.data);
    showNotification(`New note: ${event.data.title}`);
});
```

### 4. **Event Decorators for MCP**
Automatic event emission from MCP methods:

```python
@mcp.tool()
@emit_event(EventType.CREATE, target="note", ui_hint="navigate_to")
async def create_note(title, content):
    # Method executes normally
    note = create_note_logic(title, content)
    return note
    # Event automatically emitted after success
```

## Event Types

### Standard Events
- `CREATE` - New resource created
- `UPDATE` - Resource modified  
- `DELETE` - Resource removed
- `NAVIGATE` - UI should navigate
- `REFRESH` - UI should refresh
- `SYNC_START/END` - Synchronization events
- `CONFLICT` - Concurrent edit conflict

### Event Structure
```json
{
    "id": "evt_123",
    "type": "create",
    "source": "mcp|ui|system",
    "target": "note|task",
    "action": "create_note",
    "data": {
        "id": "note-1",
        "title": "My Note",
        "content": "..."
    },
    "metadata": {
        "ui_hint": "navigate_to",
        "user": "claude",
        "session": "sess_456"
    },
    "priority": "high",
    "timestamp": "2024-01-20T10:30:00Z"
}
```

## Usage Examples

### Example 1: Claude Creating a Note

```python
# Claude creates a note
note = await create_note(
    title="Meeting Notes",
    content="Discussion points..."
)

# Event automatically emitted:
# - Type: CREATE
# - Target: note
# - UI Hint: navigate_to

# UI automatically:
# 1. Adds note to list
# 2. Shows notification
# 3. Navigates to the note
```

### Example 2: Claude Watching for User Edits

```python
# Claude enters collaborative mode
while collaborating:
    updates = await wait_for_updates(
        targets=["note"],
        timeout=30
    )
    
    if updates["status"] == "updates":
        for event in updates["events"]:
            if event["type"] == "update":
                # User edited a note
                note_id = event["data"]["id"]
                # Claude can now:
                # - Add suggestions
                # - Fix formatting
                # - Generate summaries
                enhanced = await enhance_note(note_id)
```

### Example 3: Handling Conflicts

```python
# Check for updates before editing
updates = await wait_for_updates(
    targets=["note"],
    timeout=2,  # Quick check
    since=last_sync_id
)

if updates["events"]:
    # Merge changes before proceeding
    await handle_conflicts(updates["events"])

# Now safe to edit
await update_note(note_id, new_content)
```

## Configuration

### Environment Variables
```bash
# Event System
MAX_EVENT_HISTORY=1000
MAX_CONNECTIONS=100
RATE_LIMIT_EVENTS=1000
CLEANUP_INTERVAL=60

# Timeouts
DEFAULT_TIMEOUT=30
MAX_TIMEOUT=300
HEARTBEAT_INTERVAL=30

# Debug
DEBUG=false
LOG_LEVEL=INFO
```

### Event Filtering

```python
# Create custom filters
filter = EventFilter(
    types=[EventType.CREATE, EventType.UPDATE],
    targets=["note"],
    priority_min=EventPriority.NORMAL,
    since="2024-01-20T10:00:00Z"
)

# Use in wait_for_updates
updates = await wait_for_updates(
    filters=filter,
    timeout=30
)
```

## JavaScript Client API

### Connection Management
```javascript
// Initialize
const eventManager = new EventManagerClient('/events', {
    channels: ['note:*', 'task:*'],
    reconnectInterval: 3000,
    maxReconnectAttempts: 20
});

// Listen for connection events
eventManager.on('connected', () => console.log('Connected'));
eventManager.on('disconnected', () => console.log('Disconnected'));
```

### Event Handling
```javascript
// Listen to specific patterns
eventManager.on('note:create', handleNoteCreate);
eventManager.on('note:update', handleNoteUpdate);
eventManager.on('note:*', handleAnyNoteEvent);
eventManager.on('*', handleAnyEvent);

// Unsubscribe
const unsubscribe = eventManager.on('note:create', handler);
unsubscribe(); // Remove handler
```

### UI Helpers
```javascript
// Override these for custom behavior
eventManager.navigateTo = (type, id) => {
    window.location.href = `/${type}/${id}`;
};

eventManager.refreshElement = (type, id) => {
    document.querySelector(`[data-${type}-id="${id}"]`).refresh();
};
```

## Monitoring & Metrics

### Health Check Endpoint
```bash
GET /health

{
    "status": "healthy",
    "components": {
        "mcp": "operational",
        "web": "operational", 
        "events": "operational"
    },
    "metrics": {
        "events": {
            "total_events": 1234,
            "events_per_second": 2.5,
            "active_connections": 5
        }
    }
}
```

### Event Metrics
```python
metrics = event_manager.get_metrics()
# {
#     "total_events": 1234,
#     "events_by_type": {"create": 100, "update": 200},
#     "failed_deliveries": 2,
#     "rate_limit_hits": 0
# }
```

## Production Considerations

### 1. **Scalability**
- Connection pooling with configurable limits
- Event queue management with overflow handling
- Automatic cleanup of stale connections

### 2. **Reliability**
- Retry logic for failed deliveries
- Heartbeat monitoring for connection health
- Graceful reconnection with event replay

### 3. **Security**
- Rate limiting per connection
- Connection authentication (extend as needed)
- Event validation and sanitization

### 4. **Performance**
- Event prioritization for critical updates
- Batching support for bulk operations
- Async/await throughout for non-blocking I/O

## Testing

### Manual Testing
```python
# 1. Start the unified server
python run_unified_server.py

# 2. Open web UI
# http://localhost:8000/app

# 3. In another terminal, test MCP
python test_collaboration.py

# 4. Watch real-time updates in both UI and console
```

### Load Testing
```python
# Simulate multiple clients
async def load_test():
    tasks = []
    for i in range(100):
        task = asyncio.create_task(
            wait_for_updates(
                connection_id=f"client_{i}",
                timeout=60
            )
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    print(f"Handled {len(results)} concurrent connections")
```

## Troubleshooting

### Common Issues

1. **Events not received**
   - Check connection status in UI
   - Verify event channels match
   - Check rate limiting

2. **High latency**
   - Monitor event queue sizes
   - Check network connectivity
   - Review event priorities

3. **Memory usage**
   - Adjust MAX_EVENT_HISTORY
   - Enable cleanup tasks
   - Monitor connection pool

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitor event flow
event_manager.register_handler("*", lambda e: print(f"Event: {e}"))
```

## Future Enhancements

1. **WebSocket Support** - Bidirectional communication
2. **Event Persistence** - Store events in database
3. **Cluster Support** - Redis pub/sub for scaling
4. **Event Replay** - Time-travel debugging
5. **GraphQL Subscriptions** - Alternative to SSE
6. **Conflict Resolution** - Automatic CRDT merging

## License

MIT License - See LICENSE file for details.
