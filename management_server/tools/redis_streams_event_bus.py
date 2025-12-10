"""
Redis Streams Event Bus for robust inter-service communication.
This implementation uses Redis Streams with consumer groups and an acknowledgment
mechanism, providing more reliability than a simple Pub/Sub pattern.
"""
# type: ignore

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, Optional

import redis.asyncio as redis
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventMessage(BaseModel):
    """Defines the structure for all events passed through the bus."""

    type: str
    data: Dict[str, Any]
    source: str
    timestamp: float = Field(default_factory=time.time)
    version: int = 1

    def to_redis_dict(self) -> Dict[str, str]:
        """Serializes the event message for storage in Redis."""
        message_data = self.model_dump()
        redis_message: Dict[str, str] = {}
        for key, value in message_data.items():
            redis_message[key] = json.dumps(value)
        return redis_message


class RedisStreamsEventBus:
    """
    An event bus that uses Redis Streams for persistence and reliable delivery.
    """

    def __init__(self, redis_url: str, service_name: str):
        self.redis_url = redis_url
        self.service_name = service_name
        self.redis: Optional[redis.Redis] = None
        self._handlers: Dict[str, Callable] = {}
        self._listener_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self):
        """Connect to Redis and ping the server to ensure connectivity."""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info(
                f"✅ Event bus connected to Redis for service: {self.service_name}"
            )
        except redis.RedisError as e:
            logger.error(f"❌ Failed to connect event bus to Redis: {e}")
            self.redis = None

    async def disconnect(self):
        """Cancel listener tasks and close the Redis connection."""
        for task in self._listener_tasks.values():
            task.cancel()
        await asyncio.gather(*self._listener_tasks.values(), return_exceptions=True)
        self._listener_tasks.clear()

        if self.redis:
            await self.redis.close()
            self.redis = None
        logger.info(f"🔌 Event bus disconnected for service: {self.service_name}")

    async def publish(
        self, stream_name: str, event_data: Dict[str, Any], event_type: str
    ):
        """Publish an event to a specific Redis stream."""
        if not self.redis:
            logger.warning("Cannot publish event, Redis is not connected.")
            return

        try:
            event = EventMessage(
                type=event_type, data=event_data, source=self.service_name
            )
            message_dict = event.to_redis_dict()
            message_id = await self.redis.xadd(stream_name, message_dict)  # type: ignore[arg-type]
            logger.debug(
                f"📤 Published '{event_type}' to {stream_name} (ID: {message_id})"
            )
        except redis.RedisError as e:
            logger.error(f"❌ Failed to publish event to stream {stream_name}: {e}")

    async def subscribe(self, stream_name: str, callback: Callable):
        """Subscribe to a stream and start a background listener task."""
        if not self.redis:
            logger.error("Cannot subscribe, Redis is not connected.")
            return

        self._handlers[stream_name] = callback
        consumer_group = self.service_name

        try:
            await self.redis.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
            logger.info(
                f"📡 Created consumer group '{consumer_group}' for stream '{stream_name}'"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(
                    f"Consumer group '{consumer_group}' already exists for stream '{stream_name}'."
                )
                # Consumer group exists, continue with subscription
            else:
                logger.error(f"Error creating consumer group for {stream_name}: {e}")
                return

        # First, try to read any pending messages
        #         # await self._read_pending_messages(stream_name, consumer_group)  # Disabled due to bugs  # TODO: Fix this method

        task = asyncio.create_task(self._listen(stream_name, consumer_group))
        self._listener_tasks[stream_name] = task
        logger.info(f"🎧 Listening to stream '{stream_name}' in the background.")

    async def _read_pending_messages(self, stream_name: str, group_name: str):
        """Read any pending messages for this consumer group."""
        if not self.redis:
            logger.error("Redis not connected, cannot read pending messages")
            return

        try:
            consumer_name = f"{self.service_name}_{id(self)}"
            # Read pending messages
            pending = await self.redis.xpending(stream_name, group_name)  # type: ignore
            logger.info(f"XPENDING result: {pending}")

            # For now, let's just read all messages from the stream without consumer groups
            # This is a temporary solution
            all_messages = await self.redis.xrange(stream_name, "-", "+")  # type: ignore
            logger.info(f"Found {len(all_messages)} total messages in stream")

            for message_id, data in all_messages:
                try:
                    logger.info(f"Raw message {message_id}: {data}")
                    deserialized_data = {k: json.loads(v) for k, v in data.items()}
                    event = EventMessage(**deserialized_data)
                    logger.info(f"🔥 Calling handler for event: {event.type}")
                    await self._handlers[stream_name](event)
                    # Don't ack since we're not using consumer groups here
                    logger.info(f"✅ Processed message {message_id}")
                except Exception as e:
                    logger.exception(f"❌ Error processing message {message_id}")
                logger.info(
                    f"XREADGROUP result: {len(messages) if messages else 0} streams"
                )

                for _, message_list in messages:
                    logger.info(f"Processing {len(message_list)} messages")
                    for message_id, data in message_list:
                        try:
                            logger.info(f"Raw message {message_id}: {data}")
                            deserialized_data = {
                                k: json.loads(v) for k, v in data.items()
                            }
                            event = EventMessage(**deserialized_data)
                            logger.info(f"🔥 Calling handler for event: {event.type}")
                            await self._handlers[stream_name](event)
                            await self.redis.xack(stream_name, group_name, message_id)  # type: ignore
                            logger.info(f"✅ Processed pending message {message_id}")
                        except Exception as e:
                            logger.exception(
                                f"❌ Error processing pending message {message_id}"
                            )
                logger.info(
                    f"XREADGROUP result: {len(messages) if messages else 0} streams"
                )

                for _, message_list in messages:
                    logger.info(f"Processing {len(message_list)} messages")
                    for message_id, data in message_list:
                        try:
                            logger.info(f"Raw message {message_id}: {data}")
                            deserialized_data = {
                                k: json.loads(v) for k, v in data.items()
                            }
                            event = EventMessage(**deserialized_data)
                            logger.info(
                                f"🔥 Calling handler for event: {event.event_type}"
                            )
                            await self._handlers[stream_name](event)
                            await self.redis.xack(stream_name, group_name, message_id)
                            logger.info(f"✅ Processed pending message {message_id}")
                        except Exception as e:
                            logger.exception(
                                f"❌ Error processing pending message {message_id}"
                            )

        except Exception as e:
            logger.exception(f"Error reading pending messages for {stream_name}")

    async def _listen(self, stream_name: str, group_name: str):
        """The core listening loop for a consumer group."""
        consumer_name = f"{self.service_name}_{id(self)}"
        while self.redis:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={stream_name: ">"},
                    count=1,
                    block=0,  # Block indefinitely
                )
                for _, message_list in messages:
                    for message_id, data in message_list:
                        try:
                            # Deserialize data from JSON strings
                            deserialized_data = {
                                k: json.loads(v) for k, v in data.items()
                            }
                            event = EventMessage(**deserialized_data)
                            # Pass the event object to the handler
                            await self._handlers[stream_name](event)
                            await self.redis.xack(stream_name, group_name, message_id)
                        except Exception as e:
                            logger.exception(
                                f"Error processing message {message_id} from {stream_name}"
                            )
                            # Decide on an error handling strategy, e.g., move to a dead-letter queue.
            except redis.RedisError as e:
                logger.error(f"Redis error while listening to {stream_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception(f"Unexpected error in listener for {stream_name}")
                await asyncio.sleep(5)


# --- Pre-configured instances ---
# These can be configured with URLs from environment settings.
# For simplicity, we define them here.
core_streams_event_bus = RedisStreamsEventBus(
    redis_url="redis://localhost:6379", service_name="management_server"
)
mcp_streams_event_bus = RedisStreamsEventBus(
    redis_url="redis://localhost:6379", service_name="management_server"
)
