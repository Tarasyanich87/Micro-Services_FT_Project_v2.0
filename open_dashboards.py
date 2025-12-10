#!/usr/bin/env python3
"""
Dashboard Opener - Opens all Freqtrade dashboards in browser
"""

import webbrowser
import time
import subprocess
import sys


def open_dashboard(url, name, delay=0.5):
    """Open dashboard in browser with delay"""
    print(f"🌐 Opening {name}: {url}")
    webbrowser.open(url, new=2)  # new=2 opens in new tab
    time.sleep(delay)


def main():
    """Open all dashboards"""
    print("🚀 Opening Freqtrade Multi-Bot System Dashboards")
    print("=" * 60)

    # Check if services are running
    try:
        import httpx

        response = httpx.get("http://localhost:8002/health", timeout=5)
        if response.status_code != 200:
            print("❌ Management Server not responding")
            sys.exit(1)
    except:
        print("❌ Cannot connect to Management Server")
        sys.exit(1)

    print("✅ All services are running")

    # Dashboard URLs
    dashboards = [
        ("http://localhost:5176/", "Home Dashboard"),
        ("http://localhost:5176/bots", "Bot Management"),
        ("http://localhost:5176/strategies", "Strategies"),
        ("http://localhost:5176/analytics", "Analytics"),
        ("http://localhost:5176/freqai-lab", "FreqAI Lab"),
        ("http://localhost:5176/data", "Data Management"),
        ("http://localhost:5176/hyperopt", "Hyperopt"),
        ("http://localhost:5176/monitoring", "Monitoring"),
        ("http://localhost:5176/audit", "Audit"),
        ("http://localhost:5176/login", "Login"),
    ]

    # Open main access page first
    print("📋 Opening main dashboard access page...")
    open_dashboard(
        "file://"
        + "/home/taras/Documents/Opencode_NEW/jules_freqtrade_project/dashboard_access.html",
        "Dashboard Access Page",
        2,
    )

    # Open all dashboards
    print("🎯 Opening all dashboards...")
    for url, name in dashboards:
        open_dashboard(url, name, 0.8)

    # Open API docs
    print("📖 Opening API documentation...")
    open_dashboard("http://localhost:8002/docs", "Management Server API", 1)
    open_dashboard("http://localhost:8001/docs", "Trading Gateway API", 0.5)

    print("\n" + "=" * 60)
    print("🎉 ALL DASHBOARDS OPENED SUCCESSFULLY!")
    print("=" * 60)
    print("📋 Dashboard Access Page: dashboard_access.html")
    print("🔗 Main UI: http://localhost:5176/")
    print("📖 API Docs: http://localhost:8002/docs")
    print("💚 Health Check: http://localhost:8002/health")
    print("=" * 60)


if __name__ == "__main__":
    main()
