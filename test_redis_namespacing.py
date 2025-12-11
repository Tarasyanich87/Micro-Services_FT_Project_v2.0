#!/usr/bin/env python3
"""
Test Redis Streams namespacing implementation
"""

import asyncio
import redis.asyncio as redis
from shared.config.redis_streams import redis_streams_config


async def test_namespacing():
    """Test the new namespacing configuration"""
    print("🧪 Testing Redis Streams namespacing...")

    # Connect to Redis
    redis_client = redis.from_url("redis://localhost:6379")
    await redis_client.ping()
    print("✅ Connected to Redis")

    # Test stream names
    print("\n📋 Testing stream names:")
    print(f"Management → Trading: {redis_streams_config.MGMT_TRADING_COMMANDS}")
    print(f"Trading → Management: {redis_streams_config.TRADING_MGMT_STATUS}")
    print(f"Management → Backtesting: {redis_streams_config.MGMT_BACKTESTING_COMMANDS}")
    print(f"Backtesting → Management: {redis_streams_config.BACKTESTING_MGMT_RESULTS}")

    # Test consumer groups
    print("\n👥 Testing consumer groups:")
    print(f"Trading consumers: {redis_streams_config.TRADING_CONSUMERS}")
    print(f"Backtesting consumers: {redis_streams_config.BACKTESTING_CONSUMERS}")
    print(f"Management consumers: {redis_streams_config.MANAGEMENT_CONSUMERS}")

    # Test stream limits
    print("\n📏 Testing stream limits:")
    for stream_name in redis_streams_config.get_all_command_streams():
        limits = redis_streams_config.get_stream_limit(stream_name)
        print(
            f"{stream_name}: maxlen={limits['maxlen']}, approximate={limits['approximate']}"
        )

    # Test validation
    print("\n✅ Testing stream name validation:")
    valid_names = [
        "mgmt:trading:commands",
        "backtesting:mgmt:results",
        "freqai:mgmt:status",
    ]
    invalid_names = ["invalid", "too:many:parts:here", "wrong:service:purpose"]

    for name in valid_names:
        is_valid = redis_streams_config.validate_stream_name(name)
        print(f"✅ {name}: {'valid' if is_valid else 'invalid'}")

    for name in invalid_names:
        is_valid = redis_streams_config.validate_stream_name(name)
        print(f"❌ {name}: {'valid' if is_valid else 'invalid'}")

    # Test legacy compatibility
    print("\n🔄 Testing legacy compatibility:")
    from shared.config.redis_streams import legacy_config

    print(f"Legacy 'mcp_commands' → {legacy_config.get_legacy_stream('mcp_commands')}")
    print(f"Legacy 'bot_events' → {legacy_config.get_legacy_stream('bot_events')}")

    await redis_client.close()
    print("\n🎉 Namespacing test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_namespacing())
