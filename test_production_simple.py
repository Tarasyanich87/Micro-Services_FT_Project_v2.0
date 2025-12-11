#!/usr/bin/env python3
"""
Production-like Testing Suite for Freqtrade Multi-Bot System
Comprehensive end-to-end testing under production-like conditions.
"""

import asyncio
import json
import time
import statistics
from typing import Dict, List, Any
import logging

from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionTester:
    def __init__(self):
        self.metrics = {
            "start_time": time.time(),
            "test_duration": 0,
            "message_counts": {},
            "latencies": [],
            "errors": [],
            "throughput": [],
            "health_checks": [],
        }
        self.test_bots = []

    async def setup_test_bots(self, count: int = 5):
        """Create test bot configurations."""
        logger.info(f"🤖 Setting up {count} test bots...")

        for i in range(count):
            bot_config = {
                "bot_name": f"test_bot_{i}",
                "exchange": "binance",
                "strategy": "DefaultStrategy",
                "stake_amount": 100,
                "dry_run": True,
                "timeframe": "5m",
            }
            self.test_bots.append(bot_config)

        logger.info(f"✅ Created {len(self.test_bots)} test bot configurations")

    async def send_bulk_commands(self, command_type: str, count: int = 100):
        """Send bulk commands to test throughput."""
        logger.info(f"📤 Sending {count} {command_type} commands...")

        start_time = time.time()
        message_ids = []

        for i in range(count):
            bot_config = self.test_bots[i % len(self.test_bots)]

            command_data = {
                "bot_name": bot_config["bot_name"],
                "command_id": f"{command_type}_{i}_{int(time.time())}",
                "timestamp": time.time(),
            }

            # Send command
            message_id = await mcp_streams_event_bus.redis.xadd(
                "mgmt:trading:commands",
                {
                    "type": command_type,
                    "data": json.dumps(command_data),
                    "timestamp": json.dumps(str(time.time())),
                    "source": json.dumps("production_test"),
                    "version": json.dumps(1),
                },
            )
            message_ids.append(message_id)

            # Small delay to simulate realistic load
            if i % 10 == 0:
                await asyncio.sleep(0.01)

        end_time = time.time()
        duration = end_time - start_time

        self.metrics["message_counts"][command_type] = count
        self.metrics["throughput"].append(count / duration)

        logger.info(
            f"📈 Sent {count} messages in {duration:.2f}s ({count / duration:.2f} msg/s)"
        )

    async def run_simple_test(self):
        """Run a simple production-like test."""
        logger.info("🚀 Starting Simple Production Test")
        logger.info("=" * 50)

        try:
            await mcp_streams_event_bus.connect()
            await self.setup_test_bots(3)

            # Send some test commands
            await self.send_bulk_commands("START_BOT", 10)
            await self.send_bulk_commands("STOP_BOT", 5)

            # Check health
            health = await mcp_streams_event_bus.get_health_status()
            logger.info(f"🏥 System health: {health.get('status', 'unknown')}")

            # Check streams
            streams_health = await mcp_streams_event_bus.monitor_all_streams_health()
            logger.info(
                f"🌊 Streams status: {streams_health.get('overall_status', 'unknown')}"
            )

            self.metrics["test_duration"] = time.time() - self.metrics["start_time"]

            logger.info("✅ Simple production test completed!")
            logger.info(f"⏱️  Duration: {self.metrics['test_duration']:.2f}s")
            logger.info(
                f"📨 Messages sent: {sum(self.metrics['message_counts'].values())}"
            )

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
        finally:
            await mcp_streams_event_bus.disconnect()


async def main():
    tester = ProductionTester()
    await tester.run_simple_test()


if __name__ == "__main__":
    asyncio.run(main())
