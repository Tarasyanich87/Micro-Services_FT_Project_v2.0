import asyncio
import uvicorn
import sys
import os
import time
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from freqai_server.services.device_manager import DeviceManager
from freqai_server.services.model_service import ModelService
from freqai_server.services.prediction_service import PredictionService
from shared.redis_client import redis_client
from shared.logging import setup_logging
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus
from shared.config.redis_streams import redis_streams_config


# Simple config
class Config:
    SERVICE_NAME = "freqai_server"
    HOST = "localhost"
    PORT = 8004
    DEBUG = True
    LOG_LEVEL = "DEBUG"


config = Config()

# Setup logging
logger = setup_logging(config.SERVICE_NAME, config.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="FreqAI Server (Local)",
    description="Local development version of FreqAI service",
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
device_manager = DeviceManager()
model_service = ModelService()
prediction_service = PredictionService()

# Redis Streams Event Bus for enterprise messaging
event_bus = mcp_streams_event_bus


async def handle_freqai_command(event):
    """Handle FreqAI commands from Redis Streams"""
    payload = None
    try:
        command_type = event.type
        payload = event.data

        logger.info(f"🔄 Processing Redis FreqAI command: {command_type}")

        if command_type == "TRAIN_MODEL":
            result = await model_service.train_model(
                model_name=payload["model_name"],
                config=payload.get("bot_config", {}),
            )

            # Send result back via Redis Streams
            await event_bus.publish(
                redis_streams_config.FREQAI_MGMT_RESULTS,
                {
                    "task_id": payload.get(
                        "request_id", f"train_{payload['model_name']}"
                    ),
                    "model_name": payload["model_name"],
                    "status": "completed"
                    if result.get("status") == "success"
                    else "failed",
                    "result": result,
                    "timestamp": event.timestamp,
                },
                "MODEL_TRAINING_RESULT",
            )

            # Update status
            await event_bus.publish(
                redis_streams_config.FREQAI_MGMT_STATUS,
                {
                    "task_id": payload.get(
                        "request_id", f"train_{payload['model_name']}"
                    ),
                    "model_name": payload["model_name"],
                    "status": "completed"
                    if result.get("status") == "success"
                    else "failed",
                    "service": "freqai_server",
                    "timestamp": event.timestamp,
                },
                "SERVICE_STATUS",
            )

            logger.info(f"✅ Model training completed via Redis: {result}")

        elif command_type == "PREDICT":
            result = await prediction_service.predict(
                model_name=payload["model_name"],
                features=payload.get("features", {}),
            )

            # Send result back via Redis Streams
            await event_bus.publish(
                redis_streams_config.FREQAI_MGMT_RESULTS,
                {
                    "task_id": payload.get(
                        "request_id", f"predict_{payload['model_name']}"
                    ),
                    "model_name": payload["model_name"],
                    "status": "completed",
                    "predictions": result,
                    "timestamp": event.timestamp,
                },
                "PREDICTION_RESULT",
            )

            logger.info(f"🎯 Prediction completed via Redis: {result}")

    except Exception as e:
        logger.error(f"❌ Redis FreqAI command handler error: {e}")

        # Send error status
        try:
            task_id = payload.get("request_id") if payload else "unknown"
            await event_bus.publish(
                redis_streams_config.FREQAI_MGMT_STATUS,
                {
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "service": "freqai_server",
                    "timestamp": event.timestamp
                    if hasattr(event, "timestamp")
                    else time.time(),
                },
                "SERVICE_STATUS",
            )
        except Exception as status_error:
            logger.error(f"❌ Failed to send error status: {status_error}")


# Start command handler
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("🚀 Starting FreqAI Server with Redis Streams")

    # Initialize Redis Streams Event Bus
    global event_bus
    try:
        await event_bus.connect()
        logger.info("✅ Redis Streams Event Bus connected")

        # Subscribe to FreqAI commands
        await event_bus.subscribe(
            redis_streams_config.MGMT_FREQAI_COMMANDS,
            handle_freqai_command,
            consumer_group=redis_streams_config.FREQAI_CONSUMERS,
        )
        logger.info("✅ Subscribed to FreqAI commands stream")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis Streams: {e}")
        # Fallback to simple mode
        logger.warning("⚠️ Falling back to simple command handler")
        asyncio.create_task(simple_fallback_handler())

    # Test basic Redis connection
    try:
        redis_client.ping()
        logger.info("✅ Redis basic connection OK")
    except Exception as e:
        logger.warning(f"⚠️ Redis basic connection failed: {e}")


async def simple_fallback_handler():
    """Fallback command handler when Redis Streams fail"""
    logger.warning("🔄 Using fallback command handler (Redis Streams unavailable)")
    command_queue = asyncio.Queue()

    while True:
        try:
            command_data = await command_queue.get()
            command_type = command_data.get("type")
            payload = command_data.get("payload", {})

            logger.info(f"Processing fallback command: {command_type}")

            if command_type == "TRAIN_MODEL":
                result = await model_service.train_model(
                    model_name=payload["model_name"],
                    config=payload.get("bot_config", {}),
                )
                logger.info(f"Model training result (fallback): {result}")

            command_queue.task_done()

        except Exception as e:
            logger.error(f"Fallback command handler error: {e}")


@app.get("/health")
async def health_check():
    """Health check"""
    devices = device_manager.detect_devices()

    redis_streams_ok = False
    try:
        if event_bus and event_bus.redis:
            await event_bus.redis.ping()
            redis_streams_ok = True
    except:
        redis_streams_ok = False

    return {
        "status": "healthy" if redis_streams_ok else "degraded",
        "service": "freqai_server",
        "version": "0.1.0",
        "redis_connected": redis_streams_ok,
        "redis_streams_enabled": redis_streams_ok,
        "devices": devices["summary"],
        "consumer_group": redis_streams_config.FREQAI_CONSUMERS,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    import time

    devices = device_manager.detect_devices()
    metrics_text = f"""# HELP freqai_server_uptime_seconds Time since startup
# TYPE freqai_server_uptime_seconds gauge
freqai_server_uptime_seconds {time.time()}
# HELP freqai_server_gpu_available GPU availability
# TYPE freqai_server_gpu_available gauge
freqai_server_gpu_available {1 if devices["cuda"]["available"] else 0}
# HELP freqai_server_cpu_cores Number of CPU cores
# TYPE freqai_server_cpu_cores gauge
freqai_server_cpu_cores {devices["cpu"]["cores"]}
"""
    return Response(metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/devices")
async def get_devices():
    """Get device information"""
    return device_manager.detect_devices()


@app.post("/train-model")
async def train_model(model_name: str, model_type: str = "LightGBM"):
    """Train a model"""
    config = {"model_type": model_type}
    result = await model_service.train_model(model_name, config)
    return result


@app.post("/train-freqai")
async def train_freqai_model(
    model_name: str,
    strategy_name: str = "FreqaiExampleStrategy",
    timerange: str = "20240101-20241201",
    stake_amount: float = 100.0,
):
    """Train FreqAI model using backtesting data"""
    import tempfile
    import os
    import asyncio
    import json

    # Use existing working config file directly
    import os
    from pathlib import Path

    user_data_dir = Path(__file__).parent.parent / "user_data"
    config_path = user_data_dir / "configs" / "freqai_config.json"

    # Use the config file path directly

    # Use existing config file directly
    config_file = str(config_path)

    try:
        # Run Freqtrade backtesting for training
        process = await asyncio.create_subprocess_exec(
            "freqtrade",
            "backtesting",
            "--config",
            config_file,
            "--strategy",
            strategy_name,
            "--timerange",
            timerange,
            "--freqaimodel",
            model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            # Training successful - model should be saved
            model_path = f"freqai_server/models/{model_name}.joblib"
            result = {
                "model_name": model_name,
                "strategy": strategy_name,
                "timerange": timerange,
                "status": "training_completed",
                "model_path": model_path,
                "message": f"FreqAI model {model_name} trained successfully",
            }
        else:
            error_msg = stderr.decode()
            result = {
                "model_name": model_name,
                "status": "training_failed",
                "error": error_msg,
                "message": f"Training failed for model {model_name}",
            }

    except Exception as e:
        result = {
            "model_name": model_name,
            "status": "error",
            "error": str(e),
            "message": f"Training error: {str(e)}",
        }

    finally:
        # No cleanup needed for existing config file
        pass

    return result


@app.get("/training-status/{model_name}")
async def get_training_status(model_name: str):
    """Get training status for a model"""
    # In real implementation, this would check actual training status
    # For now, return mock status
    return {
        "model_name": model_name,
        "status": "completed",
        "progress": 100,
        "message": f"Training completed for {model_name}",
    }


@app.get("/models/{model_name}")
async def get_model_status(model_name: str):
    """Get model status"""
    return await model_service.get_model_status(model_name)


@app.post("/predict/{model_name}")
async def predict(model_name: str, features: dict):
    """Make prediction"""
    return await prediction_service.predict(model_name, features)


@app.get("/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get model information"""
    return await prediction_service.get_model_info(model_name)


if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
