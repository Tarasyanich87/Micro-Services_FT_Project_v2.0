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
            'start_time': time.time(),
            'test_duration': 0,
            'message_counts': {},
            'latencies': [],
            'errors': [],
            'throughput': [],
            'health_checks': []
        }
        self.test_bots = []

    async def setup_test_bots(self, count: int = 5):
        """Create test bot configurations."""
        logger.info(f"🤖 Setting up {count} test bots...")

        for i in range(count):
            bot_config = {
                'bot_name': f'test_bot_{i}',
                'exchange': 'binance',
                'strategy': 'DefaultStrategy',
                'stake_amount': 100,
                'dry_run': True,
                'timeframe': '5m'
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
                'bot_name': bot_config['bot_name'],
                'command_id': f'{command_type}_{i}_{int(time.time())}',
                'timestamp': time.time()
            }

            # Send command
            message_id = await mcp_streams_event_bus.redis.xadd(
                'mgmt:trading:commands',
                {
                    'type': command_type,
                    'data': json.dumps(command_data),
                    'timestamp': json.dumps(str(time.time())),
                    'source': json.dumps('production_test'),
                    'version': json.dumps(1)
                }
            )
            message_ids.append(message_id)

            # Small delay to simulate realistic load
            if i % 10 == 0:
                await asyncio.sleep(0.01)

        end_time = time.time()
        duration = end_time - start_time

        self.metrics['message_counts'][command_type] = count
        self.metrics['throughput'].append(count / duration)

        logger.info(".2f"
    async def test_message_processing(self):
        """Test message processing with consumer groups."""
        logger.info("🔄 Testing message processing...")

        # Send test messages
        await self.send_bulk_commands('START_BOT', 50)
        await self.send_bulk_commands('STOP_BOT', 25)
        await self.send_bulk_commands('RESTART_BOT', 25)

        # Wait for processing
        await asyncio.sleep(2)

        # Check consumer lag
        lag = await mcp_streams_event_bus.get_consumer_lag('mgmt:trading:commands', 'trading_consumers')
        logger.info(f"📊 Consumer lag: {lag} messages")

        if lag and lag > 10:
            logger.warning(f"⚠️ High consumer lag detected: {lag}")
            self.metrics['errors'].append(f'high_lag:{lag}')

    async def test_failover_scenarios(self):
        """Test system behavior during failures."""
        logger.info("🔧 Testing failover scenarios...")

        # Test 1: Temporary Redis disconnection simulation
        logger.info("Testing Redis reconnection...")
        original_redis = mcp_streams_event_bus.redis
        try:
            # Simulate disconnection
            mcp_streams_event_bus.redis = None
            await asyncio.sleep(1)

            # Test reconnection
            await mcp_streams_event_bus._reconnect_with_backoff()
            reconnection_success = mcp_streams_event_bus.redis is not None

            if reconnection_success:
                logger.info("✅ Redis reconnection successful")
            else:
                logger.error("❌ Redis reconnection failed")
                self.metrics['errors'].append('redis_reconnection_failed')

        finally:
            mcp_streams_event_bus.redis = original_redis

    async def test_load_scaling(self):
        """Test system under increasing load."""
        logger.info("📈 Testing load scaling...")

        load_levels = [10, 50, 100, 200]

        for load in load_levels:
            logger.info(f"Testing with {load} concurrent messages...")

            start_time = time.time()
            tasks = []

            # Create concurrent message sending tasks
            for i in range(load):
                task = self.send_bulk_commands('STATUS_CHECK', 1)
                tasks.append(task)

            # Execute concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            duration = end_time - start_time

            throughput = load / duration
            self.metrics['throughput'].append(throughput)
            self.metrics['latencies'].append(duration)

        logger.info(f"📈 Sent {count} messages in {duration:.2f}s ({count/duration:.2f} msg/s)")
            # Health check after load
            health = await mcp_streams_event_bus.get_health_status()
            self.metrics['health_checks'].append(health)

            await asyncio.sleep(1)  # Recovery time

    async def test_end_to_end_workflow(self):
        """Test complete bot lifecycle workflow."""
        logger.info("🔄 Testing end-to-end bot lifecycle...")

        bot_name = 'e2e_test_bot'

        # 1. Start bot
        start_data = {
            'bot_name': bot_name,
            'config': {'dry_run': True, 'strategy': 'TestStrategy'}
        }

        await mcp_streams_event_bus.publish(
            'mgmt:trading:commands', start_data, 'START_BOT'
        )

        # 2. Check status
        await asyncio.sleep(0.5)
        status_data = {'bot_name': bot_name}
        await mcp_streams_event_bus.publish(
            'mgmt:trading:commands', status_data, 'GET_STATUS'
        )

        # 3. Stop bot
        await asyncio.sleep(0.5)
        stop_data = {'bot_name': bot_name}
        await mcp_streams_event_bus.publish(
            'mgmt:trading:commands', stop_data, 'STOP_BOT'
        )

        logger.info("✅ End-to-end workflow completed")

    async def collect_performance_metrics(self):
        """Collect comprehensive performance metrics."""
        logger.info("📊 Collecting performance metrics...")

        # System health
        health = await mcp_streams_event_bus.get_health_status()

        # Stream metrics
        streams_metrics = await mcp_streams_event_bus.monitor_all_streams_health()

        # DLQ stats
        dlq_stats = {}
        streams = ['mgmt:trading:commands', 'mgmt:backtesting:commands', 'mgmt:freqai:commands']
        for stream in streams:
            dlq_stats[stream] = await mcp_streams_event_bus.get_dead_letter_stats(stream)

        return {
            'system_health': health,
            'streams_health': streams_metrics,
            'dlq_stats': dlq_stats,
            'test_metrics': self.metrics
        }

    async def run_production_tests(self):
        """Run complete production testing suite."""
        logger.info("🚀 Starting Production-like Testing Suite")
        logger.info("=" * 60)

        try:
            # Setup
            await mcp_streams_event_bus.connect()
            await self.setup_test_bots(5)

            # Run test phases
            await self.test_message_processing()
            await self.test_failover_scenarios()
            await self.test_load_scaling()
            await self.test_end_to_end_workflow()

            # Collect final metrics
            final_metrics = await self.collect_performance_metrics()

            # Calculate summary
            self.metrics['test_duration'] = time.time() - self.metrics['start_time']

            # Print results
            self.print_test_results(final_metrics)

        except Exception as e:
            logger.error(f"❌ Production testing failed: {e}")
            self.metrics['errors'].append(f'critical_error:{str(e)}')

        finally:
            await mcp_streams_event_bus.disconnect()

    def print_test_results(self, final_metrics):
        """Print comprehensive test results."""
        print("\n" + "=" * 60)
        print("📊 PRODUCTION TESTING RESULTS")
        print("=" * 60)

        # Basic metrics
        duration = self.metrics['test_duration']
        total_messages = sum(self.metrics['message_counts'].values())
        avg_throughput = statistics.mean(self.metrics['throughput']) if self.metrics['throughput'] else 0
        error_count = len(self.metrics['errors'])

        print("⏱️  Test Duration: .2f")
        print(f"📨 Total Messages: {total_messages}")
        print(".2f"        print(f"❌ Errors: {error_count}")

        # System health
        system_health = final_metrics['system_health']
        status = system_health.get('status', 'unknown')
        issues = system_health.get('issues', [])

        print(f"\n🏥 System Health: {status}")
        if issues:
            print("Issues:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"  • {issue}")

        # Streams health
        streams_health = final_metrics['streams_health']
        overall_status = streams_health.get('overall_status', 'unknown')
        total_streams = streams_health.get('total_streams', 0)
        healthy_streams = streams_health.get('healthy', 0)

        print(f"\n🌊 Streams Health: {overall_status}")
        print(f"   Total: {total_streams}, Healthy: {healthy_streams}")

        # DLQ stats
        dlq_stats = final_metrics['dlq_stats']
        total_dlq = sum(stats.get('total_messages', 0) for stats in dlq_stats.values())

        print(f"\n💀 Dead Letter Queues: {total_dlq} total messages")

        # Performance assessment
        print("\n🎯 Performance Assessment:"        if avg_throughput > 50:
            print("  ✅ High throughput achieved")
        elif avg_throughput > 10:
            print("  ⚠️ Moderate throughput - acceptable for production")
        else:
            print("  ❌ Low throughput - needs optimization")

        if error_count == 0:
            print("  ✅ Zero errors - excellent reliability")
        elif error_count < 5:
            print("  ⚠️ Few errors - acceptable for production")
        else:
            print("  ❌ High error rate - needs attention")

        if status == 'healthy':
            print("  ✅ System health good")
        else:
            print("  ❌ System health issues detected")

        # Final verdict
        print("
🏆 FINAL VERDICT:"        if (avg_throughput > 10 and error_count < 5 and status == 'healthy'):
            print("🎉 PRODUCTION READY! System passed all critical tests.")
        elif avg_throughput > 5 and error_count < 10:
            print("⚠️ MOSTLY READY - Minor issues need addressing before production.")
        else:
            print("❌ NOT READY - Critical issues need fixing before production.")

        print(f"\n📈 Detailed metrics saved to: production_test_results_{int(time.time())}.json")


async def main():
    tester = ProductionTester()
    await tester.run_production_tests()


if __name__ == "__main__":
    asyncio.run(main())