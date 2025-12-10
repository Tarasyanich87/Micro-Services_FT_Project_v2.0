#!/usr/bin/env python3
"""
Run all services locally for development
"""

import subprocess
import time
import signal
import sys
from pathlib import Path


def run_service(name: str, command: str, cwd: str = "."):
    """Run service in background"""
    print(f"🚀 Starting {name}...")
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process


def main():
    processes = []

    try:
        # Start Redis (if not running)
        print("🔍 Checking Redis...")
        redis_check = subprocess.run("redis-cli ping", shell=True, capture_output=True)
        if redis_check.returncode != 0:
            print("Redis not running, starting...")
            redis_proc = run_service("Redis", "redis-server")
            processes.append(("Redis", redis_proc))
            time.sleep(2)

        # Start Management Server
        mgmt_proc = run_service(
            "Management Server",
            "source venv/bin/activate && PYTHONPATH=. python management_server/main.py",
            cwd=".",
        )
        processes.append(("Management Server", mgmt_proc))
        time.sleep(3)

        # Start Backtesting Server
        backtest_proc = run_service(
            "Backtesting Server",
            "source venv/bin/activate && python backtesting_server/main.py",
            cwd=".",
        )
        processes.append(("Backtesting Server", backtest_proc))
        time.sleep(2)

        # Start FreqAI Server
        freqai_proc = run_service(
            "FreqAI Server",
            "source venv/bin/activate && python freqai_server/main.py",
            cwd=".",
        )
        processes.append(("FreqAI Server", freqai_proc))
        time.sleep(2)

        print("\n" + "=" * 50)
        print("🎉 Services started!")
        print("📊 Service URLs:")
        print("  Management: http://localhost:8002")
        print("  Backtesting: http://localhost:8003")
        print("  FreqAI: http://localhost:8004")
        print("🔍 Health checks:")
        print("  curl http://localhost:8002/health")
        print("  curl http://localhost:8003/health")
        print("  curl http://localhost:8004/health")
        print("=" * 50)
        print("Press Ctrl+C to stop all services")

        # Wait for interrupt
        signal.signal(signal.SIGINT, lambda sig, frame: None)
        signal.pause()

    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")

    finally:
        # Stop all processes
        for name, proc in processes:
            print(f"Stopping {name}...")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        print("✅ All services stopped")


if __name__ == "__main__":
    main()
