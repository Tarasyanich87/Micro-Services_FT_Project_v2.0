import asyncio
import redis.asyncio as redis
import json

# --- Configuration ---
REDIS_URL = "redis://localhost:6379"
STREAM_NAME = "mcp_commands"
CONSUMER_GROUP = "verification_group"
CONSUMER_NAME = "verifier"

async def publisher():
    """Connects to Redis and publishes a single test message."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        await r.ping()
        print("Publisher connected to Redis.")

        test_message = {
            "command": "PING",
            "payload": {"message": "Hello from publisher!"},
            "timestamp": asyncio.get_event_loop().time()
        }

        message_id = await r.xadd(STREAM_NAME, {"data": json.dumps(test_message)})
        print(f"Published message with ID: {message_id}")
        await r.close()

    except redis.RedisError as e:
        print(f"Publisher error: {e}")

async def consumer():
    """Connects, creates a consumer group, and listens for one message."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        await r.ping()
        print("Consumer connected to Redis.")

        try:
            await r.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="$", mkstream=True)
            print(f"Created consumer group '{CONSUMER_GROUP}'.")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                print(f"Consumer group '{CONSUMER_GROUP}' already exists.")
            else:
                raise

        print("Consumer is waiting for a message...")
        # Read a single message from the stream, blocking for up to 5 seconds.
        messages = await r.xreadgroup(
            groupname=CONSUMER_GROUP,
            consumername=CONSUMER_NAME,
            streams={STREAM_NAME: ">"},
            count=1,
            block=5000
        )

        if not messages:
            print("Consumer timed out. No message received.")
            return

        for stream, message_list in messages:
            for message_id, data in message_list:
                print(f"\n--- Message Received ---")
                print(f"  Stream: {stream}")
                print(f"  Message ID: {message_id}")
                payload = json.loads(data['data'])
                print(f"  Data: {payload}")
                print("------------------------")

                # Acknowledge the message
                await r.xack(stream, CONSUMER_GROUP, message_id)
                print("Message acknowledged.")

        await r.close()

    except redis.RedisError as e:
        print(f"Consumer error: {e}")

async def main():
    print("--- Starting Redis Stream Verification ---")
    # Run consumer in the background
    consumer_task = asyncio.create_task(consumer())

    # Give the consumer a moment to start up
    await asyncio.sleep(1)

    # Run the publisher
    await publisher()

    # Wait for the consumer to finish
    await consumer_task
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
