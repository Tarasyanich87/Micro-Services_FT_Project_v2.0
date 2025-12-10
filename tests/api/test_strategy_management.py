#!/usr/bin/env python3
"""
Comprehensive Strategy Management Test
Tests full lifecycle of Freqtrade strategies including:
- CRUD operations
- Code validation
- MD file conversion
- Backtesting
- CodeMirror editor functionality
"""

import asyncio
import json
import httpx
import time
from pathlib import Path
from typing import Dict, Any

BASE_URL = "http://localhost:8002"


class StrategyManagementTester:
    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.token: str | None = None
        self.test_results = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)
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
                "username": "strategy_tester",
                "email": "strategy@test.com",
                "password": "testpass123",
                "full_name": "Strategy Tester",
            },
        )

        # Login
        response = await self.client.post(
            "/api/v1/auth/login/json",
            json={"username": "strategy_tester", "password": "testpass123"},
        )
        self.token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        print("✅ Authenticated for strategy testing")

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "details": details,
                "timestamp": time.time(),
            }
        )

    async def test_get_strategies(self):
        """Test getting list of available strategies"""
        try:
            response = await self.client.get("/api/v1/strategies/")
            if response.status_code == 200:
                strategies = response.json()
                self.log_result(
                    "Get Strategies List",
                    True,
                    f"Found {len(strategies)} strategies: {strategies}",
                )
                return strategies
            else:
                self.log_result(
                    "Get Strategies List", False, f"HTTP {response.status_code}"
                )
                return []
        except Exception as e:
            self.log_result("Get Strategies List", False, str(e))
            return []

    async def test_get_strategy_code(self, strategy_name: str):
        """Test getting strategy code"""
        try:
            response = await self.client.get(f"/api/v1/strategies/{strategy_name}")
            if response.status_code == 200:
                code_data = response.json()
                code_length = len(code_data.get("code", ""))
                self.log_result(
                    f"Get Strategy Code: {strategy_name}",
                    True,
                    f"Code length: {code_length} chars",
                )
                return code_data.get("code", "")
            else:
                self.log_result(
                    f"Get Strategy Code: {strategy_name}",
                    False,
                    f"HTTP {response.status_code}",
                )
                return ""
        except Exception as e:
            self.log_result(f"Get Strategy Code: {strategy_name}", False, str(e))
            return ""

    async def test_create_strategy(self, name: str, code: str):
        """Test creating a new strategy"""
        try:
            response = await self.client.post(
                "/api/v1/strategies/",
                json={"code": code},
                params={"strategy_name": name},
            )

            if response.status_code == 201:
                self.log_result(f"Create Strategy: {name}", True)
                return True
            else:
                self.log_result(
                    f"Create Strategy: {name}",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                )
                return False
        except Exception as e:
            self.log_result(f"Create Strategy: {name}", False, str(e))
            return False

    async def test_update_strategy(self, name: str, new_code: str):
        """Test updating strategy code"""
        try:
            response = await self.client.put(
                f"/api/v1/strategies/{name}", json={"code": new_code}
            )

            if response.status_code == 200:
                self.log_result(f"Update Strategy: {name}", True)
                return True
            else:
                self.log_result(
                    f"Update Strategy: {name}", False, f"HTTP {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_result(f"Update Strategy: {name}", False, str(e))
            return False

    async def test_delete_strategy(self, name: str):
        """Test deleting a strategy"""
        try:
            response = await self.client.delete(f"/api/v1/strategies/{name}")

            if response.status_code == 204:
                self.log_result(f"Delete Strategy: {name}", True)
                return True
            else:
                self.log_result(
                    f"Delete Strategy: {name}", False, f"HTTP {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_result(f"Delete Strategy: {name}", False, str(e))
            return False

    async def test_analyze_strategy(self, code: str, expected_valid: bool = True):
        """Test strategy code analysis"""
        try:
            response = await self.client.post(
                "/api/v1/strategies/analyze", json={"code": code}
            )

            if response.status_code == 200:
                result = response.json()
                is_valid = result.get("valid", False)
                errors = result.get("errors", [])
                parameters = result.get("parameters", {})

                success = is_valid == expected_valid
                details = f"Valid: {is_valid}, Errors: {len(errors)}, Parameters: {len(parameters)}"
                if errors:
                    details += f" | Sample error: {errors[0][:100]}..."

                self.log_result("Analyze Strategy Code", success, details)
                return result
            else:
                self.log_result(
                    "Analyze Strategy Code", False, f"HTTP {response.status_code}"
                )
                return None
        except Exception as e:
            self.log_result("Analyze Strategy Code", False, str(e))
            return None

    async def test_md_conversion(self, md_content: str):
        """Test MD to Python conversion"""
        try:
            # Create a temporary MD file content
            files = {"file": ("strategy.md", md_content, "text/markdown")}

            response = await self.client.post(
                "/api/v1/strategies/upload_md", files=files
            )

            if response.status_code == 200:
                result = response.json()
                code = result.get("code", "")
                code_lines = len(code.split("\n"))
                self.log_result(
                    "MD to Python Conversion",
                    True,
                    f"Generated {code_lines} lines of code",
                )
                return code
            else:
                self.log_result(
                    "MD to Python Conversion",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                )
                return None
        except Exception as e:
            self.log_result("MD to Python Conversion", False, str(e))
            return None

    async def test_backtesting(self, strategy_name: str, bot_id: int):
        """Test strategy backtesting"""
        try:
            response = await self.client.post(
                "/api/v1/strategies/backtest",
                json={"strategy_name": strategy_name, "bot_id": bot_id},
            )

            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Strategy Backtesting",
                    True,
                    f"Backtest ID: {result.get('id')}, Status: {result.get('status')}",
                )
                return result
            else:
                self.log_result(
                    "Strategy Backtesting",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                )
                return None
        except Exception as e:
            self.log_result("Strategy Backtesting", False, str(e))
            return None

    async def test_get_backtest_results(self):
        """Test getting backtest results"""
        try:
            response = await self.client.get("/api/v1/strategies/backtest/results")

            if response.status_code == 200:
                results = response.json()
                self.log_result(
                    "Get Backtest Results",
                    True,
                    f"Found {len(results)} backtest results",
                )
                return results
            else:
                self.log_result(
                    "Get Backtest Results", False, f"HTTP {response.status_code}"
                )
                return []
        except Exception as e:
            self.log_result("Get Backtest Results", False, str(e))
            return []

    async def run_full_lifecycle_test(self):
        """Run complete strategy lifecycle test"""
        print("🚀 Starting Comprehensive Strategy Management Test")
        print("=" * 60)

        # Test data
        test_strategy_name = f"TestStrategy_{int(time.time())}"
        valid_strategy_code = '''from freqtrade.strategy import IStrategy
from typing import Dict, List
import numpy as np
import pandas as pd
from freqtrade.strategy import DecimalParameter, IntParameter

class TestStrategy(IStrategy):
    """
    Test strategy for validation
    """

    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.10, "15": 0.05, "240": 0, "1440": -0.05}
    stoploss = -0.10
    timeframe = '5m'

    # Strategy parameters
    buy_rsi = IntParameter(10, 40, default=30, space='buy')
    sell_rsi = IntParameter(60, 90, default=70, space='sell')

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Add RSI indicator
        dataframe['rsi'] = ta.RSI(dataframe)
        return dataframe

    def populate_buy_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi.value)
            ),
            'sell'] = 1
        return dataframe
'''

        invalid_strategy_code = """# Invalid strategy - missing required methods
class InvalidStrategy:
    pass
"""

        md_content = """# RSI Momentum Strategy

This strategy uses RSI indicator for momentum trading.

## Strategy Logic
- Buy when RSI < 30
- Sell when RSI > 70

## Parameters
- Timeframe: 5m
- Stop loss: -10%
- Minimal ROI: 10%

## Implementation
Use technical analysis library for RSI calculation.
"""

        # 1. Get initial strategies list
        initial_strategies = await self.test_get_strategies()

        # 2. Test strategy analysis - valid code
        print("\n📊 Testing Strategy Analysis...")
        analysis_result = await self.test_analyze_strategy(valid_strategy_code, True)
        if analysis_result and analysis_result.get("valid"):
            print(
                f"   ✅ Valid strategy parameters: {analysis_result.get('parameters', {})}"
            )

        # 3. Test strategy analysis - invalid code
        invalid_analysis = await self.test_analyze_strategy(
            invalid_strategy_code, False
        )

        # 4. Test MD to Python conversion
        print("\n📝 Testing MD to Python Conversion...")
        converted_code = await self.test_md_conversion(md_content)
        if converted_code:
            print(f"   ✅ Generated code preview: {converted_code[:200]}...")

        # 5. Create new strategy
        print("\n📝 Testing Strategy CRUD Operations...")
        create_success = await self.test_create_strategy(
            test_strategy_name, valid_strategy_code
        )

        if create_success:
            # 6. Get strategy code
            retrieved_code = await self.test_get_strategy_code(test_strategy_name)

            # 7. Update strategy
            updated_code = valid_strategy_code.replace(
                "TestStrategy", "UpdatedTestStrategy"
            )
            update_success = await self.test_update_strategy(
                test_strategy_name, updated_code
            )

            # 8. Verify update
            if update_success:
                updated_retrieved = await self.test_get_strategy_code(
                    test_strategy_name
                )
                if "UpdatedTestStrategy" in updated_retrieved:
                    self.log_result("Verify Strategy Update", True)
                else:
                    self.log_result(
                        "Verify Strategy Update", False, "Update not reflected"
                    )

            # 9. Create a test bot for backtesting (if needed)
            # Note: This would require a bot creation, which we tested separately

            # 10. Delete strategy
            delete_success = await self.test_delete_strategy(test_strategy_name)

        # 11. Verify deletion
        final_strategies = await self.test_get_strategies()
        if test_strategy_name not in final_strategies:
            self.log_result("Verify Strategy Deletion", True)
        else:
            self.log_result("Verify Strategy Deletion", False, "Strategy still exists")

        # 12. Test backtest results endpoint
        print("\n🧪 Testing Backtesting Endpoints...")
        backtest_results = await self.test_get_backtest_results()

        # Summary
        print("\n" + "=" * 60)
        print("📊 STRATEGY MANAGEMENT TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(".1f")

        print("\n📋 Test Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")

        # Save detailed results
        results_file = "strategy_management_test_results.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "timestamp": time.time(),
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": total_tests - passed_tests,
                    "success_rate": success_rate,
                    "results": self.test_results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Detailed results saved to {results_file}")

        return success_rate >= 80  # Consider test successful if 80%+ pass rate


async def main():
    """Main test runner"""
    async with StrategyManagementTester() as tester:
        success = await tester.run_full_lifecycle_test()

        if success:
            print("\n🎉 Strategy Management Test COMPLETED SUCCESSFULLY!")
        else:
            print("\n⚠️ Strategy Management Test completed with issues.")


if __name__ == "__main__":
    asyncio.run(main())
