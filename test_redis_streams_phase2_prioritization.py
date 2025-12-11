#!/usr/bin/env python3
"""
Test Redis Streams Phase 2: Message Prioritization
Tests the message prioritization system implementation.
"""

import asyncio
import json
import time
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus


class Phase2PrioritizationTester:
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

    async def test_priority_configuration(self):
        """Test priority configuration and stream mapping."""
        try:
            from shared.config.redis_streams import redis_streams_config

            # Test priority streams
            priority_streams = redis_streams_config.get_priority_streams()
            if not priority_streams or "critical" not in priority_streams:
                self.log_result(
                    "Priority Configuration", False, "Priority streams not configured"
                )
                return

            # Test stream priority detection
            test_stream = "mgmt:trading:commands"
            priority = redis_streams_config.get_stream_priority(test_stream)
            if priority != "high":
                self.log_result(
                    "Stream Priority Detection",
                    False,
                    f"Expected 'high', got '{priority}'",
                )
                return

            # Test priority weight
            weight = redis_streams_config.get_priority_weight("critical")
            if weight != 100:
                self.log_result("Priority Weight", False, f"Expected 100, got {weight}")
                return

            self.log_result(
                "Priority Configuration",
                True,
                f"Priority system configured with {len(priority_streams)} levels",
            )

        except Exception as e:
            self.log_result("Priority Configuration", False, f"Exception: {e}")

    async def test_critical_message_publishing(self):
        """Test publishing critical messages to separate streams."""
        try:
            test_stream = "test:priority:critical"

            # Publish critical message
            await mcp_streams_event_bus.publish(
                test_stream,
                {"command": "EMERGENCY_STOP", "bot_id": "test_bot"},
                "EMERGENCY_STOP",
                priority="critical",
            )

            # Check if critical stream was created
            critical_stream = f"{test_stream}:critical"
            stream_info = await mcp_streams_event_bus.redis.xinfo_stream(
                critical_stream
            )

            if stream_info and stream_info.get("length", 0) > 0:
                self.log_result(
                    "Critical Message Publishing",
                    True,
                    f"Critical message published to {critical_stream}",
                )
            else:
                self.log_result(
                    "Critical Message Publishing",
                    False,
                    "Critical stream not created or empty",
                )

        except Exception as e:
            self.log_result("Critical Message Publishing", False, f"Exception: {e}")

    async def test_event_message_priority_field(self):
        """Test that EventMessage includes priority field."""
        try:
            from management_server.tools.redis_streams_event_bus import EventMessage

            # Create message with priority
            event = EventMessage(
                type="TEST_MESSAGE",
                data={"test": "data"},
                source="test_source",
                priority="high",
            )

            if event.priority == "high":
                self.log_result(
                    "Event Message Priority Field",
                    True,
                    "Priority field working correctly",
                )
            else:
                self.log_result(
                    "Event Message Priority Field",
                    False,
                    f"Expected 'high', got '{event.priority}'",
                )

        except Exception as e:
            self.log_result("Event Message Priority Field", False, f"Exception: {e}")

    async def test_priority_stream_listener(self):
        """Test that batch reading handles priority ordering."""
        try:
            test_stream = "test:priority:listener"
            test_group = "test_priority_group"

            # Ensure consumer groups exist for both streams
            await mcp_streams_event_bus.ensure_consumer_group(test_stream, test_group)
            await mcp_streams_event_bus.ensure_consumer_group(
                f"{test_stream}:critical", test_group
            )

            # Publish messages to both regular and critical streams
            await mcp_streams_event_bus.publish(
                test_stream,
                {"message": "regular"},
                "REGULAR_MESSAGE",
                priority="normal",
            )

            await mcp_streams_event_bus.publish(
                test_stream,
                {"message": "critical"},
                "CRITICAL_MESSAGE",
                priority="critical",
            )

            # Read messages using batch read (this should handle priority)
            messages = await mcp_streams_event_bus.read_batch(
                test_stream, test_group, count=10
            )

            # Check if messages were read
            if len(messages) >= 1:  # At least one should be read
                # Check if critical message comes first (if present)
                priorities = [msg[1].get("priority", "normal") for msg in messages]
                critical_first = (
                    priorities[0] == "critical" if "critical" in priorities else True
                )

                if critical_first:
                    self.log_result(
                        "Priority Stream Listener",
                        True,
                        f"Read {len(messages)} messages with proper priority ordering",
                    )
                else:
                    self.log_result(
                        "Priority Stream Listener",
                        False,
                        f"Priority ordering incorrect: {priorities}",
                    )
            else:
                self.log_result(
                    "Priority Stream Listener", False, "No messages were read"
                )

        except Exception as e:
            self.log_result("Priority Stream Listener", False, f"Exception: {e}")

    async def test_priority_weight_calculation(self):
        """Test priority weight calculations for ordering."""
        try:
            from shared.config.redis_streams import redis_streams_config

            weights = {
                "critical": redis_streams_config.get_priority_weight("critical"),
                "high": redis_streams_config.get_priority_weight("high"),
                "normal": redis_streams_config.get_priority_weight("normal"),
                "low": redis_streams_config.get_priority_weight("low"),
            }

            # Verify weight ordering
            if (
                weights["critical"]
                > weights["high"]
                > weights["normal"]
                > weights["low"]
            ):
                self.log_result(
                    "Priority Weight Calculation", True, f"Weights: {weights}"
                )
            else:
                self.log_result(
                    "Priority Weight Calculation",
                    False,
                    f"Invalid weight ordering: {weights}",
                )

        except Exception as e:
            self.log_result("Priority Weight Calculation", False, f"Exception: {e}")

    async def run_all_tests(self):
        """Run all Phase 2 prioritization tests."""
        print("🚀 Starting Phase 2 Tests: Message Prioritization")
        print("=" * 60)

        # Connect to Redis
        await mcp_streams_event_bus.connect()

        try:
            # Run all tests
            await self.test_priority_configuration()
            await self.test_critical_message_publishing()
            await self.test_event_message_priority_field()
            await self.test_priority_stream_listener()
            await self.test_priority_weight_calculation()

            # Print summary
            print("\n" + "=" * 60)
            print("📊 PHASE 2 PRIORITIZATION TEST SUMMARY")
            print("=" * 60)

            passed = sum(1 for r in self.test_results if r["success"])
            total = len(self.test_results)

            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")

            print(f"\nРЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")

            if passed == total:
                print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Message Prioritization готов!")
                print("🏆 Phase 2 Priority System: IMPLEMENTED")
            else:
                print(f"⚠️ {total - passed} тест(ов) провалено. Требуется доработка.")

        finally:
            await mcp_streams_event_bus.disconnect()


async def main():
    tester = Phase2PrioritizationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
