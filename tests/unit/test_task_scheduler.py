"""
Unit tests for TaskScheduler.
"""

import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.manifest import ModuleManifest
from Systems.core.tasks.scheduler import TaskScheduler


@pytest.fixture
def scheduler():
    """Create TaskScheduler instance."""
    return TaskScheduler()


@pytest.fixture
def mock_module():
    """Create mock module."""
    manifest = ModuleManifest(
        name="test_module",
        display_name="Test Module",
        version="1.0.0",
        background_tasks=["task1", "task2"],
    )
    
    module = MagicMock(spec=BaseModule)
    module.name = "test_module"
    module.manifest = manifest
    module._task_definitions = {
        "task1": {"type": "interval", "config": {"seconds": 60}},
        "task2": {"type": "cron", "config": {"hour": 12, "minute": 0}},
    }
    
    async def task1():
        pass
    
    async def task2():
        pass
    
    module.task1 = task1
    module.task2 = task2
    
    return module


@pytest.mark.asyncio
async def test_scheduler_initialization(scheduler: TaskScheduler) -> None:
    """Test scheduler initialization."""
    assert scheduler._started is False
    assert scheduler.scheduler is not None


@pytest.mark.asyncio
async def test_start_scheduler(scheduler: TaskScheduler) -> None:
    """Test starting scheduler."""
    await scheduler.start()
    
    assert scheduler._started is True
    
    await scheduler.stop()


@pytest.mark.asyncio
async def test_stop_scheduler(scheduler: TaskScheduler) -> None:
    """Test stopping scheduler."""
    await scheduler.start()
    await scheduler.stop()
    
    assert scheduler._started is False


@pytest.mark.asyncio
async def test_register_module_tasks(
    scheduler: TaskScheduler, mock_module
) -> None:
    """Test registering module tasks."""
    await scheduler.start()
    
    try:
        await scheduler.register_module_tasks(mock_module)
        
        tasks = scheduler.get_module_tasks("test_module")
        
        assert "task1" in tasks
        assert "task2" in tasks
    finally:
        await scheduler.stop()


@pytest.mark.asyncio
async def test_unregister_module_tasks(
    scheduler: TaskScheduler, mock_module
) -> None:
    """Test unregistering module tasks."""
    await scheduler.start()
    
    try:
        await scheduler.register_module_tasks(mock_module)
        await scheduler.unregister_module_tasks("test_module")
        
        tasks = scheduler.get_module_tasks("test_module")
        
        assert len(tasks) == 0
    finally:
        await scheduler.stop()


@pytest.mark.asyncio
async def test_register_tasks_not_started(
    scheduler: TaskScheduler, mock_module
) -> None:
    """Test registering tasks when scheduler not started."""
    # Should not raise error, just log warning
    await scheduler.register_module_tasks(mock_module)
    
    tasks = scheduler.get_module_tasks("test_module")
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_get_all_tasks(
    scheduler: TaskScheduler, mock_module
) -> None:
    """Test getting all tasks."""
    await scheduler.start()
    
    try:
        await scheduler.register_module_tasks(mock_module)
        
        all_tasks = scheduler.get_all_tasks()
        
        assert "test_module" in all_tasks
        assert "task1" in all_tasks["test_module"]
        assert "task2" in all_tasks["test_module"]
    finally:
        await scheduler.stop()


@pytest.mark.asyncio
async def test_task_error_handling(scheduler: TaskScheduler) -> None:
    """Test error handling in tasks."""
    manifest = ModuleManifest(
        name="test_module",
        display_name="Test Module",
        version="1.0.0",
        background_tasks=["error_task"],
    )
    
    module = MagicMock(spec=BaseModule)
    module.name = "test_module"
    module.manifest = manifest
    module._task_definitions = {
        "error_task": {"type": "interval", "config": {"seconds": 60}},
    }
    
    async def error_task():
        raise ValueError("Test error")
    
    module.error_task = error_task
    
    await scheduler.start()
    
    try:
        # Should not raise error, just log it
        await scheduler.register_module_tasks(module)
        
        tasks = scheduler.get_module_tasks("test_module")
        assert "error_task" in tasks
    finally:
        await scheduler.stop()


@pytest.mark.asyncio
async def test_double_start(scheduler: TaskScheduler) -> None:
    """Test starting scheduler twice."""
    await scheduler.start()
    
    # Should not raise error, just log warning
    await scheduler.start()
    
    assert scheduler._started is True
    
    await scheduler.stop()


@pytest.mark.asyncio
async def test_double_stop(scheduler: TaskScheduler) -> None:
    """Test stopping scheduler twice."""
    await scheduler.start()
    await scheduler.stop()
    
    # Should not raise error, just log warning
    await scheduler.stop()
    
    assert scheduler._started is False

