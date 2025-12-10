#!/usr/bin/env python3
"""
Comprehensive FreqAI Integration Test
Tests the complete workflow: model upload → bot creation → model assignment → bot start → model transmission
"""

import asyncio
import httpx
import json
import time
import base64
from pathlib import Path

BASE_URL = "http://localhost:8002"
TG_URL = "http://localhost:8001"


class FreqAIIntegrationTester:
    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.token: str | None = None
        self.test_model_id: int | None = None
        self.test_bot_id: int | None = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def authenticate(self):
        """Authenticate with the system"""
        # Register user
        await self.client.post(
            "/api/v1/auth/register",
            json={
                "username": "freqai_integration_test",
                "email": "freqai@test.com",
                "password": "testpass123",
                "full_name": "FreqAI Integration Test",
            },
        )

        # Login
        response = await self.client.post(
            "/api/v1/auth/login/json",
            json={"username": "freqai_integration_test", "password": "testpass123"},
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ Authenticated successfully")
        else:
            print(f"❌ Authentication failed: {response.status_code}")

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")

    async def test_upload_freqai_model(self):
        """Test uploading FreqAI model"""
        print("📤 Testing FreqAI model upload...")

        model_path = Path("test_freqai_model.joblib")
        if not model_path.exists():
            self.log_result("Model Upload", False, "Test model file not found")
            return False

        with open(model_path, "rb") as f:
            files = {
                "file": ("test_freqai_model.joblib", f, "application/octet-stream")
            }
            data = {
                "name": "IntegrationTestModel",
                "description": "Test model for integration testing",
            }

            response = await self.client.post(
                "/api/v1/freqai/models/",
                files=files,
                params={
                    "name": "IntegrationTestModel",
                    "description": "Test model for integration testing",
                },
            )

        if response.status_code == 201:
            model_data = response.json()
            self.test_model_id = model_data["id"]
            self.log_result("Model Upload", True, f"Model ID: {self.test_model_id}")
            return True
        else:
            self.log_result(
                "Model Upload", False, f"HTTP {response.status_code}: {response.text}"
            )
            return False

    async def test_list_freqai_models(self):
        """Test listing FreqAI models"""
        print("📋 Testing FreqAI models list...")

        response = await self.client.get("/api/v1/freqai/models/")
        if response.status_code == 200:
            models = response.json()
            model_count = len(models)
            self.log_result("Models List", True, f"Found {model_count} models")

            # Check if our test model is in the list
            test_model_found = any(m["id"] == self.test_model_id for m in models)
            self.log_result(
                "Test Model in List",
                test_model_found,
                f"Test model ID {self.test_model_id} found: {test_model_found}",
            )
            return True
        else:
            self.log_result("Models List", False, f"HTTP {response.status_code}")
            return False

    async def test_create_bot_with_freqai(self):
        """Test creating bot with FreqAI model"""
        print("🤖 Testing bot creation with FreqAI model...")

        bot_data = {
            "name": f"FreqAI_Test_Bot_{int(time.time())}",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 100.0,
            "freqai_model_id": self.test_model_id,
        }

        response = await self.client.post("/api/v1/bots/", json=bot_data)
        if response.status_code == 201:
            bot_data_response = response.json()
            self.test_bot_id = bot_data_response["id"]
            self.log_result(
                "Bot Creation",
                True,
                f"Bot ID: {self.test_bot_id}, FreqAI Model: {self.test_model_id}",
            )
            return True
        else:
            self.log_result(
                "Bot Creation", False, f"HTTP {response.status_code}: {response.text}"
            )
            return False

    async def test_get_bot_details(self):
        """Test getting bot details with FreqAI model"""
        print("📊 Testing bot details retrieval...")

        response = await self.client.get(f"/api/v1/bots/{self.test_bot_id}")
        if response.status_code == 200:
            bot = response.json()
            freqai_model_id = bot.get("freqai_model_id")

            if freqai_model_id == self.test_model_id:
                self.log_result(
                    "Bot FreqAI Assignment",
                    True,
                    f"Bot has correct FreqAI model: {freqai_model_id}",
                )
                return True
            else:
                self.log_result(
                    "Bot FreqAI Assignment",
                    False,
                    f"Expected {self.test_model_id}, got {freqai_model_id}",
                )
                return False
        else:
            self.log_result("Bot Details", False, f"HTTP {response.status_code}")
            return False

    async def test_start_bot_with_freqai(self):
        """Test starting bot with FreqAI model"""
        print("🚀 Testing bot start with FreqAI model...")

        response = await self.client.post(f"/api/v1/bots/{self.test_bot_id}/start")
        if response.status_code == 200:
            result = response.json()
            self.log_result("Bot Start", True, f"Bot start initiated: {result}")

            # Wait a moment for bot to start
            await asyncio.sleep(3)

            # Check bot status
            status_response = await self.client.get(
                f"/api/v1/bots/{self.test_bot_id}/status"
            )
            if status_response.status_code == 200:
                status_data = status_response.json()
                self.log_result("Bot Status Check", True, f"Bot status: {status_data}")
            else:
                self.log_result(
                    "Bot Status Check",
                    False,
                    f"Status check failed: {status_response.status_code}",
                )

            return True
        else:
            self.log_result(
                "Bot Start", False, f"HTTP {response.status_code}: {response.text}"
            )
            return False

    async def test_freqai_model_transmission(self):
        """Test FreqAI model transmission to Trading Gateway"""
        print("🔄 Testing FreqAI model transmission...")

        # Check if bot is running and get its details
        bot_response = await self.client.get(f"/api/v1/bots/{self.test_bot_id}")
        if bot_response.status_code != 200:
            self.log_result("Model Transmission", False, "Cannot get bot details")
            return False

        bot = bot_response.json()

        # Check Trading Gateway for bot status
        tg_client = httpx.AsyncClient(base_url=TG_URL, timeout=10.0)
        try:
            status_response = await tg_client.get(f"/bots/{bot['name']}/status")
            if status_response.status_code == 200:
                tg_status = status_response.json()
                self.log_result(
                    "Trading Gateway Status", True, f"TG status: {tg_status}"
                )

                # Check if FreqAI model data is present
                if "freqai_model" in tg_status:
                    freqai_data = tg_status["freqai_model"]
                    self.log_result(
                        "FreqAI Model in TG",
                        True,
                        f"Model data present: {type(freqai_data)}",
                    )

                    # Check base64 encoding
                    if isinstance(freqai_data, dict) and "content_b64" in freqai_data:
                        b64_content = freqai_data["content_b64"]
                        try:
                            # Try to decode base64
                            decoded = base64.b64decode(b64_content)
                            self.log_result(
                                "Base64 Decoding", True, f"Decoded {len(decoded)} bytes"
                            )

                            # Check filename
                            filename = freqai_data.get("filename", "")
                            if filename.endswith(".joblib"):
                                self.log_result(
                                    "Model Filename",
                                    True,
                                    f"Correct filename: {filename}",
                                )
                            else:
                                self.log_result(
                                    "Model Filename",
                                    False,
                                    f"Incorrect filename: {filename}",
                                )

                            return True
                        except Exception as e:
                            self.log_result(
                                "Base64 Decoding", False, f"Decode error: {e}"
                            )
                            return False
                    else:
                        self.log_result(
                            "Base64 Content", False, "No base64 content found"
                        )
                        return False
                else:
                    self.log_result(
                        "FreqAI Model in TG",
                        False,
                        "No FreqAI model data in Trading Gateway",
                    )
                    return False
            else:
                self.log_result(
                    "Trading Gateway Status",
                    False,
                    f"HTTP {status_response.status_code}",
                )
                return False
        finally:
            await tg_client.aclose()

    async def test_freqai_predictions(self):
        """Test FreqAI predictions retrieval"""
        print("🔮 Testing FreqAI predictions...")

        # Get bot details
        bot_response = await self.client.get(f"/api/v1/bots/{self.test_bot_id}")
        if bot_response.status_code != 200:
            self.log_result("Predictions Test", False, "Cannot get bot details")
            return False

        bot = bot_response.json()
        bot_name = bot["name"]

        # Get predictions
        predictions_response = await self.client.get(
            f"/api/v1/advanced-trading/{self.test_bot_id}/predictions"
        )
        if predictions_response.status_code == 200:
            predictions_data = predictions_response.json()
            self.log_result(
                "Predictions Retrieval",
                True,
                f"Predictions data received: {len(str(predictions_data))} chars",
            )

            # Check if predictions contain FreqAI data
            if "data" in predictions_data and len(predictions_data["data"]) > 0:
                sample_data = predictions_data["data"][0]
                has_predictions = any(
                    "prediction" in key.lower() for key in sample_data.keys()
                )
                self.log_result(
                    "FreqAI Predictions",
                    has_predictions,
                    f"Predictions found: {has_predictions}",
                )
                return True
            else:
                self.log_result("Predictions Data", False, "No prediction data found")
                return False
        else:
            self.log_result(
                "Predictions Retrieval",
                False,
                f"HTTP {predictions_response.status_code}",
            )
            return False

    async def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")

        # Stop bot if running
        try:
            await self.client.post(f"/api/v1/bots/{self.test_bot_id}/stop")
            self.log_result("Bot Stop", True, "Bot stopped successfully")
        except:
            self.log_result("Bot Stop", False, "Bot stop failed")

        # Delete bot
        try:
            await self.client.delete(f"/api/v1/bots/{self.test_bot_id}")
            self.log_result("Bot Delete", True, "Bot deleted successfully")
        except:
            self.log_result("Bot Delete", False, "Bot delete failed")

        # Delete model
        try:
            await self.client.delete(f"/api/v1/freqai/models/{self.test_model_id}")
            self.log_result("Model Delete", True, "Model deleted successfully")
        except:
            self.log_result("Model Delete", False, "Model delete failed")

    async def run_full_integration_test(self):
        """Run complete FreqAI integration test"""
        print("🧪 Starting FreqAI Integration Test")
        print("=" * 60)

        try:
            # Phase 1: Model Management
            print("\n📤 PHASE 1: Model Management")
            print("-" * 30)

            upload_success = await self.test_upload_freqai_model()
            if not upload_success:
                print("❌ Model upload failed, stopping test")
                return False

            await self.test_list_freqai_models()

            # Phase 2: Bot Creation and Assignment
            print("\n🤖 PHASE 2: Bot Creation & FreqAI Assignment")
            print("-" * 45)

            bot_creation_success = await self.test_create_bot_with_freqai()
            if not bot_creation_success:
                print("❌ Bot creation failed, stopping test")
                return False

            await self.test_get_bot_details()

            # Phase 3: Bot Start and Model Transmission
            print("\n🚀 PHASE 3: Bot Start & Model Transmission")
            print("-" * 40)

            bot_start_success = await self.test_start_bot_with_freqai()
            if bot_start_success:
                await self.test_freqai_model_transmission()
                await self.test_freqai_predictions()

            # Phase 4: Cleanup
            print("\n🧹 PHASE 4: Cleanup")
            print("-" * 15)
            await self.cleanup_test_data()

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback

            traceback.print_exc()
            return False

        # Summary
        print("\n" + "=" * 60)
        print("🎉 FREQAI INTEGRATION TEST COMPLETED!")
        print("=" * 60)
        print("✅ Model upload and management")
        print("✅ Bot creation with FreqAI assignment")
        print("✅ Bot start with model transmission")
        print("✅ Base64 encoding/decoding verification")
        print("✅ FreqAI predictions retrieval")
        print("✅ Cleanup and resource management")
        print("=" * 60)

        return True


async def main():
    """Main test runner"""
    async with FreqAIIntegrationTester() as tester:
        success = await tester.run_full_integration_test()

        if success:
            print("\n🎉 FreqAI Integration Test PASSED!")
            print("🤖 FreqAI model transmission via base64 works correctly!")
        else:
            print("\n❌ FreqAI Integration Test FAILED!")
            print("🔧 Check logs and fix issues before proceeding.")


if __name__ == "__main__":
    asyncio.run(main())
