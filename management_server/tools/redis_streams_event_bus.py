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

    async def ensure_consumer_group(self, stream_name: str, consumer_group: str):
        """
        Ensure consumer group exists for the stream.
        Creates it if it doesn't exist, validates if it does.
        """
        if not self.redis:
            logger.error("Cannot ensure consumer group, Redis is not connected.")
            return False

        try:
            # Try to create the consumer group
            await self.redis.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
            logger.info(
                f"📡 Created consumer group '{consumer_group}' for stream '{stream_name}'"
            )
            return True
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists, verify it's valid
                try:
                    info = await self.redis.xinfo_groups(stream_name)
                    group_exists = any(
                        group["name"] == consumer_group for group in info
                    )
                    if group_exists:
                        logger.info(
                            f"✅ Consumer group '{consumer_group}' already exists for stream '{stream_name}'"
                        )
                        return True
                    else:
                        logger.error(
                            f"❌ Consumer group '{consumer_group}' not found in stream info"
                        )
                        return False
                except Exception as info_error:
                    logger.error(f"❌ Error checking consumer group info: {info_error}")
                    return False
            else:
                logger.error(
                    f"❌ Error creating consumer group '{consumer_group}' for {stream_name}: {e}"
                )
                return False

    async def get_consumer_group_info(
        self, stream_name: str, consumer_group: str
    ) -> Optional[Dict]:
        """
        Get detailed information about a consumer group.
        Returns None if group doesn't exist or error occurs.
        """
        if not self.redis:
            return None

        try:
            groups_info = await self.redis.xinfo_groups(stream_name)
            for group in groups_info:
                if group["name"] == consumer_group:
                    return group
            return None
        except Exception as e:
            logger.error(
                f"❌ Error getting consumer group info for {consumer_group}: {e}"
            )
            return None

    async def get_consumer_lag(
        self, stream_name: str, consumer_group: str
    ) -> Optional[int]:
        """
        Get the lag (number of unprocessed messages) for a consumer group.
        """
        group_info = await self.get_consumer_group_info(stream_name, consumer_group)
        if group_info:
            return group_info.get("lag", 0)
        return None

    async def subscribe(
        self, stream_name: str, callback: Callable, consumer_group: Optional[str] = None
    ):
        """Subscribe to a stream and start a background listener task."""
        if not self.redis:
            logger.error("Cannot subscribe, Redis is not connected.")
            return

        self._handlers[stream_name] = callback
        if consumer_group is None:
            consumer_group = self.service_name

        # Ensure consumer group exists
        if not await self.ensure_consumer_group(stream_name, consumer_group):
            logger.error(
                f"❌ Failed to ensure consumer group '{consumer_group}' for {stream_name}"
            )
            return

        # Check lag before starting
        lag = await self.get_consumer_lag(stream_name, consumer_group)
        if lag is not None and lag > 0:
            logger.warning(
                f"⚠️ Consumer group '{consumer_group}' has {lag} pending messages"
            )

        task = asyncio.create_task(self._listen(stream_name, consumer_group))
        self._listener_tasks[stream_name] = task

        # Start retry queue processor for this stream
        retry_task = asyncio.create_task(self._process_retry_queue_loop(stream_name))
        self._listener_tasks[f"{stream_name}:retry_processor"] = retry_task

        logger.info(
            f"🎧 Listening to stream '{stream_name}' with consumer group '{consumer_group}'"
        )

    async def _process_retry_queue_loop(self, stream_name: str):
        """Background loop to process retry queue."""
        while self.redis:
            try:
                await self.process_retry_queue(stream_name)
                await asyncio.sleep(10)  # Process retries every 10 seconds
            except Exception as e:
                logger.error(
                    f"❌ Error in retry queue processor for {stream_name}: {e}"
                )
                await asyncio.sleep(30)  # Wait longer on error

    async def _read_pending_messages(self, stream_name: str, group_name: str):
        """Read any pending messages for this consumer group."""
        if not self.redis:
            logger.error("Redis not connected, cannot read pending messages")
            return

        try:
            consumer_name = f"{self.service_name}_{id(self)}"

            # Read pending messages using XREADGROUP with '0' to get pending messages
            messages = await self.redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: "0"},  # '0' means read pending messages
                count=10,  # Process up to 10 pending messages at a time
                block=1000,  # Don't block for too long
            )

            if messages:
                logger.info(f"Found {len(messages)} streams with pending messages")

                for stream, message_list in messages:
                    logger.info(
                        f"Processing {len(message_list)} pending messages from {stream}"
                    )
                    for message_id, data in message_list:
                        try:
                            logger.debug(f"Raw pending message {message_id}: {data}")
                            deserialized_data = {
                                k: json.loads(v) for k, v in data.items()
                            }
                            event = EventMessage(**deserialized_data)
                            logger.info(f"🔥 Processing pending event: {event.type}")

                            await self._handlers[stream_name](event)
                            await self.redis.xack(stream_name, group_name, message_id)
                            logger.info(
                                f"✅ Processed and acknowledged pending message {message_id}"
                            )

                        except Exception as e:
                            logger.exception(
                                f"❌ Error processing pending message {message_id}"
                            )
                            # TODO: Implement dead letter queue for failed messages

        except Exception as e:
            logger.exception(f"Error reading pending messages for {stream_name}")

    async def _listen(self, stream_name: str, group_name: str):
        """The core listening loop for a consumer group with enhanced error handling."""
        consumer_name = f"{self.service_name}_{id(self)}"
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.redis:
            try:
                # Check connection health before reading
                if not await self._check_redis_connection():
                    logger.warning(f"Redis connection lost, attempting reconnection...")
                    await self._reconnect_with_backoff()
                    continue

                messages = await self.redis.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={stream_name: ">"},
                    count=1,
                    block=5000,  # Block for 5 seconds to allow graceful shutdown
                )

                if messages:
                    consecutive_errors = 0  # Reset error counter on successful read

                    for _, message_list in messages:
                        for message_id, data in message_list:
                            await self._process_message_with_ack(
                                stream_name, group_name, message_id, data
                            )

                # Check consumer lag periodically
                if hasattr(self, "_lag_check_counter"):
                    self._lag_check_counter += 1
                else:
                    self._lag_check_counter = 0

                if self._lag_check_counter % 10 == 0:  # Check every 10 iterations
                    lag = await self.get_consumer_lag(stream_name, group_name)
                    if lag and lag > 100:
                        logger.warning(
                            f"⚠️ High consumer lag detected: {lag} messages pending"
                        )

            except redis.RedisError as e:
                consecutive_errors += 1
                logger.error(
                    f"Redis error while listening to {stream_name} (error {consecutive_errors}/{max_consecutive_errors}): {e}"
                )

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(
                        f"Too many consecutive Redis errors, attempting reconnection..."
                    )
                    await self._reconnect_with_backoff()
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(
                        min(5 * consecutive_errors, 30)
                    )  # Exponential backoff

            except asyncio.CancelledError:
                logger.info(f"Listener for {stream_name} cancelled")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.exception(
                    f"Unexpected error in listener for {stream_name} (error {consecutive_errors}/{max_consecutive_errors})"
                )

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(
                        "Too many consecutive unexpected errors, shutting down listener"
                    )
                    break
                else:
                    await asyncio.sleep(5)

    async def _process_message_with_ack(
        self, stream_name: str, group_name: str, message_id: str, data: Dict
    ):
        """Process a message with proper acknowledgment and error handling."""
        try:
            # Deserialize data from JSON strings
            deserialized_data = {k: json.loads(v) for k, v in data.items()}
            event = EventMessage(**deserialized_data)

            # Pass the event object to the handler
            await self._handlers[stream_name](event)

            # Acknowledge successful processing
            await self.redis.xack(stream_name, group_name, message_id)
            logger.debug(f"✅ Acknowledged message {message_id}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error for message {message_id}: {e}")
            # Move to dead letter queue or mark as processed to avoid infinite retries
            await self._handle_failed_message(
                stream_name, group_name, message_id, data, "json_decode_error"
            )

        except Exception as e:
            logger.exception(
                f"❌ Error processing message {message_id} from {stream_name}"
            )
            # Implement retry logic or dead letter queue
            await self._handle_failed_message(
                stream_name, group_name, message_id, data, str(e)
            )

    async def _handle_failed_message(
        self, stream_name: str, group_name: str, message_id: str, data: Dict, error: str
    ):
        """Handle messages that failed processing with dead letter queue."""
        try:
            # Check if this is a poison message (failed multiple times)
            retry_count = int(data.get("retry_count", "0"))
            max_retries = int(data.get("max_retries", "3"))

            if retry_count < max_retries:
                # Retry with exponential backoff
                await self._schedule_retry(
                    stream_name, group_name, message_id, data, error, retry_count
                )
            else:
                # Move to dead letter queue
                await self._move_to_dead_letter_queue(
                    stream_name, group_name, message_id, data, error
                )

        except Exception as handle_error:
            logger.error(
                f"❌ Error handling failed message {message_id}: {handle_error}"
            )
            # Last resort: acknowledge to prevent infinite loop
            try:
                await self.redis.xack(stream_name, group_name, message_id)
            except Exception as ack_error:
                logger.critical(
                    f"❌ CRITICAL: Could not acknowledge failed message {message_id}: {ack_error}"
                )

    async def _schedule_retry(
        self,
        stream_name: str,
        group_name: str,
        message_id: str,
        data: Dict,
        error: str,
        retry_count: int,
    ):
        """Schedule a message for retry with exponential backoff."""
        try:
            # Calculate delay: exponential backoff (1s, 4s, 16s, etc.)
            delay_seconds = 1 * (4**retry_count)
            retry_at = time.time() + delay_seconds

            # Create retry message
            retry_data = data.copy()
            retry_data.update(
                {
                    "retry_count": str(retry_count + 1),
                    "last_error": error,
                    "retry_at": str(retry_at),
                    "original_message_id": message_id,
                    "scheduled_retry": "true",
                }
            )

            # Add to retry stream
            retry_stream = f"{stream_name}:retry"
            await self.redis.xadd(
                retry_stream,
                {
                    "type": json.dumps(retry_data.get("type", "retry")),
                    "data": json.dumps(retry_data),
                    "timestamp": json.dumps(str(time.time())),
                    "source": json.dumps(self.service_name),
                    "version": json.dumps(1),
                },
            )

            # Acknowledge original message
            await self.redis.xack(stream_name, group_name, message_id)

            logger.info(
                f"🔄 Scheduled retry for message {message_id} in {delay_seconds}s (attempt {retry_count + 1})"
            )

        except Exception as retry_error:
            logger.error(
                f"❌ Failed to schedule retry for message {message_id}: {retry_error}"
            )
            # Move to DLQ as fallback
            await self._move_to_dead_letter_queue(
                stream_name, group_name, message_id, data, f"retry_failed: {error}"
            )

    async def _move_to_dead_letter_queue(
        self, stream_name: str, group_name: str, message_id: str, data: Dict, error: str
    ):
        """Move failed message to dead letter queue."""
        try:
            # Create dead letter queue name
            dlq_stream = f"{stream_name}:dead"

            # Prepare DLQ message
            dlq_data = data.copy()
            dlq_data.update(
                {
                    "dead_letter_reason": error,
                    "failed_at": str(time.time()),
                    "original_stream": stream_name,
                    "original_message_id": message_id,
                    "service_name": self.service_name,
                    "final_retry_count": dlq_data.get("retry_count", "0"),
                }
            )

            # Add to dead letter queue
            dlq_id = await self.redis.xadd(
                dlq_stream,
                {
                    "type": json.dumps("dead_letter"),
                    "data": json.dumps(dlq_data),
                    "timestamp": json.dumps(str(time.time())),
                    "source": json.dumps(self.service_name),
                    "version": json.dumps(1),
                },
            )

            # Acknowledge original message
            await self.redis.xack(stream_name, group_name, message_id)

            logger.warning(
                f"💀 Moved message {message_id} to dead letter queue {dlq_stream} (ID: {dlq_id}) - Reason: {error}"
            )

        except Exception as dlq_error:
            logger.error(f"❌ Failed to move message {message_id} to DLQ: {dlq_error}")
            # Last resort acknowledgment
            try:
                await self.redis.xack(stream_name, group_name, message_id)
                logger.warning(
                    f"⚠️ Emergency acknowledgment of failed message {message_id}"
                )
            except Exception as emergency_error:
                logger.critical(
                    f"❌ CRITICAL: Could not emergency acknowledge message {message_id}: {emergency_error}"
                )

    async def process_retry_queue(self, stream_name: str):
        """Process retry queue for a stream, moving ready messages back to main stream."""
        try:
            retry_stream = f"{stream_name}:retry"
            current_time = time.time()

            # Read retry messages that are ready
            messages = await self.redis.xread({retry_stream: "0"}, count=10)

            for stream, message_list in messages:
                for message_id, data in message_list:
                    try:
                        # Parse retry data
                        retry_data = json.loads(data.get(b"data", b"{}").decode())

                        retry_at = float(retry_data.get("retry_at", 0))

                        if current_time >= retry_at:
                            # Time to retry - move back to main stream
                            original_data = retry_data.copy()
                            # Remove retry-specific fields
                            for key in [
                                "retry_count",
                                "last_error",
                                "retry_at",
                                "original_message_id",
                                "scheduled_retry",
                            ]:
                                original_data.pop(key, None)

                            # Add back to main stream
                            new_message_id = await self.redis.xadd(
                                stream_name,
                                {
                                    "type": json.dumps(
                                        original_data.get("type", "retry")
                                    ),
                                    "data": json.dumps(original_data),
                                    "timestamp": json.dumps(str(time.time())),
                                    "source": json.dumps(self.service_name),
                                    "version": json.dumps(1),
                                },
                            )

                            # Remove from retry queue
                            await self.redis.xdel(retry_stream, message_id)

                            logger.info(
                                f"🔄 Retried message {message_id} → {new_message_id} in {stream_name}"
                            )

                    except Exception as process_error:
                        logger.error(
                            f"❌ Error processing retry message {message_id}: {process_error}"
                        )

        except Exception as retry_error:
            logger.error(
                f"❌ Error processing retry queue for {stream_name}: {retry_error}"
            )

    async def get_dead_letter_stats(self, stream_name: str) -> Dict[str, Any]:
        """Get statistics for dead letter queue."""
        try:
            dlq_stream = f"{stream_name}:dead"

            # Get stream info
            info = await self.redis.xinfo_stream(dlq_stream)
            length = info.get("length", 0)

            # Get recent messages for analysis
            recent_messages = await self.redis.xrevrange(dlq_stream, "+", "-", count=10)

            error_types = {}
            for msg_id, data in recent_messages:
                try:
                    msg_data = json.loads(data.get(b"data", b"{}").decode())
                    error = msg_data.get("dead_letter_reason", "unknown")
                    error_types[error] = error_types.get(error, 0) + 1
                except:
                    error_types["parse_error"] = error_types.get("parse_error", 0) + 1

            return {
                "stream": dlq_stream,
                "total_messages": length,
                "error_types": error_types,
                "last_updated": time.time(),
            }

        except redis.ResponseError:
            # DLQ doesn't exist yet
            return {
                "stream": f"{stream_name}:dead",
                "total_messages": 0,
                "error_types": {},
                "last_updated": time.time(),
            }
        except Exception as e:
            logger.error(f"❌ Error getting DLQ stats for {stream_name}: {e}")
            return {
                "stream": f"{stream_name}:dead",
                "error": str(e),
                "last_updated": time.time(),
            }

    async def collect_performance_metrics(self) -> Dict[str, Any]:
        """
        Collect comprehensive performance metrics for monitoring.
        """
        metrics = {
            "timestamp": time.time(),
            "service": self.service_name,
            "redis_connected": self.redis is not None,
            "active_listeners": len(self._listener_tasks),
            "streams": {},
            "system_health": {},
        }

        if not self.redis:
            return metrics

        try:
            # Collect metrics for all configured streams
            from shared.config.redis_streams import redis_streams_config

            all_streams = redis_streams_config.get_all_streams()

            for stream_name in all_streams:
                try:
                    stream_metrics = await self._collect_stream_metrics(stream_name)
                    metrics["streams"][stream_name] = stream_metrics
                except Exception as e:
                    logger.error(f"Error collecting metrics for {stream_name}: {e}")
                    metrics["streams"][stream_name] = {"error": str(e)}

            # System-wide health metrics
            metrics["system_health"] = await self._collect_system_health_metrics()

        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            metrics["error"] = str(e)

        return metrics

    async def _collect_stream_metrics(self, stream_name: str) -> Dict[str, Any]:
        """Collect detailed metrics for a specific stream."""
        metrics = {
            "name": stream_name,
            "exists": False,
            "length": 0,
            "groups": {},
            "lag": {},
            "throughput": {},
            "errors": {},
        }

        try:
            # Stream info
            stream_info = await self.redis.xinfo_stream(stream_name)
            metrics["exists"] = True
            metrics["length"] = stream_info.get("length", 0)
            metrics["first_entry_id"] = (
                stream_info.get("first-entry", [b"0-0"])[0].decode()
                if stream_info.get("first-entry")
                else None
            )
            metrics["last_entry_id"] = (
                stream_info.get("last-entry", [b"0-0"])[0].decode()
                if stream_info.get("last-entry")
                else None
            )

            # Consumer group info
            try:
                groups_info = await self.redis.xinfo_groups(stream_name)
                for group in groups_info:
                    group_name = group["name"]
                    metrics["groups"][group_name] = {
                        "consumers": group.get("consumers", 0),
                        "pending": group.get("pending", 0),
                        "last_delivered_id": group.get("last-delivered-id", "0-0"),
                        "lag": group.get("lag", 0),
                    }

                    # Lag metrics
                    lag = group.get("lag", 0)
                    metrics["lag"][group_name] = lag

                    # Alert thresholds
                    if lag > 100:
                        metrics["errors"][f"{group_name}_high_lag"] = (
                            f"Lag: {lag} messages"
                        )
                    if group.get("pending", 0) > 50:
                        metrics["errors"][f"{group_name}_high_pending"] = (
                            f"Pending: {group.get('pending', 0)} messages"
                        )

            except redis.ResponseError:
                # No consumer groups
                pass

            # DLQ stats
            dlq_stats = await self.get_dead_letter_stats(stream_name)
            metrics["dlq"] = dlq_stats

            # Throughput estimation (messages per minute, rough estimate)
            # This is a simple implementation - in production you'd want more sophisticated tracking
            current_time = time.time()
            if hasattr(self, "_throughput_tracking"):
                self._throughput_tracking[stream_name] = self._throughput_tracking.get(
                    stream_name, []
                )
                self._throughput_tracking[stream_name].append(
                    (current_time, metrics["length"])
                )

                # Keep only last 10 minutes of data
                self._throughput_tracking[stream_name] = [
                    (t, l)
                    for t, l in self._throughput_tracking[stream_name]
                    if current_time - t < 600
                ]

                if len(self._throughput_tracking[stream_name]) > 1:
                    oldest_time, oldest_length = self._throughput_tracking[stream_name][
                        0
                    ]
                    time_diff = current_time - oldest_time
                    length_diff = metrics["length"] - oldest_length
                    if time_diff > 0:
                        metrics["throughput"]["messages_per_minute"] = (
                            length_diff / time_diff
                        ) * 60
            else:
                self._throughput_tracking = {}
                self._throughput_tracking[stream_name] = [
                    (current_time, metrics["length"])
                ]

        except redis.ResponseError:
            # Stream doesn't exist
            metrics["exists"] = False
        except Exception as e:
            logger.error(f"Error collecting stream metrics for {stream_name}: {e}")
            metrics["errors"]["collection_error"] = str(e)

        return metrics

    async def _collect_system_health_metrics(self) -> Dict[str, Any]:
        """Collect system-wide health metrics."""
        health = {
            "overall_status": "healthy",
            "issues": [],
            "redis_ping": False,
            "total_streams": 0,
            "total_groups": 0,
            "total_lag": 0,
            "total_dlq_messages": 0,
        }

        try:
            # Redis connectivity
            await self.redis.ping()
            health["redis_ping"] = True

            # Aggregate metrics from all streams
            if "streams" in self._latest_metrics:
                streams_data = self._latest_metrics["streams"]
                health["total_streams"] = len(streams_data)

                for stream_name, stream_metrics in streams_data.items():
                    if stream_metrics.get("exists", False):
                        # Count consumer groups
                        health["total_groups"] += len(stream_metrics.get("groups", {}))

                        # Sum lag
                        for group_lag in stream_metrics.get("lag", {}).values():
                            health["total_lag"] += group_lag

                        # Count DLQ messages
                        dlq = stream_metrics.get("dlq", {})
                        health["total_dlq_messages"] += dlq.get("total_messages", 0)

                        # Check for errors
                        if stream_metrics.get("errors"):
                            health["issues"].extend(
                                [
                                    f"{stream_name}:{error_type}"
                                    for error_type in stream_metrics["errors"].keys()
                                ]
                            )

            # Determine overall status
            if health["total_dlq_messages"] > 10:
                health["overall_status"] = "warning"
                health["issues"].append(
                    f"high_dlq_count:{health['total_dlq_messages']}"
                )

            if health["total_lag"] > 500:
                health["overall_status"] = "warning"
                health["issues"].append(f"high_total_lag:{health['total_lag']}")

            if not health["redis_ping"]:
                health["overall_status"] = "error"
                health["issues"].append("redis_disconnected")

            if len(health["issues"]) > 5:
                health["overall_status"] = "error"

        except Exception as e:
            logger.error(f"Error collecting system health metrics: {e}")
            health["overall_status"] = "error"
            health["issues"].append(f"collection_error:{str(e)}")

        return health

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status for monitoring and alerting.
        """
        try:
            # Collect fresh metrics
            self._latest_metrics = await self.collect_performance_metrics()

            health_status = {
                "service": self.service_name,
                "timestamp": time.time(),
                "status": self._latest_metrics.get("system_health", {}).get(
                    "overall_status", "unknown"
                ),
                "redis_connected": self._latest_metrics.get("redis_connected", False),
                "active_listeners": self._latest_metrics.get("active_listeners", 0),
                "issues": self._latest_metrics.get("system_health", {}).get(
                    "issues", []
                ),
                "metrics": self._latest_metrics,
            }

            return health_status

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "service": self.service_name,
                "timestamp": time.time(),
                "status": "error",
                "error": str(e),
            }

    async def _check_redis_connection(self) -> bool:
        """Check if Redis connection is healthy."""
        if not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False

    async def _reconnect_with_backoff(self):
        """Attempt to reconnect to Redis with exponential backoff."""
        max_attempts = 5
        base_delay = 1

        for attempt in range(max_attempts):
            try:
                logger.info(
                    f"Attempting Redis reconnection (attempt {attempt + 1}/{max_attempts})"
                )
                await self.connect()
                if self.redis:
                    logger.info("✅ Redis reconnection successful")
                    return
            except Exception as e:
                logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")

            if attempt < max_attempts - 1:
                delay = base_delay * (2**attempt)  # Exponential backoff
                logger.info(f"Waiting {delay} seconds before next reconnection attempt")
                await asyncio.sleep(delay)

        logger.error("❌ Failed to reconnect to Redis after all attempts")

    async def get_stream_health_status(self, stream_name: str) -> Dict[str, Any]:
        """
        Get comprehensive health status for a stream and its consumer groups.
        """
        if not self.redis:
            return {"status": "disconnected", "stream": stream_name}

        try:
            # Get stream info
            stream_info = await self.redis.xinfo_stream(stream_name)
            length = stream_info.get("length", 0)
            groups_count = stream_info.get("groups", 0)

            # Get consumer groups info
            groups_info = []
            total_lag = 0
            total_pending = 0

            if groups_count > 0:
                try:
                    groups = await self.redis.xinfo_groups(stream_name)
                    for group in groups:
                        lag = group.get("lag", 0)
                        pending = group.get("pending", 0)
                        total_lag += lag
                        total_pending += pending

                        groups_info.append(
                            {
                                "name": group.get("name"),
                                "consumers": group.get("consumers", 0),
                                "pending": pending,
                                "lag": lag,
                                "last_delivered_id": group.get("last-delivered-id"),
                            }
                        )
                except Exception as e:
                    logger.error(f"Error getting groups info for {stream_name}: {e}")

            # Determine health status
            status = "healthy"
            issues = []

            if length > 10000:  # High message count
                status = "warning"
                issues.append(f"high_message_count:{length}")

            if total_lag > 100:  # High lag
                status = "warning"
                issues.append(f"high_lag:{total_lag}")

            if total_pending > 50:  # High pending messages
                status = "warning"
                issues.append(f"high_pending:{total_pending}")

            if groups_count == 0:
                status = "warning"
                issues.append("no_consumer_groups")

            return {
                "status": status,
                "stream": stream_name,
                "length": length,
                "groups_count": groups_count,
                "total_lag": total_lag,
                "total_pending": total_pending,
                "groups": groups_info,
                "issues": issues,
                "timestamp": time.time(),
            }

        except redis.ResponseError as e:
            if "no such key" in str(e):
                return {
                    "status": "not_found",
                    "stream": stream_name,
                    "message": "Stream does not exist",
                    "timestamp": time.time(),
                }
            else:
                return {
                    "status": "error",
                    "stream": stream_name,
                    "error": str(e),
                    "timestamp": time.time(),
                }
        except Exception as e:
            return {
                "status": "error",
                "stream": stream_name,
                "error": str(e),
                "timestamp": time.time(),
            }

    async def monitor_all_streams_health(self) -> Dict[str, Any]:
        """
        Monitor health of all configured streams.
        """
        from shared.config.redis_streams import redis_streams_config

        all_streams = redis_streams_config.get_all_streams()
        results = {}

        for stream_name in all_streams:
            results[stream_name] = await self.get_stream_health_status(stream_name)

        # Calculate overall system health
        healthy_count = sum(
            1 for status in results.values() if status["status"] == "healthy"
        )
        warning_count = sum(
            1 for status in results.values() if status["status"] == "warning"
        )
        error_count = sum(
            1
            for status in results.values()
            if status["status"] in ["error", "not_found"]
        )

        overall_status = "healthy"
        if error_count > 0:
            overall_status = "error"
        elif warning_count > 0:
            overall_status = "warning"

        return {
            "overall_status": overall_status,
            "total_streams": len(all_streams),
            "healthy": healthy_count,
            "warning": warning_count,
            "error": error_count,
            "streams": results,
            "timestamp": time.time(),
        }


# --- Pre-configured instances ---
# These can be configured with URLs from environment settings.
# For simplicity, we define them here.
core_streams_event_bus = RedisStreamsEventBus(
    redis_url="redis://localhost:6379", service_name="management_server"
)
mcp_streams_event_bus = RedisStreamsEventBus(
    redis_url="redis://localhost:6379", service_name="management_server"
)
