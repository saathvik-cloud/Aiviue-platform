import asyncio
from app.shared.cache import init_redis, get_redis_client, RedisClient
from app.shared.events.publisher import EventPublisher, EventTypes

async def test_events():
    await init_redis()
    redis = await get_redis_client()
    client = RedisClient(redis)
    
    publisher = EventPublisher(client)
    
    # Publish event
    message_id = await publisher.publish_job_published(
        job_id="test-123",
        employer_id="emp-456",
        title="Test Job",
        description="Test description",
    )
    print(f"Published: {message_id}")
    
    # Read from stream to verify
    messages = await client.stream_read("events:jobs", last_id="0")
    print(f"Messages: {messages}")

asyncio.run(test_events())