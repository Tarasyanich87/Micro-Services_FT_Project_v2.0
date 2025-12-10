#!/usr/bin/env python3
"""
Test FreqAI Model Handler functionality
"""

import asyncio
import tempfile
import base64
from pathlib import Path


async def test_freqai_model_handler():
    """Test FreqAI model handler functionality"""
    print("🧪 Testing FreqAI Model Handler")

    # Import handler
    import sys

    sys.path.append("trading_gateway")
    from services.freqai_model_handler import FreqAIModelHandler

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = FreqAIModelHandler(cache_dir=temp_dir, max_cache_size=3)

        # Test data
        test_model_data = {
            "filename": "test_model.joblib",
            "content_b64": base64.b64encode(b"fake model data").decode(),
        }

        print("📤 Testing model storage...")
        try:
            model_path = await handler.store_model_for_bot("test_bot", test_model_data)
            print(f"✅ Model stored: {model_path}")

            # Check if file exists
            if Path(model_path).exists():
                print("✅ Model file exists")
            else:
                print("❌ Model file not found")

            # Test cache retrieval
            cached_path = handler.get_model_path("test_bot")
            if cached_path == model_path:
                print("✅ Cache working correctly")
            else:
                print(f"❌ Cache mismatch: {cached_path} != {model_path}")

            # Test cache stats
            stats = handler.get_cache_stats()
            print(f"📊 Cache stats: {stats}")

            # Test cleanup
            await handler.cleanup_bot_models("test_bot")
            if not Path(model_path).exists():
                print("✅ Model cleanup successful")
            else:
                print("❌ Model file still exists after cleanup")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_freqai_model_handler())
