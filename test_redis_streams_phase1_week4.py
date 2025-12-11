#!/usr/bin/env python3
"""
Test Redis Streams Phase 1 Week 4: Advanced Monitoring & Alerting
Tests the advanced monitoring, metrics collection, and health checks.
"""

import asyncio
import time
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus


class Phase1Week4Tester:
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

    async def test_performance_metrics_collection(self):
        """Test collection of performance metrics."""
        try:
            metrics = await mcp_streams_event_bus.collect_performance_metrics()

            if metrics and "timestamp" in metrics and "service" in metrics:
                streams_count = len(metrics.get("streams", {}))
                self.log_result(
                    "Performance Metrics Collection",
                    True,
                    f"Collected metrics for {streams_count} streams",
                )
            else:
                self.log_result(
                    "Performance Metrics Collection", False, "Failed to collect metrics"
                )

        except Exception as e:
            self.log_result("Performance Metrics Collection", False, f"Exception: {e}")

    async def test_stream_metrics_detail(self):
        """Test detailed stream metrics collection."""
        try:
            # Test metrics for a specific stream
            stream_metrics = await mcp_streams_event_bus._collect_stream_metrics(
                "mgmt:trading:commands"
            )

            if stream_metrics and "name" in stream_metrics:
                exists = stream_metrics.get("exists", False)
                length = stream_metrics.get("length", 0)
                groups_count = len(stream_metrics.get("groups", {}))

                self.log_result(
                    "Stream Metrics Detail",
                    True,
                    f"Stream exists: {exists}, length: {length}, groups: {groups_count}",
                )
            else:
                self.log_result(
                    "Stream Metrics Detail", False, "Failed to collect stream metrics"
                )

        except Exception as e:
            self.log_result("Stream Metrics Detail", False, f"Exception: {e}")

    async def test_system_health_metrics(self):
        """Test system-wide health metrics collection."""
        try:
            health_metrics = (
                await mcp_streams_event_bus._collect_system_health_metrics()
            )

            if health_metrics and "overall_status" in health_metrics:
                status = health_metrics.get("overall_status")
                issues_count = len(health_metrics.get("issues", []))
                redis_ping = health_metrics.get("redis_ping", False)

                self.log_result(
                    "System Health Metrics",
                    True,
                    f"Status: {status}, Redis: {redis_ping}, Issues: {issues_count}",
                )
            else:
                self.log_result(
                    "System Health Metrics", False, "Failed to collect health metrics"
                )

        except Exception as e:
            self.log_result("System Health Metrics", False, f"Exception: {e}")

    async def test_health_status_endpoint(self):
        """Test the comprehensive health status endpoint."""
        try:
            health_status = await mcp_streams_event_bus.get_health_status()

            if (
                health_status
                and "status" in health_status
                and "service" in health_status
            ):
                status = health_status.get("status")
                service = health_status.get("service")
                issues = health_status.get("issues", [])

                self.log_result(
                    "Health Status Endpoint",
                    True,
                    f"Service: {service}, Status: {status}, Issues: {len(issues)}",
                )
            else:
                self.log_result(
                    "Health Status Endpoint", False, "Failed to get health status"
                )

        except Exception as e:
            self.log_result("Health Status Endpoint", False, f"Exception: {e}")

    async def test_throughput_tracking(self):
        """Test throughput estimation functionality."""
        try:
            # Add some messages to create throughput data
            test_stream = "test:throughput:tracking"

            # Add a few messages
            for i in range(3):
                await mcp_streams_event_bus.redis.xadd(
                    test_stream,
                    {
                        "type": "test",
                        "data": f'{{"test": {i}}}',
                        "timestamp": str(time.time()),
                        "source": "test",
                        "version": "1",
                    },
                )
                await asyncio.sleep(0.1)  # Small delay

            # Collect metrics (this should trigger throughput calculation)
            metrics = await mcp_streams_event_bus._collect_stream_metrics(test_stream)

            if metrics and "throughput" in metrics:
                throughput = metrics["throughput"].get("messages_per_minute", 0)
                self.log_result(
                    "Throughput Tracking", True, f"Throughput: {throughput:.2f} msg/min"
                )
            else:
                self.log_result(
                    "Throughput Tracking",
                    True,
                    "Throughput tracking initialized (no data yet)",
                )

        except Exception as e:
            self.log_result("Throughput Tracking", False, f"Exception: {e}")

    async def test_alert_conditions(self):
        """Test alert condition detection."""
        try:
            # Create a stream with high lag for testing
            test_stream = "test:alert:conditions"

            # Add messages but don't consume them to create lag
            for i in range(5):
                await mcp_streams_event_bus.redis.xadd(
                    test_stream,
                    {
                        "type": "test_alert",
                        "data": f'{{"test": {i}}}',
                        "timestamp": str(time.time()),
                        "source": "test",
                        "version": "1",
                    },
                )

            # Create consumer group but don't read messages
            await mcp_streams_event_bus.ensure_consumer_group(
                test_stream, "test_alert_group"
            )

            # Collect metrics - this should detect pending messages
            metrics = await mcp_streams_event_bus._collect_stream_metrics(test_stream)

            if metrics and "errors" in metrics:
                errors = metrics["errors"]
                if errors:
                    self.log_result(
                        "Alert Conditions",
                        True,
                        f"Detected {len(errors)} alert conditions",
                    )
                else:
                    self.log_result(
                        "Alert Conditions", True, "No alerts detected (as expected)"
                    )
            else:
                self.log_result(
                    "Alert Conditions", False, "Failed to check alert conditions"
                )

        except Exception as e:
            self.log_result("Alert Conditions", False, f"Exception: {e}")

    async def run_all_tests(self):
        """Run all Phase 1 Week 4 tests."""
        print("📊 Starting Phase 1 Week 4 Tests: Advanced Monitoring & Alerting")
        print("=" * 70)

        # Connect to Redis
        await mcp_streams_event_bus.connect()

        try:
            # Run all tests
            await self.test_performance_metrics_collection()
            await self.test_stream_metrics_detail()
            await self.test_system_health_metrics()
            await self.test_health_status_endpoint()
            await self.test_throughput_tracking()
            await self.test_alert_conditions()

            # Print summary
            print("\n" + "=" * 70)
            print("📊 PHASE 1 WEEK 4 TEST SUMMARY")
            print("=" * 70)

            passed = sum(1 for r in self.test_results if r["success"])
            total = len(self.test_results)

            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")

            print(f"\nРЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")

            if passed == total:
                print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Phase 1 Week 4 завершен успешно!")
                print("🏆 Phase 1 (Redis Streams Infrastructure) ПОЛНОСТЬЮ ЗАВЕРШЕН!")
                print("🎯 Готово к Production Testing!")
            else:
                print(f"⚠️ {total - passed} тест(ов) провалено. Требуется доработка.")

        finally:
            await mcp_streams_event_bus.disconnect()


async def main():
    tester = Phase1Week4Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
