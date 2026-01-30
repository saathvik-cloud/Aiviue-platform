"""
Queue Consumer for Aiviue Platform.

Provides base class for background workers that process jobs from Redis queue.

Features:
- Blocking pop (waits for jobs)
- Automatic retry with exponential backoff
- Dead letter queue for failed jobs
- Graceful shutdown

Usage:
    from app.shared.queue import QueueConsumer, QueueNames
    
    class ExtractionConsumer(QueueConsumer):
        async def process_job(self, job: JobPayload) -> bool:
            # Process the job
            extraction_id = job.data["extraction_id"]
            raw_jd = job.data["raw_jd"]
            # ... do extraction ...
            return True  # Success
    
    # Run consumer
    consumer = ExtractionConsumer(redis_client, QueueNames.EXTRACTION)
    await consumer.start()
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from app.shared.cache.redis_client import RedisClient
from app.shared.logging import get_logger
from app.shared.queue.producer import JobPayload


logger = get_logger(__name__)


class QueueConsumer(ABC):
    """
    Base class for queue consumers (background workers).
    
    Subclass this and implement `process_job` method.
    
    Args:
        client: RedisClient instance
        queue_name: Name of queue to consume from
        poll_timeout: Seconds to wait for new jobs (default 5)
        max_retries: Max retry attempts per job (default 3)
    """
    
    def __init__(
        self,
        client: RedisClient,
        queue_name: str,
        poll_timeout: int = 5,
        max_retries: int = 3,
    ) -> None:
        self.client = client
        self.queue_name = queue_name
        self.poll_timeout = poll_timeout
        self.max_retries = max_retries
        self._running = False
        self._processed_count = 0
        self._failed_count = 0
    
    @abstractmethod
    async def process_job(self, job: JobPayload) -> bool:
        """
        Process a single job.
        
        Implement this method in subclass.
        
        Args:
            job: Job payload with data
        
        Returns:
            True if successful, False if failed (will retry)
        
        Raises:
            Exception: Will be caught and job will be retried
        """
        pass
    
    async def start(self) -> None:
        """
        Start consuming jobs from queue.
        
        Runs indefinitely until stop() is called.
        """
        self._running = True
        
        logger.info(
            f"Consumer started for queue: {self.queue_name}",
            extra={
                "event": "consumer_started",
                "queue": self.queue_name,
            },
        )
        
        while self._running:
            try:
                await self._poll_and_process()
            except asyncio.CancelledError:
                logger.info("Consumer received cancellation signal")
                break
            except Exception as e:
                logger.exception(
                    f"Consumer error: {e}",
                    extra={
                        "event": "consumer_error",
                        "queue": self.queue_name,
                        "error": str(e),
                    },
                )
                # Brief pause before continuing
                await asyncio.sleep(1)
        
        logger.info(
            f"Consumer stopped for queue: {self.queue_name}",
            extra={
                "event": "consumer_stopped",
                "queue": self.queue_name,
                "processed": self._processed_count,
                "failed": self._failed_count,
            },
        )
    
    async def stop(self) -> None:
        """Stop consuming jobs (graceful shutdown)."""
        self._running = False
    
    async def _poll_and_process(self) -> None:
        """Poll queue and process one job."""
        # Blocking pop with timeout
        raw_data = await self.client.queue_pop(
            self.queue_name,
            timeout=self.poll_timeout,
        )
        
        if raw_data is None:
            # Timeout, no jobs available
            return
        
        # Parse job payload
        try:
            job = JobPayload.from_dict(raw_data)
        except (KeyError, TypeError) as e:
            logger.error(
                f"Invalid job payload: {e}",
                extra={
                    "event": "invalid_job_payload",
                    "queue": self.queue_name,
                    "raw_data": raw_data,
                },
            )
            return
        
        # Process the job
        await self._handle_job(job)
    
    async def _handle_job(self, job: JobPayload) -> None:
        """Handle job processing with retry logic."""
        job.attempts += 1
        
        logger.info(
            f"Processing job: {job.job_id} (attempt {job.attempts}/{job.max_attempts})",
            extra={
                "event": "job_processing",
                "job_id": job.job_id,
                "job_type": job.job_type,
                "attempt": job.attempts,
                "queue": self.queue_name,
            },
        )
        
        start_time = datetime.now(timezone.utc)
        
        try:
            success = await self.process_job(job)
            
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            if success:
                self._processed_count += 1
                logger.info(
                    f"Job completed: {job.job_id} ({duration_ms:.0f}ms)",
                    extra={
                        "event": "job_completed",
                        "job_id": job.job_id,
                        "job_type": job.job_type,
                        "duration_ms": duration_ms,
                        "queue": self.queue_name,
                    },
                )
            else:
                await self._handle_failure(job, None)
                
        except Exception as e:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            logger.error(
                f"Job failed: {job.job_id} - {str(e)}",
                extra={
                    "event": "job_failed",
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "queue": self.queue_name,
                },
            )
            await self._handle_failure(job, e)
    
    async def _handle_failure(
        self,
        job: JobPayload,
        error: Optional[Exception],
    ) -> None:
        """Handle job failure - retry or move to dead letter queue."""
        if job.attempts < job.max_attempts:
            # Retry with exponential backoff
            delay = 2 ** job.attempts  # 2, 4, 8 seconds
            
            logger.warning(
                f"Retrying job {job.job_id} in {delay}s (attempt {job.attempts}/{job.max_attempts})",
                extra={
                    "event": "job_retry_scheduled",
                    "job_id": job.job_id,
                    "attempt": job.attempts,
                    "delay_seconds": delay,
                },
            )
            
            # Wait before retry
            await asyncio.sleep(delay)
            
            # Re-enqueue for retry
            await self.client.queue_push(self.queue_name, job.to_dict())
        else:
            # Max retries exceeded - move to dead letter queue
            self._failed_count += 1
            
            dead_letter_queue = f"{self.queue_name}:dead"
            
            # Add error info to job
            job_data = job.to_dict()
            job_data["failed_at"] = datetime.now(timezone.utc).isoformat()
            job_data["error"] = str(error) if error else "Unknown error"
            
            await self.client.queue_push(dead_letter_queue, job_data)
            
            logger.error(
                f"Job moved to dead letter queue: {job.job_id}",
                extra={
                    "event": "job_dead_lettered",
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "attempts": job.attempts,
                    "dead_letter_queue": dead_letter_queue,
                },
            )
    
    def get_stats(self) -> dict[str, Any]:
        """Get consumer statistics."""
        return {
            "queue": self.queue_name,
            "running": self._running,
            "processed_count": self._processed_count,
            "failed_count": self._failed_count,
        }


class SimpleConsumer(QueueConsumer):
    """
    Simple consumer that uses a callback function.
    
    Useful for quick testing or simple use cases.
    
    Usage:
        async def my_handler(job: JobPayload) -> bool:
            print(f"Processing: {job.data}")
            return True
        
        consumer = SimpleConsumer(
            redis_client,
            "my_queue",
            handler=my_handler,
        )
        await consumer.start()
    """
    
    def __init__(
        self,
        client: RedisClient,
        queue_name: str,
        handler: callable,
        **kwargs,
    ) -> None:
        super().__init__(client, queue_name, **kwargs)
        self._handler = handler
    
    async def process_job(self, job: JobPayload) -> bool:
        """Process job using the handler callback."""
        if asyncio.iscoroutinefunction(self._handler):
            return await self._handler(job)
        return self._handler(job)
