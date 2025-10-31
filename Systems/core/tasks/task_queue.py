"""
Task queue for asynchronous task processing.
"""

import asyncio
import json
from typing import Any, Awaitable, Callable

from Systems.core.logger import get_logger

logger = get_logger(__name__)


class TaskQueue:
    """
    Task queue for asynchronous task processing.
    
    Uses Redis for task storage and processing.
    
    Example:
        ```python
        queue = TaskQueue(redis_client)
        await queue.enqueue("process_data", {"id": 123})
        await queue.process_queue()
        ```
    """
    
    def __init__(self, redis_client: Any = None) -> None:
        """
        Initialize task queue.
        
        Args:
            redis_client: Redis client (optional)
        """
        self.redis = redis_client
        self._processing = False
        self._max_retries = 3
        self._retry_delay = 60  # seconds
        
        logger.debug("TaskQueue initialized")
    
    async def enqueue(
        self,
        task_name: str,
        data: dict[str, Any] | None = None,
        priority: int = 0,
    ) -> str:
        """
        Enqueue a task for processing.
        
        Args:
            task_name: Name of the task
            data: Task data (optional)
            priority: Task priority (lower = higher priority)
            
        Returns:
            Task ID
            
        Example:
            ```python
            task_id = await queue.enqueue("process_data", {"id": 123})
            ```
        """
        if not self.redis:
            logger.warning("Redis client not available, task not enqueued")
            return ""
        
        import uuid
        
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "name": task_name,
            "data": data or {},
            "priority": priority,
            "retries": 0,
            "created_at": asyncio.get_event_loop().time(),
        }
        
        # Add to queue (sorted set by priority)
        queue_key = "task_queue"
        score = priority * 1000 + task_data["created_at"]  # Priority + timestamp
        
        try:
            await self.redis.zadd(
                queue_key,
                {json.dumps(task_data): score},
            )
            
            logger.info(f"Task {task_name} enqueued with ID: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_name}: {e}", exc_info=True)
            return ""
    
    async def process_queue(
        self,
        handler: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        """
        Process tasks from the queue.
        
        Args:
            handler: Task handler function (optional)
            
        Example:
            ```python
            async def handle_task(task_name, data):
                print(f"Processing {task_name}: {data}")
            
            await queue.process_queue(handle_task)
            ```
        """
        if not self.redis:
            logger.warning("Redis client not available, cannot process queue")
            return
        
        if self._processing:
            logger.warning("Queue processing already running")
            return
        
        if not handler:
            logger.warning("No handler provided, cannot process queue")
            return
        
        self._processing = True
        logger.info("Starting queue processing...")
        
        queue_key = "task_queue"
        
        try:
            while self._processing:
                # Get task with highest priority (lowest score)
                result = await self.redis.zrange(queue_key, 0, 0, withscores=True)
                
                if not result:
                    # No tasks, wait a bit
                    await asyncio.sleep(1)
                    continue
                
                task_json, score = result[0]
                task_data = json.loads(task_json)
                
                task_id = task_data["id"]
                task_name = task_data["name"]
                task_data_dict = task_data["data"]
                retries = task_data["retries"]
                
                # Remove from queue
                await self.redis.zrem(queue_key, task_json)
                
                # Process task
                try:
                    logger.info(
                        f"Processing task {task_name} (ID: {task_id}, retries: {retries})"
                    )
                    
                    await handler(task_name, task_data_dict)
                    
                    logger.info(f"Task {task_name} (ID: {task_id}) completed successfully")
                    
                except Exception as e:
                    logger.error(
                        f"Error processing task {task_name} (ID: {task_id}): {e}",
                        exc_info=True,
                    )
                    
                    # Retry logic
                    if retries < self._max_retries:
                        logger.info(
                            f"Retrying task {task_name} (ID: {task_id}, attempt {retries + 1}/{self._max_retries})"
                        )
                        
                        task_data["retries"] = retries + 1
                        new_score = score + self._retry_delay
                        
                        await self.redis.zadd(
                            queue_key,
                            {json.dumps(task_data): new_score},
                        )
                    else:
                        logger.error(
                            f"Task {task_name} (ID: {task_id}) failed after {self._max_retries} retries"
                        )
                        
                        # Move to failed queue
                        failed_key = "task_queue_failed"
                        await self.redis.lpush(
                            failed_key,
                            json.dumps(task_data),
                        )
        
        except asyncio.CancelledError:
            logger.info("Queue processing cancelled")
        except Exception as e:
            logger.error(f"Error in queue processing: {e}", exc_info=True)
        finally:
            self._processing = False
            logger.info("Queue processing stopped")
    
    async def stop_processing(self) -> None:
        """Stop queue processing."""
        self._processing = False
        logger.info("Stopping queue processing...")
    
    async def get_queue_size(self) -> int:
        """
        Get current queue size.
        
        Returns:
            Number of tasks in queue
        """
        if not self.redis:
            return 0
        
        queue_key = "task_queue"
        return await self.redis.zcard(queue_key)
    
    async def get_failed_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get failed tasks.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of failed task data
        """
        if not self.redis:
            return []
        
        failed_key = "task_queue_failed"
        tasks_json = await self.redis.lrange(failed_key, 0, limit - 1)
        
        tasks = []
        for task_json in tasks_json:
            try:
                tasks.append(json.loads(task_json))
            except Exception as e:
                logger.error(f"Failed to parse failed task: {e}")
        
        return tasks

