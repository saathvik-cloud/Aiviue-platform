# server/test_queue.py
import asyncio
from app.shared.cache import init_redis, close_redis, RedisClient, get_redis_client
from app.shared.queue import QueueProducer, SimpleConsumer, QueueNames, JobPayload

async def test_queue():
    # Initialize Redis
    await init_redis()
    redis = await get_redis_client()
    client = RedisClient(redis)
    
    # Create producer
    producer = QueueProducer(client)
    
    # Test 1: Enqueue a job
    print("\n--- Test 1: Enqueue Job ---")
    job_id = await producer.enqueue(
        "test_queue",
        {"message": "Hello from test!", "value": 42},
        job_type="test_job",
    )
    print(f"Enqueued job: {job_id}")
    
    # Test 2: Check queue length
    print("\n--- Test 2: Queue Length ---")
    length = await producer.get_queue_length("test_queue")
    print(f"Queue length: {length}")
    
    # Test 3: Consume job with SimpleConsumer
    print("\n--- Test 3: Consume Job ---")
    processed_jobs = []
    
    async def handler(job: JobPayload) -> bool:
        print(f"Processing job: {job.job_id}")
        print(f"Job data: {job.data}")
        processed_jobs.append(job)
        return True
    
    consumer = SimpleConsumer(
        client,
        "test_queue",
        handler=handler,
        poll_timeout=2,  # Short timeout for test
    )
    
    # Run consumer for a few seconds
    async def run_consumer():
        await consumer.start()
    
    # Start consumer and stop after 3 seconds
    task = asyncio.create_task(run_consumer())
    await asyncio.sleep(3)
    await consumer.stop()
    task.cancel()
    
    print(f"\nProcessed {len(processed_jobs)} jobs")
    print(f"Consumer stats: {consumer.get_stats()}")
    
    # Cleanup
    await close_redis()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_queue()) 