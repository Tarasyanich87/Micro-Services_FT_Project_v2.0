"""
Centralized logging configuration for Freqtrade Multi-Bot System.
Uses structlog for structured logging with JSON output.
"""

import logging
import sys
from typing import Any, Dict

try:
    import structlog
    from pythonjsonlogger import jsonlogger

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from management_server.core.config import settings


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """
    Setup centralized logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format for logs
    """
    # Convert string log level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    if STRUCTLOG_AVAILABLE and json_format:
        # Configure structlog for JSON logging
        shared_processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]

        if settings.ENVIRONMENT == "production":
            # JSON formatter for production
            shared_processors.append(structlog.processors.JSONRenderer())
        else:
            # Human-readable formatter for development
            shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))

        structlog.configure(
            processors=shared_processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # Fallback to standard logging
        if json_format:
            # Use JSON formatter
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s"
            )
            for handler in logging.root.handlers:
                handler.setFormatter(formatter)


def get_logger(name: str) -> Any:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance (structlog or standard logging)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


# Global logger instance
logger = get_logger(__name__)
