import redis
import os
import json
from typing import Optional


class RedisClient:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD")

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
        )

    def ping(self):
        return self.client.ping()

    def publish(self, channel: str, message: str):
        return self.client.publish(channel, message)

    def xadd(self, stream: str, fields: dict):
        # Convert dict values to strings for Redis
        string_fields = {
            k: json.dumps(v) if isinstance(v, dict) else str(v)
            for k, v in fields.items()
        }
        return self.client.xadd(stream, string_fields)  # type: ignore

    def xread(self, streams: dict, count: int = 10, block: int = 1000):
        return self.client.xread(streams, count=count, block=block)


# Global instance
redis_client = RedisClient()
