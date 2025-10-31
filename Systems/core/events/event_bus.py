"""
Event bus for module communication.
"""

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable

from Systems.core.logger import get_logger

logger = get_logger(__name__)


class EventBus:
    """
    Event bus for module communication.
    
    Provides publish-subscribe pattern for modules to communicate.
    
    Example:
        ```python
        from Systems.core.events import event_bus
        
        @event_bus.on("user.created")
        async def handle_user_created(data):
            print(f"User created: {data}")
        
        await event_bus.emit("user.created", {"user_id": 123})
        ```
    """
    
    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: dict[str, list[Callable[[Any], Awaitable[None]]]] = defaultdict(
            list
        )
        self._lock = asyncio.Lock()
        
        logger.debug("EventBus initialized")
    
    async def emit(self, event_name: str, data: Any = None) -> None:
        """
        Emit an event to all subscribed handlers.
        
        Args:
            event_name: Name of the event
            data: Event data (optional)
            
        Example:
            ```python
            await event_bus.emit("user.created", {"user_id": 123})
            ```
        """
        logger.debug(f"Emitting event: {event_name}")
        
        async with self._lock:
            handlers = self._handlers.get(event_name, []).copy()
        
        if not handlers:
            logger.debug(f"No handlers for event: {event_name}")
            return
        
        logger.info(f"Event {event_name} emitted to {len(handlers)} handlers")
        
        # Execute all handlers concurrently
        tasks = []
        for handler in handlers:
            tasks.append(self._execute_handler(handler, event_name, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_handler(
        self,
        handler: Callable[[Any], Awaitable[None]],
        event_name: str,
        data: Any,
    ) -> None:
        """
        Execute a single handler with error handling.
        
        Args:
            handler: Handler function
            event_name: Event name
            data: Event data
        """
        try:
            logger.debug(f"Executing handler for event: {event_name}")
            await handler(data)
            logger.debug(f"Handler executed successfully for event: {event_name}")
        except Exception as e:
            logger.error(
                f"Error in handler for event {event_name}: {e}",
                exc_info=True,
            )
    
    def on(self, event_name: str) -> Callable:
        """
        Decorator to register an event handler.
        
        Args:
            event_name: Name of the event to listen to
            
        Returns:
            Decorator function
            
        Example:
            ```python
            @event_bus.on("user.created")
            async def handle_user_created(data):
                print(f"User created: {data['user_id']}")
            ```
        """
        
        def decorator(handler: Callable[[Any], Awaitable[None]]) -> Callable:
            """Register handler."""
            asyncio.create_task(self.subscribe(event_name, handler))
            return handler
        
        return decorator
    
    async def subscribe(
        self,
        event_name: str,
        handler: Callable[[Any], Awaitable[None]],
    ) -> None:
        """
        Subscribe a handler to an event.
        
        Args:
            event_name: Name of the event
            handler: Handler function (async)
            
        Example:
            ```python
            async def handle_user_created(data):
                print(f"User created: {data}")
            
            await event_bus.subscribe("user.created", handle_user_created)
            ```
        """
        logger.info(f"Subscribing handler to event: {event_name}")
        
        async with self._lock:
            if handler not in self._handlers[event_name]:
                self._handlers[event_name].append(handler)
                logger.debug(f"Handler subscribed to event: {event_name}")
            else:
                logger.warning(
                    f"Handler already subscribed to event: {event_name}"
                )
    
    async def unsubscribe(
        self,
        event_name: str,
        handler: Callable[[Any], Awaitable[None]],
    ) -> None:
        """
        Unsubscribe a handler from an event.
        
        Args:
            event_name: Name of the event
            handler: Handler function
            
        Example:
            ```python
            await event_bus.unsubscribe("user.created", handle_user_created)
            ```
        """
        logger.info(f"Unsubscribing handler from event: {event_name}")
        
        async with self._lock:
            if event_name in self._handlers:
                try:
                    self._handlers[event_name].remove(handler)
                    logger.debug(f"Handler unsubscribed from event: {event_name}")
                    
                    # Remove event if no handlers
                    if not self._handlers[event_name]:
                        del self._handlers[event_name]
                except ValueError:
                    logger.warning(
                        f"Handler not found for event: {event_name}"
                    )
    
    def get_handlers(self, event_name: str) -> list[Callable]:
        """
        Get all handlers for an event.
        
        Args:
            event_name: Name of the event
            
        Returns:
            List of handler functions
        """
        # Return copy (no need for lock in sync method)
        return self._handlers.get(event_name, []).copy()
    
    def get_all_events(self) -> list[str]:
        """
        Get all event names with handlers.
        
        Returns:
            List of event names
        """
        # Return copy of keys (no need for lock in sync method)
        return list(self._handlers.keys())


# Global event bus instance
event_bus = EventBus()

