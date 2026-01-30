"""
Events module for Aiviue Platform.

Provides Redis Streams-based event publishing for inter-service communication.

Components:
- EventPublisher: Publish events to streams
- Event schemas: Type-safe event definitions

Usage:
    from app.shared.events import EventPublisher, EventTypes, StreamNames
    from app.shared.events import JobPublishedEvent
    
    publisher = EventPublisher(redis_client)
    await publisher.publish_job_published(
        job_id="123",
        employer_id="456",
        title="Software Engineer",
        description="...",
    )
"""

from app.shared.events.publisher import (
    EventPublisher,
    Event,
    EventTypes,
    StreamNames,
)
from app.shared.events.schemas import (
    # Base
    BaseEvent,
    EventMetadata,
    EventEnvelope,
    # Job events
    JobCreatedEvent,
    JobPublishedEvent,
    JobUpdatedEvent,
    JobClosedEvent,
    JobDeletedEvent,
    # Employer events
    EmployerCreatedEvent,
    EmployerUpdatedEvent,
    EmployerVerifiedEvent,
    # Extraction events
    ExtractionStartedEvent,
    ExtractionCompletedEvent,
    ExtractionFailedEvent,
)

__all__ = [
    # Publisher
    "EventPublisher",
    "Event",
    "EventTypes",
    "StreamNames",
    # Base schemas
    "BaseEvent",
    "EventMetadata",
    "EventEnvelope",
    # Job events
    "JobCreatedEvent",
    "JobPublishedEvent",
    "JobUpdatedEvent",
    "JobClosedEvent",
    "JobDeletedEvent",
    # Employer events
    "EmployerCreatedEvent",
    "EmployerUpdatedEvent",
    "EmployerVerifiedEvent",
    # Extraction events
    "ExtractionStartedEvent",
    "ExtractionCompletedEvent",
    "ExtractionFailedEvent",
]
