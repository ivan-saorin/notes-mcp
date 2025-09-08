#!/usr/bin/env python3
"""
Production-Ready Real-time Event Manager for MCP-UI Collaboration
Provides bidirectional event communication with long-polling support
"""

import asyncio
import json
import logging
import uuid
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import functools
import weakref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

class EventConfig:
    """Event system configuration"""
    MAX_EVENT_HISTORY = 1000
    MAX_QUEUE_SIZE = 100
    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300  # 5 minutes max
    CLEANUP_INTERVAL = 60  # Cleanup dead connections every minute
    EVENT_TTL = 3600  # Events expire after 1 hour
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1.0
    METRICS_INTERVAL = 300  # Log metrics every 5 minutes
    MAX_CONNECTIONS = 100
    RATE_LIMIT_EVENTS = 1000  # Max events per minute per connection
    RATE_LIMIT_WINDOW = 60

# ============================================================================
# Event Types and Data Structures
# ============================================================================

class EventType(Enum):
    """Standard event types for MCP-UI communication"""
    # Data events
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    LIST = "list"
    BATCH = "batch"
    
    # Navigation events
    NAVIGATE = "navigate"
    REFRESH = "refresh"
    FOCUS = "focus"
    
    # System events
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    
    # Sync events
    SYNC_START = "sync_start"
    SYNC_END = "sync_end"
    CONFLICT = "conflict"
    
    # Custom events
    CUSTOM = "custom"

class EventPriority(Enum):
    """Event priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Event:
    """Event data structure with validation"""
    id: str
    type: EventType
    source: str
    target: str
    action: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: EventPriority = EventPriority.NORMAL
    ttl: int = None  # Time to live in seconds
    retry_count: int = 0
    correlation_id: str = None  # For tracking related events
    
    def __post_init__(self):
        """Validate event data"""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not isinstance(self.type, EventType):
            self.type = EventType(self.type)
        if not isinstance(self.priority, EventPriority):
            self.priority = EventPriority(self.priority)
        if self.ttl is None:
            self.ttl = EventConfig.EVENT_TTL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['type'] = self.type.value
        result['priority'] = self.priority.value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create from dictionary with validation"""
        try:
            data['type'] = EventType(data['type'])
            data['priority'] = EventPriority(data.get('priority', 1))
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to create event from dict: {e}")
            raise ValueError(f"Invalid event data: {e}")
    
    def is_expired(self) -> bool:
        """Check if event has expired"""
        if not self.ttl:
            return False
        created = datetime.fromisoformat(self.timestamp)
        return datetime.now() - created > timedelta(seconds=self.ttl)

