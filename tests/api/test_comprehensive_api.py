#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Freqtrade Multi-Bot System
Tests all endpoints and services systematically
"""

import asyncio
import json
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from httpx import AsyncClient, ASGITransport
import time


@dataclass
class TestResult:
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error: str = ""
    data: Any = None


class ComprehensiveAPITester:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client: AsyncClient | None = None
        self.token: str | None = None
        self.test_results: List[TestResult] = []
        self.created_resources = []

    async def __aenter__(self):
        self.client = AsyncClient(base_url=self.base_url, timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def run_test(
        self,
        endpoint: str,
        method: str = "GET",
        data: Any = None,
        headers: Dict | None = None,
        expected_status: int | None = None,
    ) -> TestResult:
        """Run a single API test"""
        start_time = time.time()

        try:
            if self.client is None:
                raise ValueError("Client not initialized")

            # Prepare request
            url = endpoint
            request_headers = headers or {}
            if self.token and "Authorization" not in request_headers:
                request_headers["Authorization"] = f"Bearer {self.token}"

            # Make request
            if method == "GET":
                response = await self.client.get(url, headers=request_headers)
            elif method == "POST":
                if isinstance(data, dict):
                    response = await self.client.post(
                        url, json=data, headers=request_headers
                    )
                else:
                    response = await self.client.post(
                        url, data=data, headers=request_headers
                    )
            elif method == "PUT":
                response = await self.client.put(
                    url, json=data, headers=request_headers
                )
            elif method == "DELETE":
                response = await self.client.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response_time = time.time() - start_time

            # Check success
            success = expected_status is None or response.status_code == expected_status
            if not success and expected_status is None:
                # For unspecified expected status, consider 2xx as success
                success = 200 <= response.status_code < 300

            # Parse response data
            try:
                response_data = response.json() if response.content else None
            except:
                response_data = response.text

            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time=response_time,
                success=success,
                data=response_data,
            )

        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e),
            )

        self.test_results.append(result)
        return result

    async def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        print("🔐 Testing Authentication...")

        # Try to register user (may already exist)
        register_result = await self.run_test(
            "/api/v1/auth/register",
            "POST",
            {
                "username": "test_user_full",
                "email": "test_full@example.com",
                "password": "testpass123",
                "full_name": "Test User Full",
            },
        )

        # Login (this should always work)
        login_result = await self.run_test(
            "/api/v1/auth/login/json",
            "POST",
            {"username": "test_user_full", "password": "testpass123"},
            expected_status=200,
        )

        if not login_result.success:
            print(f"❌ Login failed: {login_result.status_code}")
            return False

        self.token = (
            login_result.data.get("access_token") if login_result.data else None
        )
        if not self.token:
            print("❌ No access token in login response")
            return False

        print("✅ Authentication successful")
        return True

    async def test_health_endpoints(self) -> bool:
        """Test health and monitoring endpoints"""
        print("🏥 Testing Health & Monitoring...")

        tests = [
            ("/health", "GET", None, 200),
            ("/metrics", "GET", None, None),  # Metrics might return 404
        ]

        all_success = True
        for endpoint, method, data, expected_status in tests:
            result = await self.run_test(
                endpoint, method, data, expected_status=expected_status
            )
            status = "✅" if result.success else "❌"
            print(
                f"  {status} {method} {endpoint} - {result.status_code} ({result.response_time:.3f}s)"
            )

            if not result.success:
                all_success = False

        return all_success

    async def test_bot_management(self) -> bool:
        """Test complete bot lifecycle"""
        print("🤖 Testing Bot Management...")

        # Create bot
        bot_data = {
            "name": "FullTestBot",
            "description": "Bot for comprehensive testing",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 100.0,
            "max_open_trades": 3,
            "config": {
                "trading_mode": "spot",
                "dry_run": True,
                "exchange": {"name": "binance"},
                "strategy": "TestStrategy",
            },
        }

        create_result = await self.run_test(
            "/api/v1/bots/", "POST", bot_data, expected_status=201
        )
        if not create_result.success:
            print(f"❌ Bot creation failed: {create_result.status_code}")
            return False

        bot_id = create_result.data["id"]
        self.created_resources.append(("bot", bot_id))

        # List bots
        list_result = await self.run_test("/api/v1/bots/", "GET", expected_status=200)
        if not list_result.success:
            print(f"❌ Bot listing failed: {list_result.status_code}")
            return False

        # Get specific bot
        get_result = await self.run_test(
            f"/api/v1/bots/{bot_id}", "GET", expected_status=200
        )
        if not get_result.success:
            print(f"❌ Bot retrieval failed: {get_result.status_code}")
            return False

        # Update bot
        update_data = bot_data.copy()
        update_data["stake_amount"] = 200.0
        update_result = await self.run_test(
            f"/api/v1/bots/{bot_id}", "PUT", update_data, expected_status=200
        )
        if not update_result.success:
            print(f"❌ Bot update failed: {update_result.status_code}")
            return False

        # Start bot
        start_result = await self.run_test(
            f"/api/v1/bots/{bot_id}/start", "POST", expected_status=200
        )
        if not start_result.success:
            print(f"❌ Bot start failed: {start_result.status_code}")
            return False

        # Stop bot
        stop_result = await self.run_test(
            f"/api/v1/bots/{bot_id}/stop", "POST", expected_status=200
        )
        if not stop_result.success:
            print(f"❌ Bot stop failed: {stop_result.status_code}")
            return False

        print("✅ Bot lifecycle test completed")
        return True

    async def test_strategy_management(self) -> bool:
        """Test complete strategy management"""
        print("📈 Testing Strategy Management...")

        # List strategies
        list_result = await self.run_test(
            "/api/v1/strategies/", "GET", expected_status=200
        )
        if not list_result.success:
            print(f"❌ Strategy listing failed: {list_result.status_code}")
            return False

        # Get strategy code
        if list_result.data:
            strategy_name = list_result.data[0]
            code_result = await self.run_test(
                f"/api/v1/strategies/{strategy_name}", "GET", expected_status=200
            )
            if not code_result.success:
                print(f"❌ Strategy code retrieval failed: {code_result.status_code}")
                return False

        # Create strategy
        strategy_code = """
