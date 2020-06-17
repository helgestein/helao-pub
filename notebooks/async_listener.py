from aiokafka import AIOKafkaConsumer
import asyncio

loop = asyncio.get_event_loop()

async def consume():
    consumer = AIOKafkaConsumer(
        'test',
        loop=loop, bootstrap_servers='localhost:9092',
        group_id="my-group")
    # Get cluster layout and join group `my-group`
    await consumer.start()
    try:
        # Consume messages
        async for msg in consumer:
            print("consumed: ", msg.topic, msg.partition, msg.offset,
                  msg.key, msg.value, msg.timestamp)
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()

loop.run_until_complete(consume())