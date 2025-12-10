import asyncio
import pytest
import time
from typing import List
import httpx
import statistics


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.asyncio
    async def test_api_response_time_under_100ms(self):
        """Test that API health check responds within 100ms."""
        async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
            start_time = time.time()
            response = await client.get("/health")
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            assert response.status_code == 200
            assert response_time < 100, (
                f"Response time {response_time}ms exceeds 100ms limit"
            )

    @pytest.mark.asyncio
    async def test_concurrent_api_requests_10_users(self):
        """Test API performance under concurrent load of 10 users."""

        async def make_request(client: httpx.AsyncClient, user_id: int):
            # Register user
            reg_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "username": f"perf_user_{user_id}",
                    "email": f"perf{user_id}@test.com",
                    "password": "password123",
                },
            )
            assert reg_response.status_code in [200, 400]  # 400 if user exists

            # Login
            login_response = await client.post(
                "/api/v1/auth/login",
                data={"username": f"perf_user_{user_id}", "password": "password123"},
            )
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]

            # Make authenticated request
            headers = {"Authorization": f"Bearer {token}"}
            start_time = time.time()
            response = await client.get("/api/v1/bots/", headers=headers)
            end_time = time.time()

            return (end_time - start_time) * 1000  # Response time in ms

        async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
            # Run 10 concurrent requests
            tasks = [make_request(client, i) for i in range(10)]
            response_times = await asyncio.gather(*tasks)

            # Analyze results
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            print(f"Performance Results (10 concurrent users):")
            print(f"  Average: {avg_response_time:.2f}ms")
            print(f"  Max: {max_response_time:.2f}ms")
            print(f"  Min: {min_response_time:.2f}ms")

            # Assert performance requirements
            assert avg_response_time < 500, (
                f"Average response time {avg_response_time}ms exceeds 500ms"
            )
            assert max_response_time < 2000, (
                f"Max response time {max_response_time}ms exceeds 2000ms"
            )

    @pytest.mark.asyncio
    async def test_database_query_performance(self):
        """Test database query performance for bot listing."""
        # Setup user
        async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
            login_response = await client.post(
                "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
            )
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test different page sizes
            page_sizes = [10, 50, 100]
            for limit in page_sizes:
                start_time = time.time()
                response = await client.get(
                    f"/api/v1/bots/?limit={limit}", headers=headers
                )
                end_time = time.time()

                response_time = (end_time - start_time) * 1000

                assert response.status_code == 200
                assert response_time < 200, (
                    f"Query with limit {limit} took {response_time}ms (should be < 200ms)"
                )

    @pytest.mark.asyncio
    async def test_redis_streams_performance(self):
        """Test Redis streams performance for command processing."""
        import redis.asyncio as redis

        # Connect to Redis
        r = redis.from_url("redis://localhost:6379")

        # Test publishing performance
        publish_times = []
        for i in range(100):
            start_time = time.time()
            await r.xadd(
                "test_stream",
                {
                    "type": "TEST_COMMAND",
                    "data": f'{{"test_id": {i}}}',
                    "source": "performance_test",
                    "timestamp": str(time.time()),
                },
            )
            end_time = time.time()
            publish_times.append((end_time - start_time) * 1000)

        avg_publish_time = statistics.mean(publish_times)
        max_publish_time = max(publish_times)

        print(f"Redis Publish Performance (100 messages):")
        print(f"  Average: {avg_publish_time:.2f}ms")
        print(f"  Max: {max_publish_time:.2f}ms")

        assert avg_publish_time < 10, (
            f"Average publish time {avg_publish_time}ms exceeds 10ms"
        )
        assert max_publish_time < 50, (
            f"Max publish time {max_publish_time}ms exceeds 50ms"
        )

        # Cleanup
        await r.delete("test_stream")
        await r.aclose()

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage during concurrent operations."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
            # Login once
            login_response = await client.post(
                "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
            )
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Make 50 concurrent requests
            tasks = []
            for i in range(50):
                task = client.get("/api/v1/bots/", headers=headers)
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Check memory after load
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            print(f"Memory Usage Test:")
            print(f"  Initial: {initial_memory:.2f}MB")
            print(f"  Final: {final_memory:.2f}MB")
            print(f"  Increase: {memory_increase:.2f}MB")

            # Assert reasonable memory usage
            assert memory_increase < 50, (
                f"Memory increase {memory_increase}MB exceeds 50MB limit"
            )

    @pytest.mark.asyncio
    async def test_bot_lifecycle_performance(self):
        """Test performance of complete bot lifecycle operations."""
        async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
            # Login
            login_response = await client.post(
                "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
            )
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create bot
            create_start = time.time()
            create_response = await client.post(
                "/api/v1/bots/",
                json={
                    "name": "perf_test_bot",
                    "strategy_name": "TestStrategy",
                    "exchange": "binance",
                    "stake_currency": "USDT",
                    "stake_amount": 100.0,
                },
                headers=headers,
            )
            create_time = (time.time() - create_start) * 1000

            assert create_response.status_code == 201
            bot_id = create_response.json()["id"]

            # Start bot
            start_start = time.time()
            start_response = await client.post(
                f"/api/v1/bots/{bot_id}/start", headers=headers
            )
            start_time = (time.time() - start_start) * 1000

            assert start_response.status_code == 200

            # Wait for bot to start (up to 5 seconds)
            bot_started = False
            for _ in range(10):
                await asyncio.sleep(0.5)
                status_response = await client.get(
                    f"/api/v1/bots/{bot_id}", headers=headers
                )
                if status_response.json()["status"] == "running":
                    bot_started = True
                    break

            # Stop bot
            stop_start = time.time()
            stop_response = await client.post(
                f"/api/v1/bots/{bot_id}/stop", headers=headers
            )
            stop_time = (time.time() - stop_start) * 1000

            assert stop_response.status_code == 200

            # Delete bot
            delete_start = time.time()
            delete_response = await client.delete(
                f"/api/v1/bots/{bot_id}", headers=headers
            )
            delete_time = (time.time() - delete_start) * 1000

            print(f"Bot Lifecycle Performance:")
            print(f"  Create: {create_time:.2f}ms")
            print(f"  Start: {start_time:.2f}ms")
            print(f"  Stop: {stop_time:.2f}ms")
            print(f"  Delete: {delete_time:.2f}ms")
            print(f"  Bot Started: {bot_started}")

            # Assert performance requirements
            assert create_time < 500, f"Create time {create_time}ms exceeds 500ms"
            assert start_time < 200, f"Start time {start_time}ms exceeds 200ms"
            assert stop_time < 200, f"Stop time {stop_time}ms exceeds 200ms"
            assert delete_time < 200, f"Delete time {delete_time}ms exceeds 200ms"
            assert bot_started, "Bot failed to start within timeout"
