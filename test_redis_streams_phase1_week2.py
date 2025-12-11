#!/usr/bin/env python3
"""
Test Redis Streams Phase 1 Week 2: Consumer Groups, Acknowledgments & Resilience
Tests the enhanced Redis Streams functionality implemented in Week 2.
"""

import asyncio
import json
import time
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus


class Phase1Week2Tester:
    def __init__(self):
        self.test_results = []

    def log_result(self, test_name: str, success: bool, message: str = ""):
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "message": message,
                "timestamp": time.time(),
            }
        )

    async def test_consumer_group_management(self):
        """Test consumer group creation and monitoring."""
        try:
            # Test consumer group creation
            result = await mcp_streams_event_bus.ensure_consumer_group(
                "test:consumer:management", "test_consumers"
            )
            if not result:
                self.log_result(
                    "Consumer Group Creation", False, "Failed to create consumer group"
                )
                return

            # Test consumer group info retrieval
            info = await mcp_streams_event_bus.get_consumer_group_info(
                "test:consumer:management", "test_consumers"
            )
            if not info or info.get("name") != "test_consumers":
                self.log_result(
                    "Consumer Group Info",
                    False,
                    "Failed to retrieve consumer group info",
                )
                return

            # Test lag monitoring
            lag = await mcp_streams_event_bus.get_consumer_lag(
                "test:consumer:management", "test_consumers"
            )
            if lag is None:
                self.log_result(
                    "Consumer Lag Monitoring", False, "Failed to get consumer lag"
                )
                return

            self.log_result(
                "Consumer Group Management", True, f"Created group with lag: {lag}"
            )

        except Exception as e:
            self.log_result("Consumer Group Management", False, f"Exception: {e}")

    async def test_acknowledgment_mechanisms(self):
        """Test message acknowledgment functionality."""
        try:
            test_stream = "test:acknowledgment:stream"
            test_group = "test_ack_consumers"

            # Ensure consumer group exists
            await mcp_streams_event_bus.ensure_consumer_group(test_stream, test_group)

            # Publish a test message
            test_data = {
                "type": "test_ack",
                "data": {"message": "test acknowledgment"},
                "timestamp": time.time(),
            }

            message_id = await mcp_streams_event_bus.redis.xadd(
                test_stream,
                {
                    "type": json.dumps(test_data["type"]),
                    "data": json.dumps(test_data["data"]),
                    "timestamp": json.dumps(test_data["timestamp"]),
                    "source": json.dumps("test_suite"),
                    "version": json.dumps(1),
                },
            )

            # Read the message using consumer group
            messages = await mcp_streams_event_bus.redis.xreadgroup(
                groupname=test_group,
                consumername="test_consumer",
                streams={test_stream: ">"},
                count=1,
            )

            if not messages:
                self.log_result(
                    "Acknowledgment Mechanisms", False, "No messages read from stream"
                )
                return

            # Process and acknowledge the message
            for _, message_list in messages:
                for msg_id, data in message_list:
                    # Acknowledge the message
                    await mcp_streams_event_bus.redis.xack(
                        test_stream, test_group, msg_id
                    )

            # Verify acknowledgment by checking pending messages
            pending = await mcp_streams_event_bus.redis.xpending(
                test_stream, test_group
            )
            pending_count = (
                pending.get("pending", 0) if isinstance(pending, dict) else len(pending)
            )

            if pending_count == 0:
                self.log_result(
                    "Acknowledgment Mechanisms",
                    True,
                    "Message successfully acknowledged",
                )
            else:
                self.log_result(
                    "Acknowledgment Mechanisms",
                    False,
                    f"Message not acknowledged, {pending_count} pending",
                )

        except Exception as e:
            self.log_result("Acknowledgment Mechanisms", False, f"Exception: {e}")

    async def test_connection_resilience(self):
        """Test connection resilience and reconnection."""
        try:
            # Test connection check
            is_connected = await mcp_streams_event_bus._check_redis_connection()
            if not is_connected:
                self.log_result(
                    "Connection Resilience", False, "Redis connection check failed"
                )
                return

            # Test reconnection (should succeed since we're already connected)
            await mcp_streams_event_bus._reconnect_with_backoff()

            # Verify connection is still working
            is_connected_after = await mcp_streams_event_bus._check_redis_connection()
            if is_connected_after:
                self.log_result(
                    "Connection Resilience", True, "Connection resilience working"
                )
            else:
                self.log_result(
                    "Connection Resilience",
                    False,
                    "Connection lost after reconnection test",
                )

        except Exception as e:
            self.log_result("Connection Resilience", False, f"Exception: {e}")

    async def test_stream_health_monitoring(self):
        """Test stream health monitoring functionality."""
        try:
            # Test individual stream health
            health = await mcp_streams_event_bus.get_stream_health_status(
                "mgmt:trading:commands"
            )
            if not health or "status" not in health:
                self.log_result(
                    "Stream Health Monitoring", False, "Failed to get stream health"
                )
                return

            # Test overall system health
            overall_health = await mcp_streams_event_bus.monitor_all_streams_health()
            if not overall_health or "overall_status" not in overall_health:
                self.log_result(
                    "Stream Health Monitoring", False, "Failed to get overall health"
                )
                return

            self.log_result(
                "Stream Health Monitoring",
                True,
                f"System status: {overall_health['overall_status']}, "
                f"Streams: {overall_health['total_streams']}",
            )

        except Exception as e:
            self.log_result("Stream Health Monitoring", False, f"Exception: {e}")

    async def run_all_tests(self):
        """Run all Phase 1 Week 2 tests."""
        print(
            "🚀 Starting Phase 1 Week 2 Tests: Consumer Groups, Acknowledgments & Resilience"
        )
        print("=" * 70)

        # Connect to Redis
        await mcp_streams_event_bus.connect()

        try:
            # Run all tests
            await self.test_consumer_group_management()
            await self.test_acknowledgment_mechanisms()
            await self.test_connection_resilience()
            await self.test_stream_health_monitoring()

            # Print summary
            print("\n" + "=" * 70)
            print("📊 PHASE 1 WEEK 2 TEST SUMMARY")
            print("=" * 70)

            passed = sum(1 for r in self.test_results if r["success"])
            total = len(self.test_results)

            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")

            print(f"\nРЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")

            if passed == total:
                print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Phase 1 Week 2 завершен успешно!")
            else:
                print(f"⚠️ {total - passed} тест(ов) провалено. Требуется доработка.")

        finally:
            await mcp_streams_event_bus.disconnect()


async def main():
    tester = Phase1Week2Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
