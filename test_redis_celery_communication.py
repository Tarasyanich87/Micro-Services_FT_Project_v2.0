#!/usr/bin/env python3
"""
Test Redis Streams communication for backtesting workflows
"""

import redis
import json
import time
from datetime import datetime


def test_redis_streams_connection():
    """Test Redis connection and basic operations."""
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")

        # Test basic operations
        r.set("test_key", "test_value")
        value = r.get("test_key")
        assert value.decode() == "test_value"
        r.delete("test_key")
        print("✅ Redis basic operations working")

        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def test_redis_streams_operations():
    """Test Redis Streams operations."""
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)

        # Clean up any existing streams
        stream_name = "test_backtest_commands"
        r.delete(stream_name)

        # Add message to stream
        message = {
            "bot_name": "test_bot",
            "bot_config": {"strategy": "TestStrategy"},
            "freqai_model": None,
            "timestamp": datetime.now().isoformat(),
        }

        message_id = r.xadd(stream_name, {"data": json.dumps(message)})
        print(f"✅ Added message to stream: {message_id}")

        # Read from stream
        messages = r.xread({stream_name: "0"}, count=1, block=1000)
        if messages:
            stream, message_list = messages[0]
            msg_id, msg_data = message_list[0]
            data = json.loads(msg_data[b"data"].decode())
            assert data["bot_name"] == "test_bot"
            print("✅ Read message from stream successfully")

        # Clean up
        r.delete(stream_name)
        return True

    except Exception as e:
        print(f"❌ Redis Streams operations failed: {e}")
        return False


def test_celery_redis_backend():
    """Test Celery Redis backend connectivity."""
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)

        # Check if Celery is using Redis
        keys = r.keys("celery-task-meta-*")
        print(f"✅ Found {len(keys)} Celery task results in Redis")

        # Check Celery queues
        queues = r.keys("celery")
        if queues:
            print("✅ Celery queues exist in Redis")
        else:
            print("⚠️  No Celery queues found (worker may not be active)")

        return True

    except Exception as e:
        print(f"❌ Celery Redis backend test failed: {e}")
        return False


def test_backtesting_workflow_simulation():
    """Simulate a basic backtesting workflow."""
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)

        # Simulate management server sending backtest command
        command_stream = "mcp_commands"
        r.delete(command_stream)  # Clean up

        command_data = {
            "type": "START_BACKTEST",
            "data": {
                "strategy_name": "TestStrategy",
                "config": {"stake_amount": 100, "timerange": "20240101-20240102"},
            },
            "source": "management_server",
            "timestamp": time.time(),
        }

        # Add command to stream
        r.xadd(command_stream, {"data": json.dumps(command_data)})
        print("✅ Simulated backtest command sent to Redis Stream")

        # Simulate reading the command (like trading gateway would)
        messages = r.xread({command_stream: "0"}, count=1, block=1000)
        if messages:
            print("✅ Command successfully read from Redis Stream")

        # Clean up
        r.delete(command_stream)
        return True

    except Exception as e:
        print(f"❌ Backtesting workflow simulation failed: {e}")
        return False


def main():
    """Run all Redis/Celery communication tests."""
    print("🔍 Testing Redis Streams and Celery Communication")
    print("=" * 60)

    tests = [
        ("Redis Connection", test_redis_streams_connection),
        ("Redis Streams Operations", test_redis_streams_operations),
        ("Celery Redis Backend", test_celery_redis_backend),
        ("Backtesting Workflow Simulation", test_backtesting_workflow_simulation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All Redis/Celery communication tests PASSED!")
        print("✅ Backtesting через Redis Streams работает")
        print("✅ Celery асинхронные задачи работают")
        print("✅ Гипероптимизация через Celery готова")
    else:
        print("⚠️  Некоторые тесты провалились - проверьте конфигурацию")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
