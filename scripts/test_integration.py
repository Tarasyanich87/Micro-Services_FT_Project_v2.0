#!/usr/bin/env python3
"""
Integration tests for local development
"""

import asyncio
import httpx
import time


async def test_service_health():
    """Test all services are healthy"""
    services = [
        ("Management", "http://localhost:8002/health"),
        ("Backtesting", "http://localhost:8003/health"),
        ("FreqAI", "http://localhost:8004/health"),
    ]

    print("🔍 Testing service health...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, url in services:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    print(f"✅ {name}: {status}")
                else:
                    print(f"❌ {name}: Bad status {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: {e}")


async def test_basic_workflow():
    """Test basic workflow"""
    print("\n🔄 Testing basic workflow...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test backtesting server directly
            response = await client.post(
                "http://localhost:8003/test-backtest?strategy_name=TestStrategy"
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backtesting: {data.get('message', 'started')}")
            else:
                print(f"❌ Backtesting failed: {response.status_code}")

            # Test FreqAI server directly
            response = await client.post(
                "http://localhost:8004/train-model?model_name=test_model&model_type=LightGBM"
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ FreqAI training: {data.get('status', 'unknown')}")
            else:
                print(f"❌ FreqAI training failed: {response.status_code}")

            # Test FreqAI prediction (mock features)
            mock_features = {"rsi": 70.0, "macd": 0.5, "volume_mean": 1000.0}

            response = await client.post(
                "http://localhost:8004/predict/test_model", json=mock_features
            )

            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    print("✅ FreqAI prediction: successful")
                else:
                    print(f"⚠️ FreqAI prediction: {data['error']}")
            else:
                print(f"❌ FreqAI prediction failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Workflow test failed: {e}")


async def main():
    """Main test function"""
    print("🧪 Starting local integration tests...")

    # Wait for services to start
    print("⏳ Waiting for services to be ready...")
    time.sleep(10)

    # Test health
    await test_service_health()

    # Test workflow
    await test_basic_workflow()

    print("\n🎉 Integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
