"""
Task scheduler for module background tasks.
"""

import asyncio
from collections import defaultdict
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from Systems.core.logger import get_logger
from Systems.core.modules.base_module import BaseModule

logger = get_logger(__name__)


class TaskScheduler:
    """
    Task scheduler for SwiftDevBot modules.
    
    Uses APScheduler to schedule background tasks from modules.
    
    Example:
        ```python
        scheduler = TaskScheduler()
        await scheduler.start()
        
        # Register tasks from module
        await scheduler.register_module_tasks(module)
        ```
    """
    
    def __init__(self) -> None:
        """Initialize task scheduler."""
        self.scheduler = AsyncIOScheduler()
        self._module_tasks: dict[str, list[str]] = defaultdict(list)
        self._started = False
        
        logger.debug("TaskScheduler initialized")
    
    async def start(self) -> None:
        """
        Start the scheduler.
        
        Example:
            ```python
            await scheduler.start()
            ```
        """
        if self._started:
            logger.warning("Scheduler already started")
            return
        
        logger.info("Starting task scheduler...")
        
        self.scheduler.start()
        self._started = True
        
        logger.info("Task scheduler started")
    
    async def stop(self) -> None:
        """
        Stop the scheduler.
        
        Example:
            ```python
            await scheduler.stop()
            ```
        """
        if not self._started:
            logger.warning("Scheduler not started")
            return
        
        logger.info("Stopping task scheduler...")
        
        self.scheduler.shutdown(wait=True)
        self._started = False
        
        logger.info("Task scheduler stopped")
    
    async def register_module_tasks(self, module: BaseModule) -> None:
        """
        Register background tasks from a module.
        
        Parses background_tasks from module manifest and schedules them.
        
        Args:
            module: Module instance
            
        Example:
            ```python
            await scheduler.register_module_tasks(module)
            ```
        """
        if not self._started:
            logger.warning(
                f"Cannot register tasks for module {module.name}: scheduler not started"
            )
            return
        
        manifest = module.manifest
        
        if not manifest.background_tasks:
            logger.debug(f"No background tasks in module: {module.name}")
            return
        
        logger.info(
            f"Registering {len(manifest.background_tasks)} tasks for module: {module.name}"
        )
        
        # Get task definitions from module
        task_definitions = getattr(module, "_task_definitions", {})
        
        for task_name in manifest.background_tasks:
            # Check if task exists in module
            task_func = getattr(module, task_name, None)
            
            if not task_func or not callable(task_func):
                logger.warning(
                    f"Task {task_name} not found in module {module.name}"
                )
                continue
            
            # Get task definition
            task_def = task_definitions.get(task_name, {})
            
            # Schedule task
            try:
                await self._schedule_task(module.name, task_name, task_func, task_def)
                self._module_tasks[module.name].append(task_name)
                logger.debug(
                    f"Task {task_name} scheduled for module {module.name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to schedule task {task_name} for module {module.name}: {e}",
                    exc_info=True,
                )
    
    async def _schedule_task(
        self,
        module_name: str,
        task_name: str,
        task_func: Callable,
        task_def: dict[str, Any],
    ) -> None:
        """
        Schedule a single task.
        
        Args:
            module_name: Module name
            task_name: Task name
            task_func: Task function
            task_def: Task definition from manifest
        """
        # Parse schedule type
        schedule_type = task_def.get("type", "interval")
        schedule_config = task_def.get("config", {})
        
        # Create trigger based on schedule type
        if schedule_type == "interval":
            # Interval schedule (e.g., every 5 minutes)
            seconds = schedule_config.get("seconds", 60)
            trigger = IntervalTrigger(seconds=seconds)
        elif schedule_type == "cron":
            # Cron schedule (e.g., every day at 12:00)
            trigger = CronTrigger(**schedule_config)
        else:
            logger.warning(
                f"Unknown schedule type {schedule_type} for task {task_name}, using interval"
            )
            trigger = IntervalTrigger(seconds=60)
        
        # Wrap task function with error handling
        wrapped_func = self._wrap_task_with_error_handling(
            module_name, task_name, task_func
        )
        
        # Add job ID
        job_id = f"{module_name}.{task_name}"
        
        # Schedule task
        self.scheduler.add_job(
            wrapped_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
        )
        
        logger.debug(f"Task {task_name} scheduled with {schedule_type} trigger")
    
    def _wrap_task_with_error_handling(
        self,
        module_name: str,
        task_name: str,
        task_func: Callable,
    ) -> Callable:
        """
        Wrap task function with error handling.
        
        Args:
            module_name: Module name
            task_name: Task name
            task_func: Task function
            
        Returns:
            Wrapped task function
        """
        
        async def wrapped_task() -> None:
            """Wrapped task with error handling."""
            try:
                logger.info(
                    f"Executing task {task_name} for module {module_name}"
                )
                
                # Execute task
                if asyncio.iscoroutinefunction(task_func):
                    await task_func()
                else:
                    task_func()
                
                logger.info(
                    f"Task {task_name} completed successfully for module {module_name}"
                )
            except Exception as e:
                logger.error(
                    f"Error in task {task_name} for module {module_name}: {e}",
                    exc_info=True,
                )
        
        return wrapped_task
    
    async def unregister_module_tasks(self, module_name: str) -> None:
        """
        Unregister all tasks for a module.
        
        Args:
            module_name: Module name
            
        Example:
            ```python
            await scheduler.unregister_module_tasks("my_module")
            ```
        """
        if module_name not in self._module_tasks:
            logger.debug(f"No tasks registered for module: {module_name}")
            return
        
        logger.info(f"Unregistering tasks for module: {module_name}")
        
        task_names = self._module_tasks[module_name].copy()
        
        for task_name in task_names:
            job_id = f"{module_name}.{task_name}"
            
            try:
                self.scheduler.remove_job(job_id)
                logger.debug(f"Removed task {task_name} for module {module_name}")
            except Exception as e:
                logger.warning(
                    f"Failed to remove task {task_name} for module {module_name}: {e}"
                )
        
        del self._module_tasks[module_name]
    
    def get_module_tasks(self, module_name: str) -> list[str]:
        """
        Get all task names for a module.
        
        Args:
            module_name: Module name
            
        Returns:
            List of task names
        """
        return self._module_tasks.get(module_name, []).copy()
    
    def get_all_tasks(self) -> dict[str, list[str]]:
        """
        Get all tasks grouped by module.
        
        Returns:
            Dictionary of module_name -> list of task names
        """
        return {k: v.copy() for k, v in self._module_tasks.items()}

