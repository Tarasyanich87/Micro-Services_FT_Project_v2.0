#!/usr/bin/env python3
"""
Strategy UI Testing Script
Tests the strategy management UI functionality including CodeMirror editor
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
import httpx

BASE_URL = "http://localhost:8002"
UI_URL = "http://localhost:5176"


class StrategyUITester:
    def __init__(self):
        self.test_results = []

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

    async def setup_test_data(self):
        """Setup test data via API"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            # Register and login
            await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "ui_tester",
                    "email": "ui@test.com",
                    "password": "testpass123",
                    "full_name": "UI Tester",
                },
            )

            response = await client.post(
                "/api/v1/auth/login/json",
                json={"username": "ui_tester", "password": "testpass123"},
            )
            token = response.json()["access_token"]
            client.headers.update({"Authorization": f"Bearer {token}"})

            # Create a test strategy
            test_strategy_code = '''
from freqtrade.strategy import IStrategy
from typing import Dict, List
import numpy as np
import pandas as pd

class UITestStrategy(IStrategy):
    """
    Test strategy for UI testing
    """

    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.10}
    stoploss = -0.10
    timeframe = '5m'

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe)
        return dataframe

    def populate_buy_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[dataframe['rsi'] < 30, 'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[dataframe['rsi'] > 70, 'sell'] = 1
        return dataframe
'''

            await client.post(
                "/api/v1/strategies/",
                json={"code": test_strategy_code},
                params={"strategy_name": "UITestStrategy"},
            )

            print("✅ Test data setup complete")

    async def run_ui_tests(self):
        """Run UI tests using Playwright"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Navigate to strategies page
                print("🌐 Navigating to Strategies Dashboard...")
                await page.goto(f"{UI_URL}/strategies")
                await page.wait_for_load_state("networkidle")

                # Check if page loaded
                title = await page.title()
                self.log_result(
                    "Page Load", "Strategies" in title, f"Page title: {title}"
                )

                # Check if strategies are displayed
                strategies_list = page.locator(".strategies-grid .strategy-card")
                count = await strategies_list.count()
                self.log_result(
                    "Strategies Display", count > 0, f"Found {count} strategies"
                )

                # Test create strategy dialog
                print("📝 Testing Create Strategy Dialog...")
                create_btn = page.locator('button:has-text("Создать стратегию")')
                await create_btn.click()

                # Wait for dialog
                dialog = page.locator(".modal, .dialog")
                await dialog.wait_for(state="visible", timeout=5000)

                # Check if CodeMirror editor is present
                codemirror = page.locator(".code-editor-wrapper .cm-editor")
                is_visible = await codemirror.is_visible()
                self.log_result(
                    "CodeMirror Editor", is_visible, "CodeMirror editor is visible"
                )

                # Test typing in editor
                if is_visible:
                    # Click on editor to focus
                    await codemirror.click()

                    # Type some code
                    test_code = "print('Hello from CodeMirror!')"
                    await page.keyboard.type(test_code)

                    # Check if code was entered
                    editor_content = await codemirror.text_content()
                    has_code = test_code in editor_content
                    self.log_result(
                        "CodeMirror Typing", has_code, f"Code entered: {has_code}"
                    )

                # Test strategy name input
                name_input = page.locator('#strategyName, input[type="text"]').first
                await name_input.fill("TestStrategyUI")
                name_value = await name_input.input_value()
                self.log_result(
                    "Strategy Name Input",
                    name_value == "TestStrategyUI",
                    f"Name: {name_value}",
                )

                # Test file upload
                file_input = page.locator('input[type="file"][accept=".md"]')
                is_upload_visible = await file_input.is_visible()
                self.log_result(
                    "MD File Upload",
                    is_upload_visible,
                    "File upload input is available",
                )

                # Close dialog without saving
                cancel_btn = page.locator(
                    'button:has-text("Отмена"), button:has-text("Cancel")'
                ).first
                await cancel_btn.click()

                # Test existing strategy editing
                if count > 0:
                    print("✏️ Testing Strategy Editing...")
                    edit_btn = page.locator('button:has-text("Edit")').first
                    await edit_btn.click()

                    # Wait for edit dialog
                    await page.wait_for_timeout(1000)

                    # Check if edit dialog opened
                    edit_dialog = page.locator(".modal, .dialog")
                    edit_visible = await edit_dialog.is_visible()
                    self.log_result("Edit Dialog", edit_visible, "Edit dialog opened")

                    if edit_visible:
                        # Close edit dialog
                        cancel_edit = page.locator(
                            'button:has-text("Отмена"), button:has-text("Cancel")'
                        ).first
                        await cancel_edit.click()

                # Test backtest functionality (if available)
                backtest_btn = page.locator('button:has-text("Бектест")').first
                backtest_exists = await backtest_btn.is_visible()
                self.log_result(
                    "Backtest Button",
                    backtest_exists,
                    "Backtest functionality available",
                )

                if backtest_exists:
                    # Note: Not clicking to avoid actual backtesting
                    self.log_result("Backtest UI", True, "Backtest UI elements present")

                print("🎉 UI Testing Complete!")

            except Exception as e:
                self.log_result("UI Test Error", False, str(e))
                print(f"❌ UI Test failed: {e}")

            finally:
                await browser.close()

    async def run_full_test(self):
        """Run complete strategy UI test"""
        print("🚀 Starting Strategy UI Testing")
        print("=" * 50)

        # Setup test data
        await self.setup_test_data()

        # Run UI tests
        await self.run_ui_tests()

        # Summary
        print("\n" + "=" * 50)
        print("📊 STRATEGY UI TEST SUMMARY")
        print("=" * 50)

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

        # Save results
        results_file = "strategy_ui_test_results.json"
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

        print(f"\n💾 Results saved to {results_file}")

        return success_rate >= 80


async def main():
    """Main test runner"""
    tester = StrategyUITester()
    success = await tester.run_full_test()

    if success:
        print("\n🎉 Strategy UI Test COMPLETED SUCCESSFULLY!")
    else:
        print("\n⚠️ Strategy UI Test completed with issues.")


if __name__ == "__main__":
    asyncio.run(main())
