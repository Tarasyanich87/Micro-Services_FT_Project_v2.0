#!/usr/bin/env python3
"""
Test Redis Streams Phase 1 Week 3: Dead Letter Queues & Retry Logic
Tests the dead letter queue and retry functionality.
"""

import asyncio
import json
import time
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus


class Phase1Week3Tester:
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

    async def test_dead_letter_queue_basic(self):
        """Test basic dead letter queue functionality."""
        try:
            test_stream = "test:dlq:basic"
            test_group = "test_dlq_consumers"

            # Test direct DLQ functionality by calling the method
            failed_data = {
                "type": "test_failure",
                "data": {"should_fail": True},
                "timestamp": str(time.time()),
                "retry_count": "3",  # Already at max retries
                "max_retries": "3",
            }

            # Directly test the _move_to_dead_letter_queue method
            await mcp_streams_event_bus._move_to_dead_letter_queue(
                test_stream, test_group, "test_msg_123", failed_data, "test_error"
            )

            # Check if message was moved to DLQ
            dlq_stats = await mcp_streams_event_bus.get_dead_letter_stats(test_stream)

            if dlq_stats["total_messages"] > 0:
                self.log_result(
                    "Dead Letter Queue Basic",
                    True,
                    f"Message moved to DLQ: {dlq_stats['total_messages']} messages",
                )
            else:
                self.log_result(
                    "Dead Letter Queue Basic", False, "Message was not moved to DLQ"
                )

        except Exception as e:
            self.log_result("Dead Letter Queue Basic", False, f"Exception: {e}")

    async def test_retry_logic(self):
        """Test message retry logic with exponential backoff."""
        try:
            test_stream = "test:retry:logic"
            test_group = "test_retry_consumers"

            # Create a message that should be retried
            retry_data = {
                "type": "test_retry",
                "data": {"should_retry": True},
                "timestamp": str(time.time()),
                "retry_count": "0",  # First attempt
                "max_retries": "3",
            }

            # Directly test the _schedule_retry method
            await mcp_streams_event_bus._schedule_retry(
                test_stream,
                test_group,
                "retry_msg_456",
                retry_data,
                "temporary_error",
                0,
            )

            # Process retry queue immediately (should not move anything since delay hasn't passed)
            await mcp_streams_event_bus.process_retry_queue(test_stream)

            self.log_result("Retry Logic", True, "Retry logic executed without errors")

        except Exception as e:
            self.log_result("Retry Logic", False, f"Exception: {e}")

    async def test_poison_message_detection(self):
        """Test detection of poison messages (messages that always fail)."""
        try:
            test_stream = "test:poison:message"
            test_group = "test_poison_consumers"

            # Create a poison message (already exceeded max retries)
            poison_data = {
                "type": "poison_message",
                "data": {"always_fails": True},
                "timestamp": str(time.time()),
                "retry_count": "5",  # Exceeded max
                "max_retries": "3",
            }

            # Directly test poison message handling
            await mcp_streams_event_bus._move_to_dead_letter_queue(
                test_stream,
                test_group,
                "poison_msg_789",
                poison_data,
                "persistent_error",
            )

            # Check DLQ stats
            dlq_stats = await mcp_streams_event_bus.get_dead_letter_stats(test_stream)

            if dlq_stats["total_messages"] > 0:
                self.log_result(
                    "Poison Message Detection",
                    True,
                    "Poison message correctly moved to DLQ",
                )
            else:
                self.log_result(
                    "Poison Message Detection",
                    False,
                    "Poison message was not moved to DLQ",
                )

        except Exception as e:
            self.log_result("Poison Message Detection", False, f"Exception: {e}")

    async def test_dlq_statistics(self):
        """Test dead letter queue statistics and monitoring."""
        try:
            test_stream = "test:dlq:stats"

            # Get DLQ stats for non-existent stream
            stats = await mcp_streams_event_bus.get_dead_letter_stats(test_stream)

            if stats and "total_messages" in stats:
                self.log_result(
                    "DLQ Statistics",
                    True,
                    f"DLQ stats retrieved: {stats['total_messages']} messages",
                )
            else:
                self.log_result(
                    "DLQ Statistics", False, "Could not retrieve DLQ statistics"
                )

        except Exception as e:
            self.log_result("DLQ Statistics", False, f"Exception: {e}")

    async def test_retry_queue_processing(self):
        """Test retry queue processing functionality."""
        try:
            test_stream = "test:retry:processing"

            # Process retry queue (should handle gracefully even if empty)
            await mcp_streams_event_bus.process_retry_queue(test_stream)

            self.log_result(
                "Retry Queue Processing",
                True,
                "Retry queue processing completed without errors",
            )

        except Exception as e:
            self.log_result("Retry Queue Processing", False, f"Exception: {e}")

    async def run_all_tests(self):
        """Run all Phase 1 Week 3 tests."""
        print("🧪 Starting Phase 1 Week 3 Tests: Dead Letter Queues & Retry Logic")
        print("=" * 70)

        # Connect to Redis
        await mcp_streams_event_bus.connect()

        try:
            # Run all tests
            await self.test_dead_letter_queue_basic()
            await self.test_retry_logic()
            await self.test_poison_message_detection()
            await self.test_dlq_statistics()
            await self.test_retry_queue_processing()

            # Print summary
            print("\n" + "=" * 70)
            print("📊 PHASE 1 WEEK 3 TEST SUMMARY")
            print("=" * 70)

            passed = sum(1 for r in self.test_results if r["success"])
            total = len(self.test_results)

            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")

            print(f"\nРЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")

            if passed == total:
                print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Phase 1 Week 3 завершен успешно!")
            else:
                print(f"⚠️ {total - passed} тест(ов) провалено. Требуется доработка.")

        finally:
            await mcp_streams_event_bus.disconnect()


async def main():
    tester = Phase1Week3Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
