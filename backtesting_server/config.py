import os
from pathlib import Path


class Config:
    """Local development configuration"""

    # Service
    SERVICE_NAME = "backtesting_server"
    HOST = "localhost"
    PORT = 8003
    DEBUG = True

    # Redis (local)
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    # Streams
    MANAGEMENT_COMMANDS = "mgmt:backtesting:commands"
    BACKTESTING_RESULTS = "backtesting:mgmt:results"
    BACKTESTING_STATUS = "backtesting:status"

    # Task limits
    MAX_CONCURRENT_TASKS = 3  # Меньше для локальной разработки
    TASK_TIMEOUT = 600  # 10 минут

    # Paths
    USER_DATA_DIR = Path(__file__).parent.parent / "user_data"  # Абсолютный путь
    LOG_LEVEL = "DEBUG"


config = Config()
