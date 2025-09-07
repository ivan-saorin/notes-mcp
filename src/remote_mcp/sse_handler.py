#!/usr/bin/env python3
"""
Server-Sent Events (SSE) endpoint for real-time UI updates
Production-ready with reconnection support and heartbeat
"""

import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from starlette.responses import StreamingResponse
from starlette.requests import Request

from .event_manager import (
    event_manager,
    EventType,
    EventFilter,
    EventPriority,
    Connection
)

logger = logging.getLogger(__name__)

# ============================================================================
# SSE Message Formatting
# ============================================================================

class SSEMessage:
    """Format messages for Server-Sent Events"""
    
    @staticmethod
    def format(data: Any, 
               event: Optional[str] = None,
               id: Optional[str] = None,
               retry: Optional[int] = None) -> str:
        """
        Format a message for SSE
        
        Args:
            data: Message data (will be JSON-encoded if not string)
            event: Event type name
            id: Message ID for reconnection
            retry: Retry timeout in milliseconds
        """
        lines = []
        
        if id:
            lines.append(f"id: {id}")
        if event:
            lines.append(f"event: {event}")
        if retry is not None:
            lines.append(f"retry: {retry}")
        
        # Format data
        if not isinstance(data, str):
            data = json.dumps(data)
        
        # Split data by newlines and format
        for line in data.split('\n'):
            lines.append(f"data: {line}")
        
        # SSE requires double newline at end
        return '\n'.join(lines) + '\n\n'
    
    @staticmethod
    def heartbeat() -> str:
        """Create a heartbeat message"""
        return SSEMessage.format(
            data={"type": "heartbeat", "timestamp": datetime.now().isoformat()},
            event="heartbeat"
        )
    
    @staticmethod
    def error(message: str, code: Optional[str] = None) -> str:
        """Create an error message"""
        return SSEMessage.format(
            data={"type": "error", "message": message, "code": code},
            event="error"
        )

# ============================================================================
# SSE Stream Generator
# ============================================================================

async def create_sse_stream(request: Request,
                           connection_id: Optional[str] = None,
                           channels: Optional[list] = None,
                           heartbeat_interval: int = 30) -> AsyncGenerator[str, None]:
    """
    Create an SSE stream for a client
    
    Args:
        request: Starlette request object
        connection_id: Optional connection ID (will be generated if not provided)
        channels: Channels to subscribe to (default: ["*"])
        heartbeat_interval: Seconds between heartbeats
    
    Yields:
        SSE formatted messages
    """
    # Generate connection ID if not provided
    conn_id = connection_id or str(uuid.uuid4())
    
    # Default to all events
    if not channels:
        channels = ["*"]
    
    # Create connection
    try:
        conn = await event_manager.connection_pool.create_connection(
            connection_id=conn_id,
            metadata={
                "type": "sse",
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "channels": channels
            }
        )
        
        # Subscribe to channels
        for channel in channels:
            conn.subscriptions.add(channel)
        
        # Send initial connection event
        yield SSEMessage.format(
            data={
                "type": "connection",
                "connection_id": conn_id,
                "channels": channels,
                "timestamp": datetime.now().isoformat()
            },
            event="connection",
            id=conn_id,
            retry=5000  # 5 second retry
        )
        
        logger.info(f"SSE connection established: {conn_id}")
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(conn_id, heartbeat_interval)
        )
        
        try:
            # Main event loop
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected: {conn_id}")
                    break
                
                try:
                    # Wait for event with timeout for heartbeat
                    event = await asyncio.wait_for(
                        conn.queue.get(),
                        timeout=heartbeat_interval
                    )
                    
                    # Format and send event
                    yield SSEMessage.format(
                        data=event.to_dict(),
                        event=event.type.value,
                        id=event.id
                    )
                    
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield SSEMessage.heartbeat()
                    
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    yield SSEMessage.error(str(e))
                    
        finally:
            # Cleanup
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
                
    except Exception as e:
        logger.error(f"Failed to create SSE connection: {e}")
        yield SSEMessage.error(f"Connection failed: {e}")
    
    finally:
        # Remove connection
        await event_manager.connection_pool.remove_connection(conn_id)
        logger.info(f"SSE connection closed: {conn_id}")

async def _heartbeat_loop(connection_id: str, interval: int):
    """Send heartbeat events periodically"""
    while True:
        try:
            await asyncio.sleep(interval)
            
            # Send heartbeat event through event manager
            await event_manager.emit(
                event_type=EventType.HEARTBEAT,
                source="system",
                target="connection",
                action="heartbeat",
                data={"connection_id": connection_id},
                priority=EventPriority.LOW
            )
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")

# ============================================================================
# SSE Endpoint Handler
# ============================================================================

async def sse_endpoint(request: Request) -> StreamingResponse:
    """
    SSE endpoint handler for Starlette
    
    Query parameters:
        - channels: Comma-separated list of channels (default: "*")
        - last_event_id: Resume from this event ID (for reconnection)
        - connection_id: Use specific connection ID (for reconnection)
    """
    # Parse query parameters
    channels = request.query_params.get("channels", "*").split(",")
    last_event_id = request.query_params.get("last_event_id")
    connection_id = request.query_params.get("connection_id")
    
    # Handle reconnection
    if last_event_id:
        logger.info(f"SSE reconnection requested from event: {last_event_id}")
        # Could replay missed events here if needed
    
    # Create response with proper headers
    return StreamingResponse(
        create_sse_stream(
            request=request,
            connection_id=connection_id,
            channels=channels
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS
        }
    )