@dataclass
class EventFilter:
    """Filter criteria for events"""
    types: List[EventType] = None
    sources: List[str] = None
    targets: List[str] = None
    priority_min: EventPriority = EventPriority.LOW
    exclude_expired: bool = True
    since: str = None  # ISO timestamp or event ID
    correlation_id: str = None
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria"""
        if self.exclude_expired and event.is_expired():
            return False
        if self.types and event.type not in self.types:
            return False
        if self.sources and event.source not in self.sources:
            return False
        if self.targets and event.target not in self.targets:
            return False
        if event.priority.value < self.priority_min.value:
            return False
        if self.correlation_id and event.correlation_id != self.correlation_id:
            return False
        if self.since:
            if len(self.since) == 36:  # UUID format (event ID)
                # This would need event ordering logic
                pass
            else:  # ISO timestamp
                if event.timestamp < self.since:
                    return False
        return True

# ============================================================================
# Connection and Subscription Management
# ============================================================================

@dataclass
class Connection:
    """Represents a client connection"""
    id: str
    created_at: datetime
    last_activity: datetime
    subscriptions: Set[str] = field(default_factory=set)
    queue: asyncio.Queue = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_count: int = 0
    rate_limit_window_start: float = field(default_factory=time.time)
    rate_limit_count: int = 0
    
    def is_rate_limited(self) -> bool:
        """Check if connection is rate limited"""
        now = time.time()
        if now - self.rate_limit_window_start > EventConfig.RATE_LIMIT_WINDOW:
            self.rate_limit_window_start = now
            self.rate_limit_count = 0
            return False
        return self.rate_limit_count >= EventConfig.RATE_LIMIT_EVENTS
    
    def increment_rate_limit(self):
        """Increment rate limit counter"""
        self.rate_limit_count += 1

class ConnectionPool:
    """Manages client connections with cleanup"""
    
    def __init__(self):
        self.connections: Dict[str, Connection] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task = None
    
    async def create_connection(self, 
                              connection_id: str = None,
                              metadata: Dict[str, Any] = None) -> Connection:
        """Create a new connection"""
        async with self._lock:
            if len(self.connections) >= EventConfig.MAX_CONNECTIONS:
                raise RuntimeError(f"Maximum connections ({EventConfig.MAX_CONNECTIONS}) reached")
            
            conn_id = connection_id or str(uuid.uuid4())
            if conn_id in self.connections:
                raise ValueError(f"Connection {conn_id} already exists")
            
            conn = Connection(
                id=conn_id,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                queue=asyncio.Queue(maxsize=EventConfig.MAX_QUEUE_SIZE),
                metadata=metadata or {}
            )
            self.connections[conn_id] = conn
            logger.info(f"Connection created: {conn_id}")
            return conn
    
    async def get_connection(self, connection_id: str) -> Connection:
        """Get a connection by ID"""
        async with self._lock:
            conn = self.connections.get(connection_id)
            if conn:
                conn.last_activity = datetime.now()
            return conn
    
    async def remove_connection(self, connection_id: str):
        """Remove a connection"""
        async with self._lock:
            if connection_id in self.connections:
                del self.connections[connection_id]
                logger.info(f"Connection removed: {connection_id}")
    
    async def cleanup_stale_connections(self, max_idle_seconds: int = 600):
        """Remove connections that have been idle too long"""
        async with self._lock:
            now = datetime.now()
            stale = []
            for conn_id, conn in self.connections.items():
                idle_time = (now - conn.last_activity).total_seconds()
                if idle_time > max_idle_seconds:
                    stale.append(conn_id)
            
            for conn_id in stale:
                del self.connections[conn_id]
                logger.info(f"Cleaned up stale connection: {conn_id}")
            
            return len(stale)
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(EventConfig.CLEANUP_INTERVAL)
                cleaned = await self.cleanup_stale_connections()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} stale connections")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

# ============================================================================
# Event Manager Singleton
# ============================================================================

class EventManager:
    """Production-ready event management system with monitoring"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.connection_pool = ConnectionPool()
            self.event_history: deque = deque(maxlen=EventConfig.MAX_EVENT_HISTORY)
            self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
            self.metrics = EventMetrics()
            self._background_tasks: List[asyncio.Task] = []
            logger.info("EventManager initialized")
    
    async def start(self):
        """Start event manager background tasks"""
        await self.connection_pool.start_cleanup_task()
        self._background_tasks.append(
            asyncio.create_task(self._metrics_loop())
        )
        logger.info("EventManager started")
    
    async def stop(self):
        """Stop event manager and cleanup"""
        await self.connection_pool.stop_cleanup_task()
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("EventManager stopped")
    
    async def emit(self,
                   event_type: EventType,
                   source: str,
                   target: str,
                   action: str,
                   data: Dict[str, Any],
                   metadata: Dict[str, Any] = None,
                   priority: EventPriority = EventPriority.NORMAL,
                   correlation_id: str = None) -> Event:
        """
        Emit an event to all subscribers with retry logic
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            target=target,
            action=action,
            data=data,
            metadata=metadata or {},
            priority=priority,
            correlation_id=correlation_id
        )
        
        # Add to history
        self.event_history.append(event)
        self.metrics.record_event(event)
        
        # Notify subscribers with retry
        await self._distribute_event(event)
        
        logger.debug(f"Event emitted: {action} on {target} (priority: {priority.name})")
        return event
    
    async def _distribute_event(self, event: Event):
        """Distribute event to all relevant subscribers"""
        channels = [
            f"{event.target}:{event.type.value}",
            f"{event.target}:*",
            f"*:{event.type.value}",
            "*"
        ]
        
        tasks = []
        for channel in channels:
            for conn_id in await self._get_channel_subscribers(channel):
                task = asyncio.create_task(
                    self._send_to_connection(conn_id, event)
                )
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _get_channel_subscribers(self, channel: str) -> List[str]:
        """Get all connections subscribed to a channel"""
        subscribers = []
        async with self.connection_pool._lock:
            for conn in self.connection_pool.connections.values():
                if channel in conn.subscriptions:
                    subscribers.append(conn.id)
        return subscribers
    
    async def _send_to_connection(self, connection_id: str, event: Event):
        """Send event to a specific connection with retry"""
        conn = await self.connection_pool.get_connection(connection_id)
        if not conn:
            return
        
        # Check rate limiting
        if conn.is_rate_limited():
            logger.warning(f"Connection {connection_id} is rate limited")
            self.metrics.record_rate_limit(connection_id)
            return
        
        conn.increment_rate_limit()
        
        # Try to send with retries
        for attempt in range(EventConfig.MAX_RETRY_ATTEMPTS):
            try:
                if conn.queue:
                    await asyncio.wait_for(
                        conn.queue.put(event),
                        timeout=1.0
                    )
                    conn.event_count += 1
                    return
            except asyncio.TimeoutError:
                if attempt < EventConfig.MAX_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(EventConfig.RETRY_DELAY * (attempt + 1))
                else:
                    logger.warning(f"Failed to send event to {connection_id} after {EventConfig.MAX_RETRY_ATTEMPTS} attempts")
                    self.metrics.record_failed_delivery(connection_id)
            except Exception as e:
                logger.error(f"Error sending to connection {connection_id}: {e}")
                break
    
    async def wait_for_updates(self,
                              connection_id: str,
                              targets: List[str] = None,
                              timeout: int = EventConfig.DEFAULT_TIMEOUT,
                              filters: EventFilter = None,
                              since: str = None) -> Dict[str, Any]:
        """
        Long-polling wait for updates (used by Claude)
        
        Returns:
            {
                "status": "updates" | "timeout" | "error",
                "events": [...],
                "summary": {...},
                "last_event_id": "...",
                "duration": 1.23
            }
        """
        start_time = time.time()
        
        # Validate timeout
        timeout = min(timeout, EventConfig.MAX_TIMEOUT)
        
        # Create or get connection
        conn = await self.connection_pool.get_connection(connection_id)
        if not conn:
            conn = await self.connection_pool.create_connection(connection_id)
        
        # Set up subscriptions
        channels = []
        if targets:
            for target in targets:
                channels.extend([f"{target}:*", f"*:{target}"])
        else:
            channels = ["*"]
        
        for channel in channels:
            conn.subscriptions.add(channel)
        
        # Create filter
        if not filters:
            filters = EventFilter(since=since)
        
        # Collect events
        events = []
        deadline = asyncio.get_event_loop().time() + timeout
        
        try:
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                
                try:
                    event = await asyncio.wait_for(
                        conn.queue.get(),
                        timeout=remaining
                    )
                    
                    if filters.matches(event):
                        events.append(event)
                        
                        # Check if this is a high-priority event that should trigger immediate return
                        if event.priority == EventPriority.CRITICAL:
                            break
                            
                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    logger.error(f"Error waiting for events: {e}")
                    return {
                        "status": "error",
                        "error": str(e),
                        "duration": time.time() - start_time
                    }
            
            # Prepare response
            if events:
                return {
                    "status": "updates",
                    "events": [e.to_dict() for e in events],
                    "summary": self._summarize_events(events),
                    "last_event_id": events[-1].id if events else None,
                    "duration": time.time() - start_time
                }
            else:
                return {
                    "status": "timeout",
                    "events": [],
                    "summary": {},
                    "duration": time.time() - start_time
                }
                
        finally:
            # Cleanup subscriptions if this was a temporary connection
            if conn.metadata.get("temporary"):
                await self.connection_pool.remove_connection(connection_id)
    
    def _summarize_events(self, events: List[Event]) -> Dict[str, Any]:
        """Create a summary of events"""
        summary = defaultdict(lambda: defaultdict(int))
        affected_ids = defaultdict(set)
        
        for event in events:
            summary[event.target][event.type.value] += 1
            if "id" in event.data:
                affected_ids[event.target].add(event.data["id"])
        
        return {
            "counts": dict(summary),
            "affected": {k: list(v) for k, v in affected_ids.items()},
            "total": len(events),
            "priority_breakdown": {
                p.name: sum(1 for e in events if e.priority == p)
                for p in EventPriority
            }
        }
    
    async def sync_changes(self,
                          connection_id: str,
                          last_sync_id: str = None,
                          include_full_state: bool = False) -> Dict[str, Any]:
        """Get all changes since last sync point"""
        events = []
        
        # Find events after last_sync_id
        found_sync_point = last_sync_id is None
        for event in self.event_history:
            if found_sync_point and not event.is_expired():
                events.append(event)
            elif event.id == last_sync_id:
                found_sync_point = True
        
        result = {
            "events": [e.to_dict() for e in events],
            "next_sync_id": events[-1].id if events else last_sync_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if include_full_state:
            # This would include current state from your data stores
            # For now, just a placeholder
            result["state"] = {
                "notes": {},  # Would fetch from notes_db
                "tasks": {}   # Would fetch from tasks_db
            }
        
        return result
    
    def register_handler(self, pattern: str, handler: Callable, priority: int = 0):
        """Register an event handler with priority"""
        self.event_handlers[pattern].append((priority, handler))
        self.event_handlers[pattern].sort(key=lambda x: x[0], reverse=True)
        logger.debug(f"Handler registered for pattern: {pattern}")
    
    def unregister_handler(self, pattern: str, handler: Callable):
        """Unregister an event handler"""
        self.event_handlers[pattern] = [
            (p, h) for p, h in self.event_handlers[pattern]
            if h != handler
        ]
    
    async def _execute_handlers(self, event: Event):
        """Execute registered event handlers"""
        patterns = [
            f"{event.target}:{event.type.value}",
            f"{event.target}:*",
            f"*:{event.type.value}",
            "*"
        ]
        
        for pattern in patterns:
            for priority, handler in self.event_handlers.get(pattern, []):
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}\n{traceback.format_exc()}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.get_summary()
    
    async def _metrics_loop(self):
        """Background metrics logging"""
        while True:
            try:
                await asyncio.sleep(EventConfig.METRICS_INTERVAL)
                metrics = self.get_metrics()
                logger.info(f"Event metrics: {json.dumps(metrics)}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")

# ============================================================================
# Metrics and Monitoring
# ============================================================================

class EventMetrics:
    """Track event system metrics"""
    
    def __init__(self):
        self.total_events = 0
        self.events_by_type = defaultdict(int)
        self.events_by_source = defaultdict(int)
        self.failed_deliveries = 0
        self.rate_limit_hits = 0
        self.start_time = time.time()
    
    def record_event(self, event: Event):
        """Record event metrics"""
        self.total_events += 1
        self.events_by_type[event.type.value] += 1
        self.events_by_source[event.source] += 1
    
    def record_failed_delivery(self, connection_id: str):
        """Record failed delivery"""
        self.failed_deliveries += 1
    
    def record_rate_limit(self, connection_id: str):
        """Record rate limit hit"""
        self.rate_limit_hits += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": uptime,
            "total_events": self.total_events,
            "events_per_second": self.total_events / uptime if uptime > 0 else 0,
            "events_by_type": dict(self.events_by_type),
            "events_by_source": dict(self.events_by_source),
            "failed_deliveries": self.failed_deliveries,
            "rate_limit_hits": self.rate_limit_hits
        }

# ============================================================================
# Decorators for MCP Methods
# ============================================================================

def emit_event(event_type: EventType = EventType.CUSTOM,
               target: str = None,
               extract_id: Callable = None,
               ui_hint: str = None,
               priority: EventPriority = EventPriority.NORMAL):
    """
    Decorator to automatically emit events from MCP methods
    
    Args:
        event_type: Type of event to emit
        target: Target resource (extracted from function name if not provided)
        extract_id: Function to extract resource ID from result
        ui_hint: Hint for UI behavior (e.g., "navigate_to", "refresh")
        priority: Event priority
    
    Example:
        @emit_event(EventType.CREATE, target="note", ui_hint="navigate_to")
        async def create_note(title, content):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get event manager instance
            manager = EventManager()
            
            # Determine target from function name if not provided
            nonlocal target
            if not target:
                # Extract from function name (e.g., "create_note" -> "note")
                parts = func.__name__.split('_')
                if len(parts) > 1:
                    target = parts[-1]
                else:
                    target = "unknown"
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Extract ID if extractor provided
                resource_id = None
                if extract_id and result:
                    resource_id = extract_id(result)
                elif isinstance(result, dict) and "id" in result:
                    resource_id = result["id"]
                
                # Prepare event metadata
                metadata = {
                    "function": func.__name__,
                    "source": "mcp"
                }
                if ui_hint:
                    metadata["ui_hint"] = ui_hint
                if resource_id:
                    metadata["resource_id"] = resource_id
                
                # Emit event
                await manager.emit(
                    event_type=event_type,
                    source="mcp",
                    target=target,
                    action=func.__name__,
                    data=result if isinstance(result, dict) else {"result": result},
                    metadata=metadata,
                    priority=priority
                )
                
                return result
                
            except Exception as e:
                # Emit error event
                await manager.emit(
                    event_type=EventType.ERROR,
                    source="mcp",
                    target=target,
                    action=func.__name__,
                    data={"error": str(e)},
                    metadata={"function": func.__name__},
                    priority=EventPriority.HIGH
                )
                raise
        
        return wrapper
    return decorator

