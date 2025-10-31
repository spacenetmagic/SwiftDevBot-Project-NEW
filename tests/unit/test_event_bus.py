"""
Unit tests for EventBus.
"""

import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.core.events.event_bus import EventBus


@pytest.fixture
def event_bus_instance():
    """Create EventBus instance."""
    return EventBus()


@pytest.mark.asyncio
async def test_emit_no_handlers(event_bus_instance: EventBus) -> None:
    """Test emitting event with no handlers."""
    # Should not raise error
    await event_bus_instance.emit("test.event", {"data": "test"})


@pytest.mark.asyncio
async def test_subscribe_and_emit(event_bus_instance: EventBus) -> None:
    """Test subscribing handler and emitting event."""
    handler_called = []
    
    async def handler(data):
        handler_called.append(data)
    
    await event_bus_instance.subscribe("test.event", handler)
    await event_bus_instance.emit("test.event", {"data": "test"})
    
    # Wait a bit for async execution
    await asyncio.sleep(0.1)
    
    assert len(handler_called) == 1
    assert handler_called[0] == {"data": "test"}


@pytest.mark.asyncio
async def test_multiple_handlers(event_bus_instance: EventBus) -> None:
    """Test multiple handlers for same event."""
    handler1_called = []
    handler2_called = []
    
    async def handler1(data):
        handler1_called.append(data)
    
    async def handler2(data):
        handler2_called.append(data)
    
    await event_bus_instance.subscribe("test.event", handler1)
    await event_bus_instance.subscribe("test.event", handler2)
    
    await event_bus_instance.emit("test.event", {"data": "test"})
    
    # Wait a bit for async execution
    await asyncio.sleep(0.1)
    
    assert len(handler1_called) == 1
    assert len(handler2_called) == 1


@pytest.mark.asyncio
async def test_decorator_handler(event_bus_instance: EventBus) -> None:
    """Test using decorator to register handler."""
    handler_called = []
    
    @event_bus_instance.on("test.event")
    async def handler(data):
        handler_called.append(data)
    
    # Wait for async subscription
    await asyncio.sleep(0.1)
    
    await event_bus_instance.emit("test.event", {"data": "test"})
    
    # Wait a bit for async execution
    await asyncio.sleep(0.1)
    
    assert len(handler_called) == 1


@pytest.mark.asyncio
async def test_unsubscribe(event_bus_instance: EventBus) -> None:
    """Test unsubscribing handler."""
    handler_called = []
    
    async def handler(data):
        handler_called.append(data)
    
    await event_bus_instance.subscribe("test.event", handler)
    await event_bus_instance.unsubscribe("test.event", handler)
    
    await event_bus_instance.emit("test.event", {"data": "test"})
    
    # Wait a bit for async execution
    await asyncio.sleep(0.1)
    
    assert len(handler_called) == 0


@pytest.mark.asyncio
async def test_handler_error_handling(event_bus_instance: EventBus) -> None:
    """Test error handling in handlers."""
    handler_called = []
    
    async def error_handler(data):
        raise ValueError("Test error")
    
    async def normal_handler(data):
        handler_called.append(data)
    
    await event_bus_instance.subscribe("test.event", error_handler)
    await event_bus_instance.subscribe("test.event", normal_handler)
    
    # Should not raise error, normal handler should still execute
    await event_bus_instance.emit("test.event", {"data": "test"})
    
    # Wait a bit for async execution
    await asyncio.sleep(0.1)
    
    assert len(handler_called) == 1


@pytest.mark.asyncio
async def test_get_handlers(event_bus_instance: EventBus) -> None:
    """Test getting handlers for event."""
    async def handler1(data):
        pass
    
    async def handler2(data):
        pass
    
    await event_bus_instance.subscribe("test.event", handler1)
    await event_bus_instance.subscribe("test.event", handler2)
    
    handlers = event_bus_instance.get_handlers("test.event")
    
    assert len(handlers) == 2
    assert handler1 in handlers
    assert handler2 in handlers


@pytest.mark.asyncio
async def test_get_all_events(event_bus_instance: EventBus) -> None:
    """Test getting all events."""
    async def handler(data):
        pass
    
    await event_bus_instance.subscribe("event1", handler)
    await event_bus_instance.subscribe("event2", handler)
    
    events = event_bus_instance.get_all_events()
    
    assert "event1" in events
    assert "event2" in events


@pytest.mark.asyncio
async def test_emit_with_none_data(event_bus_instance: EventBus) -> None:
    """Test emitting event with None data."""
    handler_called = []
    
    async def handler(data):
        handler_called.append(data)
    
    await event_bus_instance.subscribe("test.event", handler)
    await event_bus_instance.emit("test.event")
    
    # Wait a bit for async execution
    await asyncio.sleep(0.1)
    
    assert len(handler_called) == 1
    assert handler_called[0] is None

