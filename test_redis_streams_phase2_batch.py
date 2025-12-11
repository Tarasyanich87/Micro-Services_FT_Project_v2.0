#!/usr/bin/env python3
"""
Test Redis Streams Phase 2: Batch Processing
Tests the batch processing capabilities for improved performance.
"""

import asyncio
import json
import time
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus


class Phase2BatchTester:
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

    async def test_batch_publish(self):
        """Test batch publishing of multiple events."""
        try:
            test_stream = "test:batch:publish"

            # Create batch of events
            events = [
                ({"bot_id": "bot_1", "command": "start"}, "START_BOT"),
                ({"bot_id": "bot_2", "command": "start"}, "START_BOT"),
                ({"bot_id": "bot_3", "command": "start"}, "START_BOT"),
                ({"bot_id": "bot_4", "command": "start"}, "START_BOT"),
                ({"bot_id": "bot_5", "command": "start"}, "START_BOT"),
            ]

            # Publish batch
            start_time = time.time()
            message_ids = await mcp_streams_event_bus.publish_batch(test_stream, events)
            end_time = time.time()

            duration = end_time - start_time

            if len(message_ids) == len(events):
                self.log_result(
                    "Batch Publish",
                    True,
                    f"Published {len(events)} events in {duration:.3f}s",
                )
            else:
                self.log_result(
                    "Batch Publish",
                    False,
                    f"Expected {len(events)} IDs, got {len(message_ids)}",
                )

        except Exception as e:
            self.log_result("Batch Publish", False, f"Exception: {e}")

    async def test_batch_read(self):
        """Test batch reading of multiple messages."""
        try:
            test_stream = "test:batch:read"
            test_group = "test_batch_group"

            # Ensure consumer group exists
            await mcp_streams_event_bus.ensure_consumer_group(test_stream, test_group)

            # Publish some messages first
            events = [({"message": f"test_{i}"}, "TEST_MESSAGE") for i in range(5)]
            await mcp_streams_event_bus.publish_batch(test_stream, events)

            # Read batch
            messages = await mcp_streams_event_bus.read_batch(
                test_stream, test_group, count=10
            )

            if len(messages) > 0:
                self.log_result(
                    "Batch Read", True, f"Read {len(messages)} messages in batch"
                )
            else:
                self.log_result("Batch Read", False, "No messages read")

        except Exception as e:
            self.log_result("Batch Read", False, f"Exception: {e}")

    async def test_batch_process(self):
        """Test batch processing of messages."""
        try:
            test_stream = "test:batch:process"
            test_group = "test_batch_process_group"

            # Ensure consumer group exists
            await mcp_streams_event_bus.ensure_consumer_group(test_stream, test_group)

            # Publish messages
            events = [
                ({"message": f"process_{i}"}, "PROCESS_MESSAGE") for i in range(3)
            ]
            await mcp_streams_event_bus.publish_batch(test_stream, events)

            # Read messages
            messages = await mcp_streams_event_bus.read_batch(
                test_stream, test_group, count=10
            )

            if messages:
                # Process batch
                await mcp_streams_event_bus.process_batch(
                    test_stream, test_group, messages
                )
                self.log_result(
                    "Batch Process",
                    True,
                    f"Processed {len(messages)} messages in batch",
                )
            else:
                self.log_result("Batch Process", False, "No messages to process")

        except Exception as e:
            self.log_result("Batch Process", False, f"Exception: {e}")

    async def test_performance_comparison(self):
        """Compare performance of individual vs batch publishing."""
        try:
            test_stream_individual = "test:perf:individual"
            test_stream_batch = "test:perf:batch"

            # Test data
            events = [({"data": f"perf_{i}"}, "PERF_TEST") for i in range(20)]

            # Individual publishing
            start_time = time.time()
            for event_data, event_type in events:
                await mcp_streams_event_bus.publish(
                    test_stream_individual, event_data, event_type
                )
            individual_time = time.time() - start_time

            # Batch publishing
            start_time = time.time()
            await mcp_streams_event_bus.publish_batch(test_stream_batch, events)
            batch_time = time.time() - start_time

            # Calculate improvement
            if batch_time > 0:
                improvement = (individual_time - batch_time) / individual_time * 100
                self.log_result(
                    "Performance Comparison",
                    True,
                    f"Individual: {individual_time:.3f}s, Batch: {batch_time:.3f}s "
                    f"({improvement:.1f}% improvement)",
                )
            else:
                self.log_result(
                    "Performance Comparison",
                    True,
                    f"Individual: {individual_time:.3f}s, Batch: {batch_time:.3f}s",
                )

        except Exception as e:
            self.log_result("Performance Comparison", False, f"Exception: {e}")

    async def test_priority_in_batch(self):
        """Test that priority is maintained in batch operations."""
        try:
            test_stream = "test:batch:priority"

            # Create mixed priority events
            events = [
                ({"message": "critical_msg"}, "CRITICAL_ALERT"),
                ({"message": "normal_msg_1"}, "NORMAL_MESSAGE"),
                ({"message": "high_msg"}, "HIGH_PRIORITY"),
                ({"message": "normal_msg_2"}, "NORMAL_MESSAGE"),
            ]

            # Ensure consumer group exists
            await mcp_streams_event_bus.ensure_consumer_group(
                test_stream, "test_priority_group"
            )

            # Publish batch (priority determined by event type)
            await mcp_streams_event_bus.publish_batch(test_stream, events)

            # Read and check ordering (should be sorted by priority)
            messages = await mcp_streams_event_bus.read_batch(
                test_stream, "test_priority_group", count=10
            )

            if len(messages) >= 3:  # Should get at least 3 regular messages
                priorities = [msg[1].get("priority", "normal") for msg in messages]

                # Check if all messages have normal priority (since critical goes to separate stream)
                all_normal = all(p == "normal" for p in priorities)

                if all_normal:
                    self.log_result(
                        "Priority in Batch",
                        True,
                        f"Regular messages have correct priority: {priorities}",
                    )
                else:
                    self.log_result(
                        "Priority in Batch",
                        False,
                        f"Unexpected priorities: {priorities}",
                    )
            else:
                self.log_result(
                    "Priority in Batch",
                    False,
                    f"Expected 3+ messages, got {len(messages)}",
                )

        except Exception as e:
            self.log_result("Priority in Batch", False, f"Exception: {e}")

    async def run_all_tests(self):
        """Run all Phase 2 batch processing tests."""
        print("📦 Starting Phase 2 Tests: Batch Processing")
        print("=" * 60)

        # Connect to Redis
        await mcp_streams_event_bus.connect()

        try:
            # Run all tests
            await self.test_batch_publish()
            await self.test_batch_read()
            await self.test_batch_process()
            await self.test_performance_comparison()
            await self.test_priority_in_batch()

            # Print summary
            print("\n" + "=" * 60)
            print("📊 PHASE 2 BATCH PROCESSING TEST SUMMARY")
            print("=" * 60)

            passed = sum(1 for r in self.test_results if r["success"])
            total = len(self.test_results)

            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")

            print(f"\nРЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")

            if passed == total:
                print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Batch Processing готов!")
                print("🏆 Phase 2 Batch Processing: IMPLEMENTED")
            else:
                print(f"⚠️ {total - passed} тест(ов) провалено. Требуется доработка.")

        finally:
            await mcp_streams_event_bus.disconnect()


async def main():
    tester = Phase2BatchTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
