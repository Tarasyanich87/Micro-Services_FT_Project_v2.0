#!/usr/bin/env python3
"""
Bulk Bot Operations Test for Freqtrade Multi-Bot System
Tests concurrent creation, starting, and stopping of multiple bots
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from httpx import AsyncClient, ASGITransport
import statistics


@dataclass
class BulkTestResult:
    operation: str
    bots_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    success_count: int
    failure_count: int
    errors: List[str]


class BulkBotOperationsTester:
    def __init__(
        self, base_url: str = "http://localhost:8002", max_concurrent: int = 10
    ):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.client: AsyncClient | None = None
        self.token: str | None = None
        self.created_bots: List[int] = []
        self.test_results: List[BulkTestResult] = []

    async def __aenter__(self):
        self.client = AsyncClient(base_url=self.base_url, timeout=60.0)
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        if self.client:
            await self.client.aclose()

    async def authenticate(self):
        """Authenticate and get JWT token"""
        if not self.client:
            print("❌ Client not initialized")
            return

        try:
            # First try to register user (may already exist)
            register_data = {
                "username": "test_user_bulk",
                "email": "test_bulk@example.com",
                "password": "testpass123",
                "full_name": "Test User Bulk",
            }
            register_response = await self.client.post(
                "/api/v1/auth/register", json=register_data
            )
            print(f"Register response: {register_response.status_code}")

            # Then login
            auth_data = {"username": "test_user_bulk", "password": "testpass123"}
            response = await self.client.post("/api/v1/auth/login/json", json=auth_data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Authentication successful")
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Authentication error: {e}")

    async def create_bot_batch(self, count: int) -> BulkTestResult:
        """Create multiple bots concurrently"""
        print(f"🤖 Creating {count} bots concurrently...")

        start_time = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def create_single_bot(bot_num: int):
            async with semaphore:
                bot_data = {
                    "name": f"BulkBot_{bot_num}_{int(time.time())}",
                    "strategy_name": "TestStrategy",
                    "exchange": "binance",
                    "stake_currency": "USDT",
                    "stake_amount": 100.0,
                }

                try:
                    response = await self.client.post("/api/v1/bots/", json=bot_data)
                    if response.status_code == 201:
                        bot_id = response.json()["id"]
                        return bot_id, None
                    else:
                        error = f"HTTP {response.status_code}: {response.text}"
                        return None, error
                except Exception as e:
                    return None, str(e)

        tasks = [create_single_bot(i) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time
        successful_creations = []
        errors = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result[0] is not None:
                successful_creations.append(result[0])
            else:
                errors.append(result[1])

        self.created_bots.extend(successful_creations)

        result = BulkTestResult(
            operation="create_bots",
            bots_count=count,
            total_time=total_time,
            avg_time=total_time / count if count > 0 else 0,
            min_time=0,  # Would need individual timing
            max_time=0,  # Would need individual timing
            success_count=len(successful_creations),
            failure_count=len(errors),
            errors=errors[:5],  # Limit error messages
        )

        print(
            f"✅ Created {len(successful_creations)}/{count} bots in {total_time:.2f}s"
        )
        if errors:
            print(f"❌ {len(errors)} failures: {errors[0]}")

        return result

    async def start_bots_batch(self, bot_ids: List[int]) -> BulkTestResult:
        """Start multiple bots concurrently"""
        print(f"🚀 Starting {len(bot_ids)} bots concurrently...")

        start_time = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def start_single_bot(bot_id: int):
            async with semaphore:
                try:
                    response = await self.client.post(f"/api/v1/bots/{bot_id}/start")
                    if response.status_code == 200:
                        return True, None
                    else:
                        error = f"HTTP {response.status_code}: {response.text}"
                        return False, error
                except Exception as e:
                    return False, str(e)

        tasks = [start_single_bot(bot_id) for bot_id in bot_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time
        success_count = 0
        errors = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result[0]:
                success_count += 1
            else:
                errors.append(result[1])

        result = BulkTestResult(
            operation="start_bots",
            bots_count=len(bot_ids),
            total_time=total_time,
            avg_time=total_time / len(bot_ids) if bot_ids else 0,
            min_time=0,
            max_time=0,
            success_count=success_count,
            failure_count=len(errors),
            errors=errors[:5],
        )

        print(f"✅ Started {success_count}/{len(bot_ids)} bots in {total_time:.2f}s")
        if errors:
            print(f"❌ {len(errors)} failures: {errors[0]}")

        return result

    async def stop_bots_batch(self, bot_ids: List[int]) -> BulkTestResult:
        """Stop multiple bots concurrently"""
        print(f"🛑 Stopping {len(bot_ids)} bots concurrently...")

        start_time = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def stop_single_bot(bot_id: int):
            async with semaphore:
                try:
                    response = await self.client.post(f"/api/v1/bots/{bot_id}/stop")
                    if response.status_code == 200:
                        return True, None
                    else:
                        error = f"HTTP {response.status_code}: {response.text}"
                        return False, error
                except Exception as e:
                    return False, str(e)

        tasks = [stop_single_bot(bot_id) for bot_id in bot_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time
        success_count = 0
        errors = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result[0]:
                success_count += 1
            else:
                errors.append(result[1])

        result = BulkTestResult(
            operation="stop_bots",
            bots_count=len(bot_ids),
            total_time=total_time,
            avg_time=total_time / len(bot_ids) if bot_ids else 0,
            min_time=0,
            max_time=0,
            success_count=success_count,
            failure_count=len(errors),
            errors=errors[:5],
        )

        print(f"✅ Stopped {success_count}/{len(bot_ids)} bots in {total_time:.2f}s")
        if errors:
            print(f"❌ {len(errors)} failures: {errors[0]}")

        return result

    async def check_bots_status(self, bot_ids: List[int]) -> Dict[str, Any]:
        """Check status of all bots"""
        print(f"📊 Checking status of {len(bot_ids)} bots...")

        status_counts = {
            "running": 0,
            "stopped": 0,
            "error": 0,
            "starting": 0,
            "stopping": 0,
        }

        for bot_id in bot_ids:
            try:
                response = await self.client.get(f"/api/v1/bots/{bot_id}")
                if response.status_code == 200:
                    status = response.json()["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1
                else:
                    status_counts["error"] += 1
            except Exception as e:
                status_counts["error"] += 1

        print(f"📊 Status summary: {status_counts}")
        return status_counts

    async def cleanup(self):
        """Clean up created bots"""
        print(f"🧹 Cleaning up {len(self.created_bots)} test bots...")

        if not self.created_bots:
            return

        # Stop all bots first
        await self.stop_bots_batch(self.created_bots)

        # Delete bots
        semaphore = asyncio.Semaphore(self.max_concurrent)
        delete_tasks = []

        async def delete_bot(bot_id: int):
            async with semaphore:
                try:
                    await self.client.delete(f"/api/v1/bots/{bot_id}")
                    print(f"✅ Deleted bot {bot_id}")
                except Exception as e:
                    print(f"❌ Failed to delete bot {bot_id}: {e}")

        delete_tasks = [delete_bot(bot_id) for bot_id in self.created_bots]
        await asyncio.gather(*delete_tasks, return_exceptions=True)

        print("✅ Cleanup completed")

    async def run_bulk_test(self, bot_count: int = 12):
        """Run complete bulk operations test"""
        print("🚀 Starting Bulk Bot Operations Test")
        print("=" * 50)

        try:
            # Test 1: Create multiple bots
            create_result = await self.create_bot_batch(bot_count)
            self.test_results.append(create_result)

            if create_result.success_count == 0:
                print("❌ No bots created, stopping test")
                return

            successful_bot_ids = self.created_bots[-create_result.success_count :]

            # Test 2: Start all bots
            start_result = await self.start_bots_batch(successful_bot_ids)
            self.test_results.append(start_result)

            # Wait a bit for bots to start
            await asyncio.sleep(5)

            # Check status
            await self.check_bots_status(successful_bot_ids)

            # Test 3: Stop all bots
            stop_result = await self.stop_bots_batch(successful_bot_ids)
            self.test_results.append(stop_result)

            # Final status check
            await self.check_bots_status(successful_bot_ids)

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            # Print results
            self.print_results()

    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 BULK OPERATIONS TEST RESULTS")
        print("=" * 60)

        total_bots = sum(r.bots_count for r in self.test_results)
        total_time = sum(r.total_time for r in self.test_results)
        total_success = sum(r.success_count for r in self.test_results)
        total_failures = sum(r.failure_count for r in self.test_results)

        print(f"🤖 Total bots processed: {total_bots}")
        print(".2f")
        print(f"✅ Total successful operations: {total_success}")
        print(f"❌ Total failed operations: {total_failures}")
        print(".1f")

        print("\n📈 Detailed Results:")
        for result in self.test_results:
            print(f"\n{result.operation.upper()}:")
            print(f"  Bots: {result.bots_count}")
            print(".2f")
            print(".3f")
            print(f"  Success: {result.success_count}")
            print(f"  Failures: {result.failure_count}")
            if result.errors:
                print(f"  Sample errors: {result.errors[0][:100]}...")

        # Save results to file
        results_data = {
            "timestamp": time.time(),
            "total_bots": total_bots,
            "total_time": total_time,
            "total_success": total_success,
            "total_failures": total_failures,
            "success_rate": (total_success / (total_success + total_failures)) * 100
            if (total_success + total_failures) > 0
            else 0,
            "results": [
                {
                    "operation": r.operation,
                    "bots_count": r.bots_count,
                    "total_time": r.total_time,
                    "avg_time": r.avg_time,
                    "success_count": r.success_count,
                    "failure_count": r.failure_count,
                    "errors": r.errors,
                }
                for r in self.test_results
            ],
        }

        with open("bulk_operations_test_results.json", "w") as f:
            json.dump(results_data, f, indent=2)

        print("\n💾 Results saved to bulk_operations_test_results.json")
        print("=" * 60)


async def main():
    """Main test runner"""
    bot_counts = [5, 10, 12, 15]  # Test different batch sizes

    for count in bot_counts:
        print(f"\n🎯 Testing with {count} bots")
        async with BulkBotOperationsTester(max_concurrent=5) as tester:
            await tester.run_bulk_test(count)


if __name__ == "__main__":
    asyncio.run(main())
