"""
Queue Producer for Aiviue Platform.

Provides methods to enqueue jobs for background processing.

The queue uses Redis List with LPUSH (add to head) and BRPOP (remove from tail),
implementing a FIFO queue.

Usage:
    from app.shared.queue import QueueProducer, QueueNames
    
    producer = QueueProducer(redis_client)
    
    # Enqueue extraction job
    job_id = await producer.enqueue(
        QueueNames.EXTRACTION,
        {
            "extraction_id": "123",
            "raw_jd": "Looking for a software engineer...",
        },
    )
    
    # Check queue length
    length = await producer.get_queue_length(QueueNames.EXTRACTION)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.shared.cache.redis_client import RedisClient
from app.shared.logging import get_logger


logger = get_logger(__name__)


class QueueNames:
    """
    Predefined queue names.
    
    Use these constants to ensure consistency.
    """
    
    # JD extraction queue (LLM processing)
    EXTRACTION = "queue:extraction"
    
    # Job publishing queue (distribute to channels)
    JOB_PUBLISH = "queue:job_publish"
    
    # Email notification queue
    EMAIL = "queue:email"
    
    # General background tasks
    BACKGROUND = "queue:background"


class JobPayload:
    """
    Standard job payload structure.
    
    Every job in the queue has:
    - job_id: Unique identifier for tracking
    - job_type: Type of job (for routing)
    - data: Actual job data
    - created_at: When job was created
    - attempts: Number of processing attempts
    - max_attempts: Maximum retry attempts
    """
    
    def __init__(
        self,
        job_type: str,
        data: dict[str, Any],
        job_id: Optional[str] = None,
        max_attempts: int = 3,
    ) -> None:
        self.job_id = job_id or str(uuid.uuid4())
        self.job_type = job_type
        self.data = data
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.attempts = 0
        self.max_attempts = max_attempts
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "data": self.data,
            "created_at": self.created_at,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobPayload":
        """Create from dictionary."""
        payload = cls(
            job_type=data["job_type"],
            data=data["data"],
            job_id=data["job_id"],
            max_attempts=data.get("max_attempts", 3),
        )
        payload.created_at = data["created_at"]
        payload.attempts = data.get("attempts", 0)
        return payload


class QueueProducer:
    """
    Produces jobs to Redis queue.
    
    Uses Redis LPUSH to add jobs to the head of the list.
    Workers use BRPOP to consume from the tail (FIFO).
    
    Args:
        client: RedisClient instance
    """
    
    def __init__(self, client: RedisClient) -> None:
        self.client = client
    
    async def enqueue(
        self,
        queue_name: str,
        data: dict[str, Any],
        job_type: Optional[str] = None,
        job_id: Optional[str] = None,
        max_attempts: int = 3,
    ) -> str:
        """
        Enqueue a job for background processing.
        
        Args:
            queue_name: Name of the queue (use QueueNames constants)
            data: Job data (will be included in payload)
            job_type: Type of job (defaults to queue name)
            job_id: Custom job ID (auto-generated if not provided)
            max_attempts: Maximum retry attempts (default 3)
        
        Returns:
            Job ID
        
        Raises:
            Exception: If enqueue fails
        
        Example:
            job_id = await producer.enqueue(
                QueueNames.EXTRACTION,
                {"extraction_id": "123", "raw_jd": "..."},
            )
        """
        # Create job payload
        payload = JobPayload(
            job_type=job_type or queue_name,
            data=data,
            job_id=job_id,
            max_attempts=max_attempts,
        )
        
        # Enqueue
        success = await self.client.queue_push(queue_name, payload.to_dict())
        
        if success:
            logger.info(
                f"Job enqueued: {payload.job_id}",
                extra={
                    "event": "job_enqueued",
                    "job_id": payload.job_id,
                    "job_type": payload.job_type,
                    "queue": queue_name,
                },
            )
            return payload.job_id
        else:
            logger.error(
                f"Failed to enqueue job: {payload.job_id}",
                extra={
                    "event": "job_enqueue_failed",
                    "job_id": payload.job_id,
                    "queue": queue_name,
                },
            )
            raise Exception(f"Failed to enqueue job to {queue_name}")
    
    async def enqueue_extraction(
        self,
        extraction_id: str,
        raw_jd: str,
        employer_id: Optional[str] = None,
    ) -> str:
        """
        Convenience method to enqueue JD extraction job.
        
        Args:
            extraction_id: ID of extraction record in database
            raw_jd: Raw job description text
            employer_id: Optional employer ID
        
        Returns:
            Job ID
        """
        return await self.enqueue(
            queue_name=QueueNames.EXTRACTION,
            data={
                "extraction_id": extraction_id,
                "raw_jd": raw_jd,
                "employer_id": employer_id,
            },
            job_type="jd_extraction",
        )
    
    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get number of jobs waiting in queue.
        
        Args:
            queue_name: Name of the queue
        
        Returns:
            Number of pending jobs
        """
        return await self.client.queue_length(queue_name)
    
    async def get_queue_stats(self, queue_name: str) -> dict[str, Any]:
        """
        Get queue statistics.
        
        Args:
            queue_name: Name of the queue
        
        Returns:
            Dictionary with queue stats
        """
        length = await self.get_queue_length(queue_name)
        return {
            "queue": queue_name,
            "pending_jobs": length,
        }
