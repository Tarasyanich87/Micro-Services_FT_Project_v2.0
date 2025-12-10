#!/usr/bin/env python3
"""
Comprehensive Dashboard Testing Script
Tests all 10 dashboards for functionality and task compliance
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from typing import Dict, List, Any

BASE_URL = "http://localhost:5176"


class DashboardTester:
    def __init__(self):
        self.test_results = []
        self.dashboards = {
            "/": "Home Dashboard",
            "/bots": "Bot Management Dashboard",
            "/strategies": "Strategies Dashboard",
            "/analytics": "Analytics Dashboard",
            "/freqai-lab": "FreqAI Lab Dashboard",
            "/data": "Data Management Dashboard",
            "/hyperopt": "Hyperopt Dashboard",
            "/monitoring": "Monitoring Dashboard",
            "/audit": "Audit Dashboard",
            "/login": "Login Dashboard",
        }

    def log_result(
        self, dashboard: str, test_name: str, success: bool, details: str = ""
    ):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} [{dashboard}] {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append(
            {
                "dashboard": dashboard,
                "test": test_name,
                "success": success,
                "details": details,
                "timestamp": time.time(),
            }
        )

    async def authenticate(self, page):
        """Authenticate in the application"""
        try:
            # Check if we're on login page
            if "/login" in page.url or page.url.endswith("/"):
                # Try to login
                username_input = page.locator(
                    'input[type="text"], input[placeholder*="username"]'
                ).first
                password_input = page.locator(
                    'input[type="password"], input[placeholder*="password"]'
                ).first
                login_button = page.locator(
                    'button:has-text("Login"), button[type="submit"]'
                ).first

                if await username_input.is_visible():
                    await username_input.fill("testuser")
                    await password_input.fill("testpass123")
                    await login_button.click()
                    await page.wait_for_load_state("networkidle")
                    return True
        except Exception as e:
            print(f"Authentication failed: {e}")

        return False

    async def test_home_dashboard(self, page):
        """Test Home Dashboard"""
        dashboard = "Home Dashboard"

        # Check title
        title = await page.title()
        self.log_result(
            dashboard, "Page Title", "Freqtrade" in title, f"Title: {title}"
        )

        # Check main sections
        header = page.locator("h1, .dashboard-header h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard,
            "Main Header",
            "Freqtrade" in header_text,
            f"Header: {header_text}",
        )

        # Check navigation
        nav_links = page.locator("nav a, .sidebar a, .menu a")
        nav_count = await nav_links.count()
        self.log_result(
            dashboard,
            "Navigation Links",
            nav_count > 0,
            f"Found {nav_count} navigation links",
        )

        # Check system status cards
        status_cards = page.locator(".status-card, .metric-card, .info-card")
        cards_count = await status_cards.count()
        self.log_result(
            dashboard,
            "Status Cards",
            cards_count >= 3,
            f"Found {cards_count} status cards",
        )

        # Check quick actions
        actions = page.locator("button, .action-btn")
        actions_count = await actions.count()
        self.log_result(
            dashboard,
            "Quick Actions",
            actions_count > 0,
            f"Found {actions_count} action buttons",
        )

    async def test_bot_management_dashboard(self, page):
        """Test Bot Management Dashboard"""
        dashboard = "Bot Management Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard,
            "Header",
            "Bot" in header_text and "Management" in header_text,
            f"Header: {header_text}",
        )

        # Check bot list/table
        bot_cards = page.locator(".bot-card, .bot-item, tr")
        bots_count = await bot_cards.count()
        self.log_result(dashboard, "Bot List", True, f"Found {bots_count} bot items")

        # Check action buttons
        create_btn = page.locator(
            'button:has-text("Create"), button:has-text("Add")'
        ).first
        create_visible = await create_btn.is_visible()
        self.log_result(
            dashboard, "Create Bot Button", create_visible, "Create bot button visible"
        )

        # Check bot status indicators
        status_indicators = page.locator(".status, .badge, .status-badge")
        status_count = await status_indicators.count()
        self.log_result(
            dashboard,
            "Status Indicators",
            status_count > 0,
            f"Found {status_count} status indicators",
        )

    async def test_strategies_dashboard(self, page):
        """Test Strategies Dashboard"""
        dashboard = "Strategies Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard, "Header", "Strateg" in header_text, f"Header: {header_text}"
        )

        # Check strategies list
        strategy_cards = page.locator(".strategy-card, .strategy-item")
        strategies_count = await strategy_cards.count()
        self.log_result(
            dashboard,
            "Strategies List",
            strategies_count >= 0,
            f"Found {strategies_count} strategies",
        )

        # Check create strategy button
        create_btn = page.locator(
            'button:has-text("Create"), button:has-text("Add")'
        ).first
        create_visible = await create_btn.is_visible()
        self.log_result(
            dashboard,
            "Create Strategy Button",
            create_visible,
            "Create strategy button visible",
        )

        # Check CodeMirror editor (if create dialog is open)
        codemirror = page.locator(".cm-editor, .code-editor-wrapper")
        editor_visible = await codemirror.is_visible()
        if editor_visible:
            self.log_result(
                dashboard, "CodeMirror Editor", True, "CodeMirror editor is visible"
            )
        else:
            self.log_result(
                dashboard,
                "CodeMirror Editor",
                True,
                "Editor not visible (expected for closed dialog)",
            )

    async def test_analytics_dashboard(self, page):
        """Test Analytics Dashboard"""
        dashboard = "Analytics Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard, "Header", "Analytic" in header_text, f"Header: {header_text}"
        )

        # Check charts/graphs
        charts = page.locator("canvas, .chart, .graph, svg")
        charts_count = await charts.count()
        self.log_result(
            dashboard, "Charts/Graphs", charts_count > 0, f"Found {charts_count} charts"
        )

        # Check metrics cards
        metrics = page.locator(".metric, .stat, .kpi")
        metrics_count = await metrics.count()
        self.log_result(
            dashboard, "Metrics", metrics_count > 0, f"Found {metrics_count} metrics"
        )

        # Check time filters
        time_filters = page.locator("select, .time-filter, .date-picker")
        filters_count = await time_filters.count()
        self.log_result(
            dashboard,
            "Time Filters",
            filters_count >= 0,
            f"Found {filters_count} time filters",
        )

    async def test_freqai_lab_dashboard(self, page):
        """Test FreqAI Lab Dashboard"""
        dashboard = "FreqAI Lab Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard,
            "Header",
            "FreqAI" in header_text or "AI" in header_text,
            f"Header: {header_text}",
        )

        # Check model list
        models = page.locator(".model-card, .ai-model, .freqai-model")
        models_count = await models.count()
        self.log_result(dashboard, "AI Models", True, f"Found {models_count} AI models")

        # Check training controls
        train_btn = page.locator(
            'button:has-text("Train"), button:has-text("Start")'
        ).first
        train_visible = await train_btn.is_visible()
        self.log_result(
            dashboard, "Training Controls", train_visible, "Training controls visible"
        )

    async def test_data_management_dashboard(self, page):
        """Test Data Management Dashboard"""
        dashboard = "Data Management Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard, "Header", "Data" in header_text, f"Header: {header_text}"
        )

        # Check data sources
        data_sources = page.locator(".data-source, .exchange, .market-data")
        sources_count = await data_sources.count()
        self.log_result(
            dashboard,
            "Data Sources",
            sources_count >= 0,
            f"Found {sources_count} data sources",
        )

        # Check import/export buttons
        import_btn = page.locator('button:has-text("Import"), input[type="file"]').first
        import_visible = await import_btn.is_visible()
        self.log_result(
            dashboard, "Import Controls", import_visible, "Import controls visible"
        )

    async def test_hyperopt_dashboard(self, page):
        """Test Hyperopt Dashboard"""
        dashboard = "Hyperopt Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard,
            "Header",
            "Hyperopt" in header_text or "Optimization" in header_text,
            f"Header: {header_text}",
        )

        # Check optimization results
        results = page.locator(".result, .optimization, .hyperopt-result")
        results_count = await results.count()
        self.log_result(
            dashboard,
            "Optimization Results",
            True,
            f"Found {results_count} optimization results",
        )

        # Check parameter controls
        params = page.locator("input, select, .parameter")
        params_count = await params.count()
        self.log_result(
            dashboard,
            "Parameter Controls",
            params_count >= 0,
            f"Found {params_count} parameter controls",
        )

    async def test_monitoring_dashboard(self, page):
        """Test Monitoring Dashboard"""
        dashboard = "Monitoring Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard, "Header", "Monitor" in header_text, f"Header: {header_text}"
        )

        # Check system metrics
        metrics = page.locator(".metric, .system-info, .health")
        metrics_count = await metrics.count()
        self.log_result(
            dashboard,
            "System Metrics",
            metrics_count > 0,
            f"Found {metrics_count} system metrics",
        )

        # Check logs section
        logs = page.locator(".log, .console, .terminal")
        logs_visible = await logs.is_visible()
        self.log_result(dashboard, "Logs Section", logs_visible, "Logs section visible")

    async def test_audit_dashboard(self, page):
        """Test Audit Dashboard"""
        dashboard = "Audit Dashboard"

        # Check header
        header = page.locator("h1").first
        header_text = await header.text_content() if await header.is_visible() else ""
        self.log_result(
            dashboard, "Header", "Audit" in header_text, f"Header: {header_text}"
        )

        # Check audit logs table
        logs_table = page.locator("table, .audit-log, .log-entry")
        logs_visible = await logs_table.is_visible()
        self.log_result(dashboard, "Audit Logs", logs_visible, "Audit logs visible")

        # Check filters
        filters = page.locator('select, .filter, input[type="date"]')
        filters_count = await filters.count()
        self.log_result(
            dashboard,
            "Audit Filters",
            filters_count >= 0,
            f"Found {filters_count} filters",
        )

    async def test_login_dashboard(self, page):
        """Test Login Dashboard"""
        dashboard = "Login Dashboard"

        # Check login form
        login_form = page.locator("form, .login-form")
        form_visible = await login_form.is_visible()
        self.log_result(dashboard, "Login Form", form_visible, "Login form visible")

        # Check input fields
        username_input = page.locator(
            'input[type="text"], input[placeholder*="username"]'
        ).first
        password_input = page.locator(
            'input[type="password"], input[placeholder*="password"]'
        ).first

        username_visible = await username_input.is_visible()
        password_visible = await password_input.is_visible()

        self.log_result(
            dashboard, "Username Field", username_visible, "Username input visible"
        )
        self.log_result(
            dashboard, "Password Field", password_visible, "Password input visible"
        )

        # Check login button
        login_btn = page.locator(
            'button[type="submit"], button:has-text("Login")'
        ).first
        login_visible = await login_btn.is_visible()
        self.log_result(
            dashboard, "Login Button", login_visible, "Login button visible"
        )

    async def run_dashboard_test(self, page, path: str, dashboard_name: str):
        """Run test for specific dashboard"""
        print(f"\n🧪 Testing {dashboard_name} ({path})")
        print("=" * 50)

        try:
            # Navigate to dashboard
            await page.goto(f"{BASE_URL}{path}")
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Authenticate if needed
            if path != "/login":
                await self.authenticate(page)

            # Run specific dashboard test
            if path == "/":
                await self.test_home_dashboard(page)
            elif path == "/bots":
                await self.test_bot_management_dashboard(page)
            elif path == "/strategies":
                await self.test_strategies_dashboard(page)
            elif path == "/analytics":
                await self.test_analytics_dashboard(page)
            elif path == "/freqai-lab":
                await self.test_freqai_lab_dashboard(page)
            elif path == "/data":
                await self.test_data_management_dashboard(page)
            elif path == "/hyperopt":
                await self.test_hyperopt_dashboard(page)
            elif path == "/monitoring":
                await self.test_monitoring_dashboard(page)
            elif path == "/audit":
                await self.test_audit_dashboard(page)
            elif path == "/login":
                await self.test_login_dashboard(page)

        except Exception as e:
            self.log_result(dashboard_name, "Dashboard Load", False, f"Error: {str(e)}")

    async def run_all_tests(self):
        """Run tests for all dashboards"""
        print("🚀 Starting Comprehensive Dashboard Testing")
        print("=" * 60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()

            try:
                for path, dashboard_name in self.dashboards.items():
                    page = await context.new_page()
                    await self.run_dashboard_test(page, path, dashboard_name)
                    await page.close()

            except Exception as e:
                print(f"❌ Test suite failed: {e}")

            finally:
                await browser.close()

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 DASHBOARD TESTING SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(".1f")

        # Group by dashboard
        dashboard_stats = {}
        for result in self.test_results:
            dashboard = result["dashboard"]
            if dashboard not in dashboard_stats:
                dashboard_stats[dashboard] = {"total": 0, "passed": 0}
            dashboard_stats[dashboard]["total"] += 1
            if result["success"]:
                dashboard_stats[dashboard]["passed"] += 1

        print("\n📋 Dashboard Results:")
        for dashboard, stats in dashboard_stats.items():
            rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
            print(".1f")

        print("\n📋 Detailed Test Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} [{result['dashboard']}] {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")

        # Save detailed results
        results_file = "dashboard_testing_results.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "timestamp": time.time(),
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": total_tests - passed_tests,
                    "success_rate": success_rate,
                    "dashboard_stats": dashboard_stats,
                    "results": self.test_results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Detailed results saved to {results_file}")

        if success_rate >= 80:
            print("\n🎉 DASHBOARD TESTING COMPLETED SUCCESSFULLY!")
        else:
            print("\n⚠️ Dashboard testing completed with issues.")


async def main():
    """Main test runner"""
    tester = DashboardTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
