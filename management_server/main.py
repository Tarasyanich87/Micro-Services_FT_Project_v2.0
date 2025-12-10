"""
Main entry point for Freqtrade Multi-Bot System API server.
"""

import uvicorn
import logging
from management_server.core.app import create_application
from management_server.core.config import settings
from management_server.api.middleware.audit_middleware import AuditMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

app = create_application("full_featured")

# Add middleware
app.add_middleware(AuditMiddleware)

if __name__ == "__main__":
    logger.info("🚀 Starting Freqtrade Multi-Bot System API Server")
    logger.info("📊 Profile: full_featured")
    logger.info("🌐 API docs available at: http://localhost:8000/docs")
    uvicorn.run(
        "management_server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
        access_log=True,
    )
