import logging
import sys
from pathlib import Path


def setup_logging(service_name: str, level: str = "INFO"):
    """Setup logging for local development"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=f"%(asctime)s - {service_name} - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / f"{service_name}.log"),
        ],
    )

    return logging.getLogger(service_name)