# ============================================================================
# JavaScript Client Code (to be embedded in HTML)
# ============================================================================

SSE_CLIENT_JS = """
// EventManager client for real-time updates
class EventManagerClient {
    constructor(url = '/events', options = {}) {
        this.url = url;
        this.options = {
            channels: ['*'],
            reconnectInterval: 5000,
            maxReconnectAttempts: 10,
            heartbeatTimeout: 60000,
            ...options
        };
        
        this.eventSource = null;
        this.connectionId = null;
        this.lastEventId = null;
        this.reconnectAttempts = 0;
        this.handlers = new Map();
        this.heartbeatTimer = null;
        
        // Auto-connect
        this.connect();
    }
    
    connect() {
        // Build URL with parameters
        const params = new URLSearchParams({
            channels: this.options.channels.join(',')
        });
        
        if (this.connectionId) {
            params.append('connection_id', this.connectionId);
        }
        
        if (this.lastEventId) {
            params.append('last_event_id', this.lastEventId);
        }
        
        const url = `${this.url}?${params}`;
        
        // Create EventSource
        this.eventSource = new EventSource(url);
        
        // Connection established
        this.eventSource.addEventListener('connection', (e) => {
            const data = JSON.parse(e.data);
            this.connectionId = data.connection_id;
            this.reconnectAttempts = 0;
            console.log('EventManager connected:', this.connectionId);
            this.trigger('connected', data);
            this.resetHeartbeat();
        });
        
        // Handle events
        this.eventSource.addEventListener('message', (e) => {
            const event = JSON.parse(e.data);
            this.lastEventId = e.lastEventId;
            this.handleEvent(event);
            this.resetHeartbeat();
        });
        
        // Handle specific event types
        ['create', 'update', 'delete', 'navigate', 'error'].forEach(type => {
            this.eventSource.addEventListener(type, (e) => {
                const event = JSON.parse(e.data);
                this.lastEventId = e.lastEventId;
                this.handleEvent(event);
                this.resetHeartbeat();
            });
        });
        
        // Handle heartbeat
        this.eventSource.addEventListener('heartbeat', (e) => {
            this.resetHeartbeat();
            this.trigger('heartbeat', JSON.parse(e.data));
        });
        
        // Handle errors
        this.eventSource.onerror = (e) => {
            console.error('EventSource error:', e);
            this.eventSource.close();
            this.trigger('error', e);
            
            // Reconnect logic
            if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Reconnecting in ${this.options.reconnectInterval}ms (attempt ${this.reconnectAttempts})`);
                setTimeout(() => this.connect(), this.options.reconnectInterval);
            } else {
                console.error('Max reconnection attempts reached');
                this.trigger('disconnected', {reason: 'max_attempts'});
            }
        };
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        if (this.heartbeatTimer) {
            clearTimeout(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
        
        this.trigger('disconnected', {reason: 'manual'});
    }
    
    resetHeartbeat() {
        if (this.heartbeatTimer) {
            clearTimeout(this.heartbeatTimer);
        }
        
        this.heartbeatTimer = setTimeout(() => {
            console.warn('Heartbeat timeout - reconnecting');
            this.eventSource.close();
            this.connect();
        }, this.options.heartbeatTimeout);
    }
    
    handleEvent(event) {
        console.debug('Event received:', event);
        
        // Trigger specific handlers
        const key = `${event.target}:${event.type}`;
        this.trigger(key, event);
        
        // Trigger wildcard handlers
        this.trigger(`${event.target}:*`, event);
        this.trigger(`*:${event.type}`, event);
        this.trigger('*', event);
        
        // Handle UI hints
        if (event.metadata?.ui_hint) {
            this.handleUIHint(event.metadata.ui_hint, event);
        }
    }
    
    handleUIHint(hint, event) {
        switch (hint) {
            case 'navigate_to':
                if (event.data?.id) {
                    this.navigateTo(event.target, event.data.id);
                }
                break;
            case 'refresh':
                this.refreshElement(event.target, event.data?.id);
                break;
            case 'focus':
                this.focusElement(event.target, event.data?.id);
                break;
        }
    }
    
    on(pattern, handler) {
        if (!this.handlers.has(pattern)) {
            this.handlers.set(pattern, new Set());
        }
        this.handlers.get(pattern).add(handler);
        return () => this.off(pattern, handler);
    }
    
    off(pattern, handler) {
        const handlers = this.handlers.get(pattern);
        if (handlers) {
            handlers.delete(handler);
            if (handlers.size === 0) {
                this.handlers.delete(pattern);
            }
        }
    }
    
    trigger(pattern, data) {
        const handlers = this.handlers.get(pattern);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error('Handler error:', error);
                }
            });
        }
    }
    
    // UI Helper methods
    navigateTo(type, id) {
        // Override in your application
        console.log(`Navigate to ${type}/${id}`);
    }
    
    refreshElement(type, id) {
        // Override in your application
        console.log(`Refresh ${type}/${id}`);
    }
    
    focusElement(type, id) {
        // Override in your application
        console.log(`Focus ${type}/${id}`);
    }
}

// Auto-initialize on window load
if (typeof window !== 'undefined') {
    window.EventManagerClient = EventManagerClient;
}
"""

__all__ = [
    'sse_endpoint',
    'create_sse_stream',
    'SSEMessage',
    'SSE_CLIENT_JS'
]
