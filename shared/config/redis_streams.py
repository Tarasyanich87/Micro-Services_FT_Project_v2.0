"""
Redis Streams Configuration - Enterprise Namespacing Strategy
Centralized configuration for all Redis Streams in the microservices architecture.
"""

from typing import Dict, Any


class RedisStreamsConfig:
    """
    Centralized configuration for Redis Streams namespacing.

    Naming convention: {service}:{direction}:{purpose}
    Examples:
    - mgmt:trading:commands (Management → Trading Gateway commands)
    - trading:mgmt:status (Trading Gateway → Management status updates)
    - backtesting:mgmt:results (Backtesting → Management results)
    """

    # ============================================================================
    # MANAGEMENT SERVER STREAMS
    # ============================================================================

    # Management → Trading Gateway
    MGMT_TRADING_COMMANDS = "mgmt:trading:commands"
    TRADING_MGMT_STATUS = "trading:mgmt:status"
    TRADING_MGMT_RESULTS = "trading:mgmt:results"

    # Management → Backtesting Server
    MGMT_BACKTESTING_COMMANDS = "mgmt:backtesting:commands"
    BACKTESTING_MGMT_RESULTS = "backtesting:mgmt:results"
    BACKTESTING_MGMT_STATUS = "backtesting:mgmt:status"

    # Management → FreqAI Server
    MGMT_FREQAI_COMMANDS = "mgmt:freqai:commands"
    FREQAI_MGMT_RESULTS = "freqai:mgmt:results"
    FREQAI_MGMT_STATUS = "freqai:mgmt:status"

    # ============================================================================
    # SERVICE-SPECIFIC STREAMS
    # ============================================================================

    # System-wide events
    SYSTEM_EVENTS = "system:events"
    SYSTEM_HEALTH = "system:health"

    # Audit and logging
    AUDIT_EVENTS = "audit:events"
    AUDIT_TRAIL = "audit:trail"

    # Monitoring and metrics
    MONITORING_EVENTS = "monitoring:events"
    METRICS_EVENTS = "metrics:events"

    # ============================================================================
    # CONSUMER GROUP CONFIGURATION
    # ============================================================================

    # Consumer groups for reliable delivery
    MANAGEMENT_CONSUMERS = "management_consumers"
    TRADING_CONSUMERS = "trading_consumers"
    BACKTESTING_CONSUMERS = "backtesting_consumers"
    FREQAI_CONSUMERS = "freqai_consumers"
    MONITORING_CONSUMERS = "monitoring_consumers"
    AUDIT_CONSUMERS = "audit_consumers"

    # ============================================================================
    # STREAM LIMITS AND POLICIES
    # ============================================================================

    STREAM_LIMITS: Dict[str, Dict[str, Any]] = {
        # Command streams - keep recent commands
        MGMT_TRADING_COMMANDS: {"maxlen": 10000, "approximate": False},
        MGMT_BACKTESTING_COMMANDS: {"maxlen": 5000, "approximate": False},
        MGMT_FREQAI_COMMANDS: {"maxlen": 5000, "approximate": False},
        # Result streams - keep all results
        TRADING_MGMT_RESULTS: {"maxlen": 50000, "approximate": True},
        BACKTESTING_MGMT_RESULTS: {"maxlen": 25000, "approximate": True},
        FREQAI_MGMT_RESULTS: {"maxlen": 25000, "approximate": True},
        # Status streams - keep recent status updates
        TRADING_MGMT_STATUS: {"maxlen": 50000, "approximate": True},
        BACKTESTING_MGMT_STATUS: {"maxlen": 25000, "approximate": True},
        FREQAI_MGMT_STATUS: {"maxlen": 25000, "approximate": True},
        # System streams
        SYSTEM_EVENTS: {"maxlen": 100000, "approximate": True},
        SYSTEM_HEALTH: {"maxlen": 10000, "approximate": False},
        AUDIT_EVENTS: {"maxlen": 500000, "approximate": True},
    }

    # ============================================================================
    # CONSUMER GROUP MAPPINGS
    # ============================================================================

    CONSUMER_GROUPS: Dict[str, str] = {
        MGMT_TRADING_COMMANDS: TRADING_CONSUMERS,
        MGMT_BACKTESTING_COMMANDS: BACKTESTING_CONSUMERS,
        MGMT_FREQAI_COMMANDS: FREQAI_CONSUMERS,
        TRADING_MGMT_RESULTS: MANAGEMENT_CONSUMERS,
        TRADING_MGMT_STATUS: MANAGEMENT_CONSUMERS,
        BACKTESTING_MGMT_RESULTS: MANAGEMENT_CONSUMERS,
        BACKTESTING_MGMT_STATUS: MANAGEMENT_CONSUMERS,
        FREQAI_MGMT_RESULTS: MANAGEMENT_CONSUMERS,
        FREQAI_MGMT_STATUS: MANAGEMENT_CONSUMERS,
        SYSTEM_EVENTS: MONITORING_CONSUMERS,
        SYSTEM_HEALTH: MONITORING_CONSUMERS,
        AUDIT_EVENTS: AUDIT_CONSUMERS,
    }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    @classmethod
    def get_stream_limit(cls, stream_name: str) -> Dict[str, Any]:
        """Get stream limit configuration for a given stream."""
        return cls.STREAM_LIMITS.get(
            stream_name, {"maxlen": 10000, "approximate": True}
        )

    @classmethod
    def get_consumer_group(cls, stream_name: str) -> str:
        """Get consumer group for a given stream."""
        return cls.CONSUMER_GROUPS.get(stream_name, "default_consumers")

    @classmethod
    def get_all_command_streams(cls) -> list[str]:
        """Get all command streams (Management → Services)."""
        return [
            cls.MGMT_TRADING_COMMANDS,
            cls.MGMT_BACKTESTING_COMMANDS,
            cls.MGMT_FREQAI_COMMANDS,
        ]

    @classmethod
    def get_all_result_streams(cls) -> list[str]:
        """Get all result streams (Services → Management)."""
        return [
            cls.TRADING_MGMT_RESULTS,
            cls.BACKTESTING_MGMT_RESULTS,
            cls.FREQAI_MGMT_RESULTS,
        ]

    @classmethod
    def get_all_status_streams(cls) -> list[str]:
        """Get all status streams."""
        return [
            cls.TRADING_MGMT_STATUS,
            cls.BACKTESTING_MGMT_STATUS,
            cls.FREQAI_MGMT_STATUS,
            cls.SYSTEM_HEALTH,
        ]

    @classmethod
    def get_all_streams(cls) -> list[str]:
        """Get all configured streams."""
        return list(cls.STREAM_LIMITS.keys())

    @classmethod
    def get_priority_streams(cls) -> Dict[str, list[str]]:
        """Get streams organized by priority levels."""
        return {
            "critical": [
                "mgmt:trading:emergency",  # Emergency stop commands
                "system:alerts",  # System alerts
            ],
            "high": [
                cls.MGMT_TRADING_COMMANDS,  # Trading commands
                cls.MGMT_BACKTESTING_COMMANDS,  # Backtesting commands
            ],
            "normal": [
                cls.MGMT_FREQAI_COMMANDS,  # FreqAI commands
                cls.SYSTEM_EVENTS,  # System events
                cls.AUDIT_EVENTS,  # Audit events
            ],
            "low": [
                cls.MONITORING_EVENTS,  # Monitoring data
                cls.SYSTEM_HEALTH,  # Health status
            ],
        }

    @classmethod
    def get_stream_priority(cls, stream_name: str) -> str:
        """Get priority level for a stream."""
        priority_streams = cls.get_priority_streams()
        for priority, streams in priority_streams.items():
            if stream_name in streams:
                return priority
        return "normal"  # Default priority

    @classmethod
    def get_priority_weight(cls, priority: str) -> int:
        """Get numeric weight for priority (higher = more urgent)."""
        weights = {"critical": 100, "high": 75, "normal": 50, "low": 25}
        return weights.get(priority, 50)

    @classmethod
    def validate_stream_name(cls, stream_name: str) -> bool:
        """Validate that a stream name follows the naming convention."""
        parts = stream_name.split(":")
        if len(parts) != 3:
            return False

        service, direction, purpose = parts

        # Validate service names
        valid_services = {
            "mgmt",
            "trading",
            "backtesting",
            "freqai",
            "system",
            "audit",
            "monitoring",
        }

        # Validate directions
        valid_directions = {
            "trading",
            "backtesting",
            "freqai",
            "mgmt",
            "events",
            "health",
            "trail",
        }

        # Validate purposes
        valid_purposes = {"commands", "results", "status", "events", "health", "trail"}

        return (
            service in valid_services
            and direction in valid_directions
            and purpose in valid_purposes
        )


# ============================================================================
# BACKWARD COMPATIBILITY ALIASES
# ============================================================================


# For gradual migration, keep old names as aliases
class LegacyConfig:
    """Backward compatibility aliases for gradual migration."""

    # Old names → New names mapping
    LEGACY_MAPPING = {
        "mcp_commands": RedisStreamsConfig.MGMT_TRADING_COMMANDS,
        "bot_commands": RedisStreamsConfig.MGMT_TRADING_COMMANDS,
        "bot_events": RedisStreamsConfig.TRADING_MGMT_STATUS,
        "mcp_events": RedisStreamsConfig.SYSTEM_EVENTS,
        "system_events": RedisStreamsConfig.SYSTEM_EVENTS,
    }

    @classmethod
    def get_legacy_stream(cls, old_name: str) -> str:
        """Get new stream name for legacy stream name."""
        return cls.LEGACY_MAPPING.get(old_name, old_name)


# ============================================================================
# CONFIGURATION INSTANCE
# ============================================================================

# Global configuration instance
redis_streams_config = RedisStreamsConfig()
legacy_config = LegacyConfig()
