#!/usr/bin/env python3
"""
Setup script for local development environment
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run command with error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Output: {e.output}")
        return False


def setup_local_environment():
    """Setup local development environment"""

    print("🚀 Setting up Freqtrade Microservices local environment...")

    # 1. Create virtual environment
    if not Path("venv").exists():
        run_command("python -m venv venv", "Creating virtual environment")

    # 2. Activate venv and install dependencies
    activate_cmd = "source venv/bin/activate && "
    pip_cmd = activate_cmd + "pip install -r requirements.txt"

    if run_command(pip_cmd, "Installing dependencies"):
        print("📦 Dependencies installed successfully")

    # 3. Setup database
    db_cmd = (
        activate_cmd
        + 'python -c "from management_server.database.connection import init_db; init_db()"'
    )
    run_command(db_cmd, "Initializing database")

    # 4. Create shared modules (already done)
    print("📁 Shared modules created")

    # 5. Test Redis connection
    redis_cmd = (
        activate_cmd
        + "python -c \"import redis; r = redis.Redis(); print('Redis:', r.ping())\""
    )
    run_command(redis_cmd, "Testing Redis connection")

    print("🎉 Local environment setup completed!")
    print("\n📋 Next steps:")
    print("1. source venv/bin/activate")
    print("2. python scripts/run_all.py")


if __name__ == "__main__":
    setup_local_environment()
