import asyncio
import uvicorn
import sys
import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from backtesting_server.services.task_service import TaskService
from shared.redis_client import redis_client
from shared.logging import setup_logging


# Simple config
class Config:
    SERVICE_NAME = "backtesting_server"
    HOST = "localhost"
    PORT = 8003
    DEBUG = True
    LOG_LEVEL = "DEBUG"


config = Config()

# Setup logging
logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="Backtesting Server (Local)",
    description="Local development version of backtesting service",
    version="0.1.0",
    debug=config.DEBUG,
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
task_service = TaskService()

# Simple in-memory command handler (without Redis Streams complexity)
command_queue = asyncio.Queue()


async def simple_command_handler():
    """Simple command handler for local development"""
    while True:
        try:
            command_data = await command_queue.get()

            command_type = command_data.get("type")
            payload = command_data.get("payload", {})

            logger.info(f"Processing command: {command_type}")

            if command_type == "START_BACKTEST":
                result = await task_service.start_backtest(
                    strategy_name=payload["strategy_name"],
                    config=payload["config"],
                    request_id=payload.get("request_id", "local"),
                )

                # Simple response (in real implementation - send to Redis)
                logger.info(f"Backtest started: {result}")

            elif command_type == "GET_TASK_STATUS":
                result = await task_service.get_task_status(payload["task_id"])
                logger.info(f"Task status: {result}")

            command_queue.task_done()

        except Exception as e:
            logger.error(f"Command handler error: {e}")


# Start command handler
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("🚀 Starting Backtesting Server (Local)")

    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

    # Start command handler
    asyncio.create_task(simple_command_handler())


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "backtesting_server",
        "version": "0.1.0",
        "redis_connected": True,  # Simplified
        "active_tasks": len(task_service.active_tasks),
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    import time

    metrics_text = f"""# HELP backtesting_server_uptime_seconds Time since startup
# TYPE backtesting_server_uptime_seconds gauge
backtesting_server_uptime_seconds {time.time()}
# HELP backtesting_server_active_tasks Number of active tasks
# TYPE backtesting_server_active_tasks gauge
backtesting_server_active_tasks {len(task_service.active_tasks)}
# HELP backtesting_server_completed_tasks Total completed tasks
# TYPE backtesting_server_completed_tasks counter
backtesting_server_completed_tasks {sum(1 for t in task_service.active_tasks.values() if t.status == "completed")}
"""
    return Response(metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/tasks")
async def get_tasks():
    """Get active tasks"""
    return await task_service.get_active_tasks()


@app.post("/test-backtest")
async def test_backtest(strategy_name: str = "TestStrategy"):
    """Test endpoint for backtesting"""
    result = await task_service.start_backtest(
        strategy_name=strategy_name,
        config_dict={"timerange": "20240101-20240102", "stake_amount": 100},
        request_id="test",
    )
    return result


@app.post("/freqai-backtest")
async def freqai_backtest(
    strategy_name: str,
    freqai_model: str,
    timerange: str = "20240101-20240102",
    stake_amount: float = 100.0,
):
    """Run FreqAI backtesting with specified model"""
    config_dict = {"timerange": timerange, "stake_amount": stake_amount}

    result = await task_service.start_backtest(
        strategy_name=strategy_name,
        config_dict=config_dict,
        request_id=f"freqai_{freqai_model}_{strategy_name}",
        freqai_model=freqai_model,
    )
    return result


@app.get("/freqai-models")
async def get_available_freqai_models():
    """Get list of available FreqAI models from FreqAI Server"""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8004/health")
            if response.status_code == 200:
                # In real implementation, get models from FreqAI Server
                return {
                    "status": "success",
                    "models": ["LightGBMRegressor", "LightGBMClassifier"],
                    "server_connected": True,
                }
            else:
                return {"status": "error", "message": "FreqAI Server not available"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}


@app.post("/test-freqai-backtest")
async def test_freqai_backtest(
    strategy_name: str = "TestStrategy", freqai_model: str = "test_model"
):
    """Test endpoint for FreqAI backtesting"""
    result = await task_service.start_backtest(
        strategy_name=strategy_name,
        config_dict={"timerange": "20240101-20240102", "stake_amount": 100},
        request_id="freqai_test",
        freqai_model=freqai_model,
    )
    return result


if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
