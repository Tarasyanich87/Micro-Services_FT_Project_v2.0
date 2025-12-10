import asyncio
import pytest
import httpx
from typing import Dict, Any

from tests.conftest import app_client  # type: ignore


@pytest.mark.e2e
class TestEndToEndBotLifecycle:
    """
    End-to-end tests for complete bot lifecycle:
    Create → Start → Monitor → Stop → Delete
    """

    @pytest.mark.asyncio
    async def test_complete_bot_lifecycle(self):
        """
        Test the complete lifecycle of a bot from creation to deletion.
        This test simulates real user workflow.
        """
        # Test data
        bot_data = {
            "name": "e2e_test_bot",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 100.0,
        }

        async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
            # Step 1: Register and authenticate user
            reg_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "e2e_user",
                    "email": "e2e@test.com",
                    "password": "securepassword",
                },
            )
            assert reg_response.status_code == 200

            login_response = await client.post(
                "/api/v1/auth/login",
                json={"username": "e2e_user", "password": "securepassword"},
            )
            assert login_response.status_code == 200

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Step 2: Create a bot
            create_response = await client.post(
                "/api/v1/bots/", json=bot_data, headers=headers
            )
            assert create_response.status_code == 201

            bot_response = create_response.json()
            bot_id = bot_response["id"]
            assert bot_response["name"] == bot_data["name"]
            assert bot_response["status"] == "stopped"

            # Step 3: Verify bot appears in list
            list_response = await client.get("/api/v1/bots/", headers=headers)
            assert list_response.status_code == 200

            bots_list = list_response.json()
            assert len(bots_list) >= 1
            our_bot = next((b for b in bots_list if b["id"] == bot_id), None)
            assert our_bot is not None
            assert our_bot["status"] == "stopped"

            # Step 4: Start the bot
            start_response = await client.post(
                f"/api/v1/bots/{bot_id}/start", headers=headers
            )
            assert start_response.status_code == 200
            assert start_response.json()["status"] == "start_command_sent"

            # Step 5: Check bot status changes to starting/running
            # Wait a bit for async processing
            await asyncio.sleep(2)

            status_response = await client.get(
                f"/api/v1/bots/{bot_id}", headers=headers
            )
            assert status_response.status_code == 200
            bot_status = status_response.json()
            # Status should be either "starting" or "running" depending on timing
            assert bot_status["status"] in ["starting", "running", "stopped"]

            # Step 6: Get detailed bot status
            detailed_status_response = await client.get(
                f"/api/v1/bots/{bot_id}/status", headers=headers
            )
            assert detailed_status_response.status_code == 200
            detailed_status = detailed_status_response.json()
            assert detailed_status["status"] == "success"
            assert detailed_status["bot_name"] == bot_data["name"]

            # Step 7: Stop the bot
            stop_response = await client.post(
                f"/api/v1/bots/{bot_id}/stop", headers=headers
            )
            assert stop_response.status_code == 200
            assert stop_response.json()["status"] == "stop_command_sent"

            # Step 8: Verify bot is stopped
            await asyncio.sleep(2)

            final_status_response = await client.get(
                f"/api/v1/bots/{bot_id}", headers=headers
            )
            assert final_status_response.status_code == 200
            final_bot = final_status_response.json()
            assert final_bot["status"] == "stopped"

            # Step 9: Delete the bot
            delete_response = await client.delete(
                f"/api/v1/bots/{bot_id}", headers=headers
            )
            assert delete_response.status_code == 204

            # Step 10: Verify bot is gone
            final_list_response = await client.get("/api/v1/bots/", headers=headers)
            assert final_list_response.status_code == 200

            final_bots_list = final_list_response.json()
            deleted_bot = next((b for b in final_bots_list if b["id"] == bot_id), None)
            assert deleted_bot is None

    @pytest.mark.asyncio
    async def test_concurrent_bot_operations(self, app_client):
        """
        Test concurrent operations on multiple bots.
        """
        # Setup user
        reg_response = await app_client.post(
            "/api/v1/auth/register",
            json={
                "username": "concurrent_user",
                "email": "concurrent@test.com",
                "password": "password",
            },
        )
        assert reg_response.status_code == 200

        login_response = await app_client.post(
            "/api/v1/auth/login",
            json={"username": "concurrent_user", "password": "password"},
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create multiple bots concurrently
        bot_creation_tasks = []
        for i in range(3):
            bot_data = {
                "name": f"concurrent_bot_{i}",
                "strategy_name": "TestStrategy",
                "exchange": "binance",
                "stake_currency": "USDT",
                "stake_amount": 100.0,
            }
            task = app_client.post("/api/v1/bots/", json=bot_data, headers=headers)
            bot_creation_tasks.append(task)

        creation_results = await asyncio.gather(*bot_creation_tasks)

        # Verify all bots were created
        bot_ids = []
        for result in creation_results:
            assert result.status_code == 201
            bot_ids.append(result.json()["id"])

        # Start all bots concurrently
        start_tasks = []
        for bot_id in bot_ids:
            task = app_client.post(f"/api/v1/bots/{bot_id}/start", headers=headers)
            start_tasks.append(task)

        start_results = await asyncio.gather(*start_tasks)

        # Verify all start commands were accepted
        for result in start_results:
            assert result.status_code == 200
            assert result.json()["status"] == "start_command_sent"

        # Stop all bots concurrently
        stop_tasks = []
        for bot_id in bot_ids:
            task = app_client.post(f"/api/v1/bots/{bot_id}/stop", headers=headers)
            stop_tasks.append(task)

        stop_results = await asyncio.gather(*stop_tasks)

        # Verify all stop commands were accepted
        for result in stop_results:
            assert result.status_code == 200
            assert result.json()["status"] == "stop_command_sent"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, app_client):
        """
        Test error handling and system recovery capabilities.
        """
        # Setup user
        reg_response = await app_client.post(
            "/api/v1/auth/register",
            json={
                "username": "error_test_user",
                "email": "error@test.com",
                "password": "password",
            },
        )
        assert reg_response.status_code == 200

        login_response = await app_client.post(
            "/api/v1/auth/login",
            json={"username": "error_test_user", "password": "password"},
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test 1: Try to start non-existent bot
        fake_bot_response = await app_client.post(
            "/api/v1/bots/99999/start", headers=headers
        )
        assert fake_bot_response.status_code == 404

        # Test 2: Try to access bot without authentication
        no_auth_response = await app_client.get("/api/v1/bots/")
        assert no_auth_response.status_code == 401

        # Test 3: Create bot with invalid data
        invalid_bot_response = await app_client.post(
            "/api/v1/bots/",
            json={
                "name": "",  # Invalid: empty name
                "strategy_name": "TestStrategy",
                "exchange": "invalid_exchange",
            },
            headers=headers,
        )
        assert invalid_bot_response.status_code == 422  # Validation error

        # Test 4: Try to delete non-existent bot
        delete_fake_response = await app_client.delete(
            "/api/v1/bots/99999", headers=headers
        )
        assert delete_fake_response.status_code == 404

        # Test 5: Health check still works
        health_response = await app_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_system_limits_and_boundaries(self, app_client):
        """
        Test system limits and boundary conditions.
        """
        # Setup user
        reg_response = await app_client.post(
            "/api/v1/auth/register",
            json={
                "username": "limits_user",
                "email": "limits@test.com",
                "password": "password",
            },
        )
        assert reg_response.status_code == 200

        login_response = await app_client.post(
            "/api/v1/auth/login",
            json={"username": "limits_user", "password": "password"},
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test pagination limits
        for limit in [1, 50, 100, 1000]:
            list_response = await app_client.get(
                f"/api/v1/bots/?limit={limit}", headers=headers
            )
            assert list_response.status_code == 200

        # Test invalid pagination
        invalid_limit_response = await app_client.get(
            "/api/v1/bots/?limit=1001",  # Exceeds max limit
            headers=headers,
        )
        assert invalid_limit_response.status_code == 422

        # Test negative pagination
        negative_response = await app_client.get(
            "/api/v1/bots/?limit=-1", headers=headers
        )
        assert negative_response.status_code == 422
