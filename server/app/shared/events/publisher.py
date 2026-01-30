"""
Event Publisher for Aiviue Platform.

Publishes events to Redis Streams for inter-service communication.

This is used for:
- Communicating with Screening System (job.published, job.closed)
- Future microservice communication
- Event-driven architecture

Usage:
    from app.shared.events import EventPublisher, EventTypes
    
    publisher = EventPublisher(redis_client)
    
    await publisher.publish(
        EventTypes.JOB_PUBLISHED,
        {
            "job_id": "123",
            "employer_id": "456",
            "title": "Software Engineer",
        },
    )
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.shared.cache.redis_client import RedisClient
from app.shared.logging import get_logger


logger = get_logger(__name__)


class StreamNames:
    """
    Predefined stream names.
    
    Use these constants for consistency across services.
    """
    
    # Job-related events (consumed by Screening System)
    JOBS = "events:jobs"
    
    # Employer-related events
    EMPLOYERS = "events:employers"
    
    # Extraction events (internal)
    EXTRACTIONS = "events:extractions"
    
    # General notifications
    NOTIFICATIONS = "events:notifications"


class EventTypes:
    """
    Predefined event types.
    
    Use these constants for consistency.
    """
    
    # Job events
    JOB_CREATED = "job.created"
    JOB_UPDATED = "job.updated"
    JOB_PUBLISHED = "job.published"
    JOB_CLOSED = "job.closed"
    JOB_DELETED = "job.deleted"
    
    # Employer events
    EMPLOYER_CREATED = "employer.created"
    EMPLOYER_UPDATED = "employer.updated"
    EMPLOYER_VERIFIED = "employer.verified"
    
    # Extraction events
    EXTRACTION_STARTED = "extraction.started"
    EXTRACTION_COMPLETED = "extraction.completed"
    EXTRACTION_FAILED = "extraction.failed"


class Event:
    """
    Event data structure.
    
    Every event has:
    - event_id: Unique identifier
    - event_type: Type of event (e.g., "job.published")
    - timestamp: When event was created
    - data: Event payload
    - metadata: Additional context
    """
    
    def __init__(
        self,
        event_type: str,
        data: dict[str, Any],
        event_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.data = data
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create from dictionary."""
        event = cls(
            event_type=data["event_type"],
            data=data["data"],
            event_id=data["event_id"],
            metadata=data.get("metadata", {}),
        )
        event.timestamp = data["timestamp"]
        return event


class EventPublisher:
    """
    Publishes events to Redis Streams.
    
    Args:
        client: RedisClient instance
        default_stream: Default stream name (optional)
    
    Usage:
        publisher = EventPublisher(redis_client)
        
        # Publish to specific stream
        await publisher.publish(
            EventTypes.JOB_PUBLISHED,
            {"job_id": "123"},
            stream=StreamNames.JOBS,
        )
        
        # Use convenience methods
        await publisher.publish_job_published(job_id="123", ...)
    """
    
    def __init__(
        self,
        client: RedisClient,
        default_stream: str = StreamNames.JOBS,
    ) -> None:
        self.client = client
        self.default_stream = default_stream
    
    async def publish(
        self,
        event_type: str,
        data: dict[str, Any],
        stream: Optional[str] = None,
        event_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Publish an event to a stream.
        
        Args:
            event_type: Type of event (use EventTypes constants)
            data: Event payload
            stream: Stream name (uses default if not specified)
            event_id: Custom event ID (auto-generated if not provided)
            metadata: Additional metadata
        
        Returns:
            Message ID from Redis or None if failed
        
        Example:
            message_id = await publisher.publish(
                EventTypes.JOB_PUBLISHED,
                {"job_id": "123", "title": "Engineer"},
            )
        """
        stream_name = stream or self.default_stream
        
        # Create event
        event = Event(
            event_type=event_type,
            data=data,
            event_id=event_id,
            metadata=metadata,
        )
        
        # Publish to stream
        message_id = await self.client.stream_publish(
            stream_name,
            event.to_dict(),
        )
        
        if message_id:
            logger.info(
                f"Event published: {event_type}",
                extra={
                    "event": "event_published",
                    "event_id": event.event_id,
                    "event_type": event_type,
                    "stream": stream_name,
                    "message_id": message_id,
                },
            )
        else:
            logger.error(
                f"Failed to publish event: {event_type}",
                extra={
                    "event": "event_publish_failed",
                    "event_id": event.event_id,
                    "event_type": event_type,
                    "stream": stream_name,
                },
            )
        
        return message_id
    
    # ==================== CONVENIENCE METHODS ====================
    
    async def publish_job_created(
        self,
        job_id: str,
        employer_id: str,
        title: str,
        **extra_data: Any,
    ) -> Optional[str]:
        """Publish job.created event."""
        return await self.publish(
            EventTypes.JOB_CREATED,
            {
                "job_id": job_id,
                "employer_id": employer_id,
                "title": title,
                **extra_data,
            },
            stream=StreamNames.JOBS,
        )
    
    async def publish_job_published(
        self,
        job_id: str,
        employer_id: str,
        title: str,
        description: str,
        location: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        **extra_data: Any,
    ) -> Optional[str]:
        """
        Publish job.published event.
        
        This event is consumed by the Screening System to:
        - Distribute job to advertising channels (Meta, etc.)
        - Start sourcing candidates
        """
        return await self.publish(
            EventTypes.JOB_PUBLISHED,
            {
                "job_id": job_id,
                "employer_id": employer_id,
                "title": title,
                "description": description,
                "location": location,
                "salary_min": salary_min,
                "salary_max": salary_max,
                **extra_data,
            },
            stream=StreamNames.JOBS,
        )
    
    async def publish_job_closed(
        self,
        job_id: str,
        employer_id: str,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        """
        Publish job.closed event.
        
        This event tells the Screening System to:
        - Stop advertising the job
        - Stop accepting new candidates
        """
        return await self.publish(
            EventTypes.JOB_CLOSED,
            {
                "job_id": job_id,
                "employer_id": employer_id,
                "reason": reason,
            },
            stream=StreamNames.JOBS,
        )
    
    async def publish_extraction_completed(
        self,
        extraction_id: str,
        job_id: Optional[str] = None,
        employer_id: Optional[str] = None,
    ) -> Optional[str]:
        """Publish extraction.completed event."""
        return await self.publish(
            EventTypes.EXTRACTION_COMPLETED,
            {
                "extraction_id": extraction_id,
                "job_id": job_id,
                "employer_id": employer_id,
            },
            stream=StreamNames.EXTRACTIONS,
        )