# ============================================================================
# Context Manager for Event Sessions
# ============================================================================

@asynccontextmanager
async def event_session(connection_id: str = None,
                        metadata: Dict[str, Any] = None):
    """
    Context manager for event sessions
    
    Example:
        async with event_session() as session:
            events = await session.wait_for_updates(timeout=30)
    """
    manager = EventManager()
    conn_id = connection_id or str(uuid.uuid4())
    
    # Create connection
    conn = await manager.connection_pool.create_connection(
        conn_id,
        metadata={**(metadata or {}), "session": True}
    )
    
    try:
        yield manager
    finally:
        # Cleanup connection
        await manager.connection_pool.remove_connection(conn_id)

# ============================================================================
# Singleton Instance
# ============================================================================

# Create singleton instance
event_manager = EventManager()

# Export commonly used functions
async def emit(event_type: EventType, **kwargs) -> Event:
    """Convenience function to emit events"""
    return await event_manager.emit(event_type, **kwargs)

async def wait_for_updates(**kwargs) -> Dict[str, Any]:
    """Convenience function for long-polling"""
    connection_id = kwargs.pop('connection_id', str(uuid.uuid4()))
    return await event_manager.wait_for_updates(connection_id, **kwargs)

__all__ = [
    'EventManager',
    'Event',
    'EventType',
    'EventPriority',
    'EventFilter',
    'EventConfig',
    'emit_event',
    'event_session',
    'event_manager',
    'emit',
    'wait_for_updates'
]
