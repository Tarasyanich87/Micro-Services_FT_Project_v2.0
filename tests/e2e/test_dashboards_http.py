#!/usr/bin/env python3
"""
Dashboard Availability Test - HTTP-based testing without browser
Tests all dashboard routes for HTTP availability and basic content
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List, Any

BASE_URL = "http://localhost:5176"


class DashboardHTTPTester:
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

    async def test_dashboard_route(self, path: str, dashboard_name: str):
        """Test dashboard route availability"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{BASE_URL}{path}")

                # Check HTTP status
                status_ok = response.status_code in [200, 304]
                self.log_result(
                    dashboard_name,
                    "HTTP Status",
                    status_ok,
                    f"Status: {response.status_code}",
                )

                if status_ok:
                    # Check content type
                    content_type = response.headers.get("content-type", "")
                    is_html = "text/html" in content_type
                    self.log_result(
                        dashboard_name,
                        "Content Type",
                        is_html,
                        f"Content-Type: {content_type}",
                    )

                    # Check content length
                    content_length = len(response.text)
                    has_content = (
                        content_length > 1000
                    )  # Reasonable minimum for a dashboard
                    self.log_result(
                        dashboard_name,
                        "Content Length",
                        has_content,
                        f"Length: {content_length} chars",
                    )

                    # Check for key dashboard elements in HTML
                    html_content = response.text.lower()

                    # Common checks for all dashboards
                    has_vue = "vue" in html_content or "vue-router" in html_content
                    self.log_result(
                        dashboard_name, "Vue Framework", has_vue, "Vue.js detected"
                    )

                    # Dashboard-specific checks
                    if path == "/":
                        has_title = "freqtrade" in html_content
                        self.log_result(
                            dashboard_name,
                            "Home Title",
                            has_title,
                            "Freqtrade branding found",
                        )

                    elif path == "/bots":
                        has_bot_elements = (
                            "bot" in html_content or "management" in html_content
                        )
                        self.log_result(
                            dashboard_name,
                            "Bot Elements",
                            has_bot_elements,
                            "Bot-related content found",
                        )

                    elif path == "/strategies":
                        has_strategy_elements = (
                            "strategy" in html_content or "code" in html_content
                        )
                        self.log_result(
                            dashboard_name,
                            "Strategy Elements",
                            has_strategy_elements,
                            "Strategy-related content found",
                        )

                    elif path == "/analytics":
                        has_chart_elements = (
                            "chart" in html_content or "analytics" in html_content
                        )
                        self.log_result(
                            dashboard_name,
                            "Analytics Elements",
                            has_chart_elements,
                            "Analytics content found",
                        )

                    elif path == "/login":
                        has_login_elements = (
                            "login" in html_content or "auth" in html_content
                        )
                        self.log_result(
                            dashboard_name,
                            "Login Elements",
                            has_login_elements,
                            "Login form elements found",
                        )

                    # Check for common UI elements
                    has_navigation = "nav" in html_content or "menu" in html_content
                    self.log_result(
                        dashboard_name,
                        "Navigation",
                        has_navigation,
                        "Navigation elements found",
                    )

                    has_buttons = "button" in html_content
                    self.log_result(
                        dashboard_name,
                        "Action Buttons",
                        has_buttons,
                        "Interactive buttons found",
                    )

                else:
                    self.log_result(
                        dashboard_name,
                        "Response Body",
                        False,
                        f"Error response: {response.text[:200]}...",
                    )

        except Exception as e:
            self.log_result(dashboard_name, "HTTP Request", False, f"Error: {str(e)}")

    async def run_all_tests(self):
        """Run HTTP availability tests for all dashboards"""
        print("🌐 Starting Dashboard HTTP Availability Testing")
        print("=" * 60)

        for path, dashboard_name in self.dashboards.items():
            print(f"\n🧪 Testing {dashboard_name} ({path})")
            print("-" * 40)
            await self.test_dashboard_route(path, dashboard_name)

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 DASHBOARD HTTP TESTING SUMMARY")
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

        print("\n📋 Critical Findings:")

        # Check for critical issues
        critical_issues = []
        for result in self.test_results:
            if not result["success"] and "HTTP Status" in result["test"]:
                critical_issues.append(
                    f"❌ {result['dashboard']}: HTTP {result['details']}"
                )

        if critical_issues:
            print("🚨 HTTP Availability Issues:")
            for issue in critical_issues:
                print(f"   {issue}")
        else:
            print("✅ All dashboards are HTTP accessible")

        # Check for content issues
        content_issues = []
        for result in self.test_results:
            if not result["success"] and "Content" in result["test"]:
                content_issues.append(
                    f"⚠️ {result['dashboard']}: {result['test']} - {result['details']}"
                )

        if content_issues:
            print("\n⚠️ Content Issues:")
            for issue in content_issues[:5]:  # Limit output
                print(f"   {issue}")

        print("\n📋 Detailed Test Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} [{result['dashboard']}] {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")

        # Save detailed results
        results_file = "dashboard_http_testing_results.json"
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

        if success_rate >= 90:
            print("\n🎉 DASHBOARD HTTP TESTING COMPLETED SUCCESSFULLY!")
            print("✅ All dashboards are accessible and properly configured")
        elif success_rate >= 70:
            print("\n⚠️ Dashboard HTTP testing completed with minor issues")
        else:
            print("\n❌ Dashboard HTTP testing found significant issues")


async def main():
    """Main test runner"""
    tester = DashboardHTTPTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
