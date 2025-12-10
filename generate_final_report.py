#!/usr/bin/env python3
"""
Final Test Report Generator
Generates comprehensive report of all test results and system status.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
import httpx


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def check_service_health(url: str) -> dict:
    """Check service health and return status."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{url}/health")
            return {
                "url": url,
                "status_code": response.status_code,
                "healthy": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else None,
            }
    except Exception as e:
        return {"url": url, "status_code": None, "healthy": False, "error": str(e)}


def run_test_suite(test_path: str) -> dict:
    """Run pytest on specific test path and return results."""
    os.chdir("/home/taras/Documents/Opencode_NEW/jules_freqtrade_project")
    cmd = f"python -m pytest {test_path} --tb=no -q"
    returncode, stdout, stderr = run_command(cmd)

    # Parse pytest output
    lines = stdout.strip().split("\n")
    if lines and "=" in lines[-1]:
        summary_line = lines[-1]
        # Extract numbers from summary like "5 failed, 10 passed"
        parts = summary_line.split(",")
        passed = 0
        failed = 0
        for part in parts:
            part = part.strip()
            if "passed" in part:
                passed = int(part.split()[0])
            elif "failed" in part:
                failed = int(part.split()[0])

        return {
            "total": passed + failed,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / (passed + failed)) * 100
            if (passed + failed) > 0
            else 0,
        }

    return {"total": 0, "passed": 0, "failed": 0, "success_rate": 0}


def generate_report():
    """Generate comprehensive test report."""

    report = {
        "timestamp": datetime.now().isoformat(),
        "system_status": {},
        "test_results": {},
        "summary": {},
    }

    # Check all services
    services = {
        "Management Server": "http://localhost:8002",
        "Trading Gateway": "http://localhost:8001",
        "Backtesting Server": "http://localhost:8003",
        "FreqAI Server": "http://localhost:8004",
    }

    print("🔍 Checking service health...")
    for name, url in services.items():
        health = check_service_health(url)
        report["system_status"][name] = health
        status = "✅" if health["healthy"] else "❌"
        print(f"  {status} {name}: {health['status_code'] or 'ERROR'}")

    # Run test suites
    test_suites = {
        "API Tests": "tests/api/",
        "Unit Tests": "tests/unit/",
        "Integration Tests": "tests/integration/",
        "E2E Tests": "tests/e2e/",
        "All Tests": "tests/",
    }

    print("\n🧪 Running test suites...")
    total_tests = 0
    total_passed = 0
    total_failed = 0

    for suite_name, test_path in test_suites.items():
        print(f"  Running {suite_name}...")
        results = run_test_suite(test_path)
        report["test_results"][suite_name] = results

        total_tests += results["total"]
        total_passed += results["passed"]
        total_failed += results["failed"]

        success_rate = results["success_rate"]
        status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
        print(
            f"    {status} {results['passed']}/{results['total']} passed ({success_rate:.1f}%)"
        )

    # Generate summary
    overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0

    report["summary"] = {
        "total_services": len(services),
        "healthy_services": sum(
            1 for s in report["system_status"].values() if s["healthy"]
        ),
        "total_tests": total_tests,
        "passed_tests": total_passed,
        "failed_tests": total_failed,
        "overall_success_rate": overall_success_rate,
        "system_health_score": (
            sum(1 for s in report["system_status"].values() if s["healthy"])
            / len(services)
        )
        * 100,
    }

    # Save report
    report_path = Path(
        "/home/taras/Documents/Opencode_NEW/jules_freqtrade_project/reports/python/final_test_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print final summary
    print("\n📊 FINAL TEST REPORT")
    print("=" * 50)
    print(
        f"🖥️  Services: {report['summary']['healthy_services']}/{report['summary']['total_services']} healthy"
    )
    print(
        f"🧪 Tests: {total_passed}/{total_tests} passed ({overall_success_rate:.1f}%)"
    )
    print(f"📁 Report saved: {report_path}")

    if overall_success_rate >= 80 and report["summary"]["system_health_score"] >= 80:
        print("🎉 SYSTEM STATUS: EXCELLENT - Ready for production!")
    elif overall_success_rate >= 60 and report["summary"]["system_health_score"] >= 60:
        print("⚠️  SYSTEM STATUS: GOOD - Minor issues to address")
    else:
        print("❌ SYSTEM STATUS: NEEDS ATTENTION - Critical issues found")

    return report


if __name__ == "__main__":
    generate_report()
