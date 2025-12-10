#!/usr/bin/env python3
"""
Quick Bulk Operations Demo: Create 3 bots, start them, then emergency stop all
"""

import asyncio
import httpx
import time
import json

BASE_URL = "http://localhost:8002"


async def authenticate(client):
    """Register and login"""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "demo_user",
            "email": "demo@example.com",
            "password": "demopass123",
            "full_name": "Demo User",
        },
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "demo_user", "password": "demopass123"},
    )
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authenticated")


async def create_and_start_bots():
    """Create 3 bots and start them"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        await authenticate(client)

        print("🤖 Creating 3 bots...")

        # Create 3 bots
        bot_ids = []
        for i in range(1, 4):
            bot_data = {
                "name": f"DemoBot_{i}_{int(time.time())}",
                "strategy_name": "TestStrategy",
                "exchange": "binance",
                "stake_currency": "USDT",
                "stake_amount": 100.0,
            }

            response = await client.post("/api/v1/bots/", json=bot_data)
            if response.status_code == 201:
                bot_id = response.json()["id"]
                bot_ids.append(bot_id)
                print(f"✅ Created bot {i}: ID {bot_id}")
            else:
                print(f"❌ Failed to create bot {i}: {response.status_code}")

        if not bot_ids:
            print("❌ No bots created")
            return

        print(f"🚀 Starting {len(bot_ids)} bots...")

        # Start all bots
        for bot_id in bot_ids:
            response = await client.post(f"/api/v1/bots/{bot_id}/start")
            if response.status_code == 200:
                print(f"✅ Started bot {bot_id}")
            else:
                print(f"❌ Failed to start bot {bot_id}: {response.status_code}")

        # Wait a bit for bots to start
        print("⏳ Waiting 10 seconds for bots to initialize...")
        await asyncio.sleep(10)

        # Check status
        print("📊 Checking bot statuses...")
        for bot_id in bot_ids:
            response = await client.get(f"/api/v1/bots/{bot_id}")
            if response.status_code == 200:
                status = response.json()["status"]
                print(f"📊 Bot {bot_id}: {status}")
            else:
                print(f"❌ Failed to get status for bot {bot_id}")

        print("🚨 Executing EMERGENCY STOP ALL...")
        print("=" * 50)

        # Emergency stop all
        emergency_response = await client.post("/api/v1/emergency/stop-all")
        if emergency_response.status_code == 200:
            print("✅ Emergency stop command sent successfully!")
            result = emergency_response.json()
            print(f"📊 Emergency stop result: {result}")
        else:
            print(f"❌ Emergency stop failed: {emergency_response.status_code}")
            print(f"Response: {emergency_response.text}")

        # Wait and check final status
        print("⏳ Waiting 5 seconds for emergency stop to complete...")
        await asyncio.sleep(5)

        print("📊 Final status check:")
        for bot_id in bot_ids:
            response = await client.get(f"/api/v1/bots/{bot_id}")
            if response.status_code == 200:
                status = response.json()["status"]
                print(f"📊 Bot {bot_id}: {status}")
            else:
                print(f"❌ Failed to get final status for bot {bot_id}")

        # Cleanup
        print("🧹 Cleaning up demo bots...")
        for bot_id in bot_ids:
            try:
                await client.delete(f"/api/v1/bots/{bot_id}")
                print(f"✅ Deleted bot {bot_id}")
            except Exception as e:
                print(f"❌ Failed to delete bot {bot_id}: {e}")

        print("🎉 Demo completed!")


if __name__ == "__main__":
    asyncio.run(create_and_start_bots())