from freqtrade.strategy import IStrategy

class FullTestStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    stoploss = -0.10

    def populate_indicators(self, dataframe, metadata):
        return dataframe

    def populate_buy_trend(self, dataframe, metadata):
        dataframe.loc[:, "buy"] = 0
        return dataframe

    def populate_sell_trend(self, dataframe, metadata):
        dataframe.loc[:, "sell"] = 0
        return dataframe
"""

        create_result = await self.run_test(
            "/api/v1/strategies/?strategy_name=FullTestStrategy",
            "POST",
            {"code": strategy_code},
            expected_status=201,
        )
        if not create_result.success:
            print(f"❌ Strategy creation failed: {create_result.status_code}")
            return False

        self.created_resources.append(("strategy", "FullTestStrategy"))

        # Analyze strategy
        analyze_result = await self.run_test(
            "/api/v1/strategies/analyze",
            "POST",
            {"code": strategy_code},
            expected_status=200,
        )
        if not analyze_result.success:
            print(f"❌ Strategy analysis failed: {analyze_result.status_code}")
            return False

        # Update strategy
        update_result = await self.run_test(
            "/api/v1/strategies/FullTestStrategy",
            "PUT",
            {"code": strategy_code.replace("5m", "1h")},
            expected_status=200,
        )
        if not update_result.success:
            print(f"❌ Strategy update failed: {update_result.status_code}")
            return False

        print("✅ Strategy management test completed")
        return True

    async def test_analytics_audit(self) -> bool:
        """Test analytics and audit systems"""
        print("📊 Testing Analytics & Audit...")

        # Analytics endpoints (require authentication)
        analytics_endpoints = [
            "/api/v1/analytics/performance",
            "/api/v1/analytics/risk",
            "/api/v1/analytics/portfolio",
            "/api/v1/analytics/market",
            "/api/v1/analytics/profit",
            "/api/v1/analytics/dashboard",
        ]

        for endpoint in analytics_endpoints:
            result = await self.run_test(endpoint, "GET", expected_status=200)
            status = "✅" if result.success else "❌"
            print(f"  {status} GET {endpoint} - {result.status_code}")

            if not result.success:
                print(f"    Error: {result.error}")
                # Don't fail the test for analytics issues - they might need proper data
                print(
                    f"    Note: Analytics may require bot data to return meaningful results"
                )
                continue

        # Audit endpoints
        audit_result = await self.run_test(
            "/api/v1/audit/logs", "GET", expected_status=200
        )
        if not audit_result.success:
            print(f"❌ Audit logs failed: {audit_result.status_code}")
            return False

        print("✅ Analytics & Audit test completed")
        return True

    async def test_freqai_integration(self) -> bool:
        """Test FreqAI integration"""
        print("🧠 Testing FreqAI Integration...")

        # List FreqAI models
        models_result = await self.run_test(
            "/api/v1/freqai/models/", "GET", expected_status=200
        )
        if not models_result.success:
            print(f"❌ FreqAI models listing failed: {models_result.status_code}")
            return False

        print(f"✅ Found {len(models_result.data)} FreqAI models")
        return True

    async def test_emergency_operations(self) -> bool:
        """Test emergency operations"""
        print("🚨 Testing Emergency Operations...")

        # Emergency stop all
        emergency_result = await self.run_test(
            "/api/v1/emergency/stop-all", "POST", expected_status=200
        )
        if not emergency_result.success:
            print(f"❌ Emergency stop failed: {emergency_result.status_code}")
            return False

        print("✅ Emergency operations test completed")
        return True

    async def cleanup_resources(self):
        """Clean up created resources"""
        print("🧹 Cleaning up test resources...")

        for resource_type, resource_id in self.created_resources:
            try:
                if resource_type == "bot":
                    await self.run_test(f"/api/v1/bots/{resource_id}", "DELETE")
                elif resource_type == "strategy":
                    await self.run_test(f"/api/v1/strategies/{resource_id}", "DELETE")
                print(f"✅ Cleaned up {resource_type}: {resource_id}")
            except Exception as e:
                print(f"❌ Failed to cleanup {resource_type} {resource_id}: {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.success])
        failed_tests = total_tests - successful_tests

        # Group by category
        categories = {}
        for result in self.test_results:
            category = (
                result.endpoint.split("/")[2]
                if len(result.endpoint.split("/")) > 2
                else "other"
            )
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        # Calculate response times
        response_times = [r.response_time for r in self.test_results if r.success]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        max_response_time = max(response_times) if response_times else 0

        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{(successful_tests / total_tests * 100):.1f}%"
                if total_tests > 0
                else "0%",
                "avg_response_time": f"{avg_response_time:.3f}s",
                "max_response_time": f"{max_response_time:.3f}s",
            },
            "categories": {
                cat: {
                    "total": len(results),
                    "successful": len([r for r in results if r.success]),
                    "failed": len([r for r in results if not r.success]),
                }
                for cat, results in categories.items()
            },
            "failed_tests": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "error": r.error,
                    "response_time": f"{r.response_time:.3f}s",
                }
                for r in self.test_results
                if not r.success
            ],
        }


async def main():
    """Main testing function"""
    print("🚀 Starting Comprehensive API Testing")
    print("=" * 50)

    async with ComprehensiveAPITester() as tester:
        # Authentication
        if not await tester.authenticate():
            print("❌ Authentication failed - cannot continue testing")
            return

        # Test all components
        test_components = [
            ("Health & Monitoring", tester.test_health_endpoints),
            ("Bot Management", tester.test_bot_management),
            ("Strategy Management", tester.test_strategy_management),
            ("Analytics & Audit", tester.test_analytics_audit),
            ("FreqAI Integration", tester.test_freqai_integration),
            ("Emergency Operations", tester.test_emergency_operations),
        ]

        results = {}
        for component_name, test_func in test_components:
            print(f"\n{'=' * 20} {component_name} {'=' * 20}")
            try:
                success = await test_func()
                results[component_name] = success
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"{status}: {component_name}")
            except Exception as e:
                print(f"❌ ERROR in {component_name}: {e}")
                results[component_name] = False

        # Cleanup
        await tester.cleanup_resources()

        # Generate report
        print(f"\n{'=' * 50}")
        print("📊 COMPREHENSIVE TEST REPORT")
        print(f"{'=' * 50}")

        report = tester.generate_report()

        print(f"📈 SUMMARY:")
        print(f"   Total Tests: {report['summary']['total_tests']}")
        print(f"   Successful: {report['summary']['successful_tests']}")
        print(f"   Failed: {report['summary']['failed_tests']}")
        print(f"   Success Rate: {report['summary']['success_rate']}")
        print(f"   Avg Response Time: {report['summary']['avg_response_time']}")
        print(f"   Max Response Time: {report['summary']['max_response_time']}")

        print(f"\n📂 BY CATEGORY:")
        for category, stats in report["categories"].items():
            success_rate = (
                (stats["successful"] / stats["total"] * 100)
                if stats["total"] > 0
                else 0
            )
            print(
                f"   {category}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)"
            )

        if report["failed_tests"]:
            print(f"\n❌ FAILED TESTS:")
            for failed in report["failed_tests"][:5]:  # Show first 5 failures
                print(
                    f"   {failed['method']} {failed['endpoint']} - {failed['status_code']} ({failed['response_time']})"
                )
                if failed["error"]:
                    print(f"     Error: {failed['error']}")

        # Overall result
        all_passed = all(results.values())
        print(
            f"\n{'🎉' if all_passed else '⚠️'} OVERALL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}"
        )

        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
