#!/usr/bin/env python3
"""
Script to initialize the database
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from management_server.database.connection import init_database


async def main():
    await init_database()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())
