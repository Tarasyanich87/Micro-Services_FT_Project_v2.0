"""
FreqAI API endpoints - Integrated with FreqAI Server
"""

from fastapi import APIRouter, Depends, HTTPException
from management_server.auth.dependencies import get_current_active_user
from management_server.models.models import User
from management_server.services.freqai_server_client import (
    get_freqai_server_client,
    FreqAIServerClient,
)

router = APIRouter()


@router.post("/train")
async def start_freqai_model_training(
    model_name: str,
    strategy_name: str = "FreqaiExampleStrategy",
    timerange: str = "20240101-20241201",
    current_user: User = Depends(get_current_active_user),
):
    """Start FreqAI model training via FreqAI Server."""
    try:
        freqai_client = get_freqai_server_client()
        result = await freqai_client.train_freqai_model(
            model_name, strategy_name, timerange
        )

        if "error" in result:
            raise HTTPException(
                status_code=500, detail=f"FreqAI training failed: {result['error']}"
            )

        return {
            "status": "success",
            "message": f"FreqAI training completed for model {model_name}",
            "model_name": model_name,
            "strategy": strategy_name,
            "timerange": timerange,
            "training_result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/models")
async def list_freqai_models(
    current_user: User = Depends(get_current_active_user),
):
    """List available FreqAI models from FreqAI Server."""
    try:
        freqai_client = get_freqai_server_client()

        # Get devices info as a way to check server status
        devices = await freqai_client.get_devices()

        return {
            "status": "success",
            "server_status": "connected" if "error" not in devices else "error",
            "devices": devices,
            "note": "Models are managed directly through FreqAI Server API",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Cannot connect to FreqAI Server: {str(e)}",
            "models": [],
        }


@router.get("/models/{model_name}")
async def get_freqai_model_status(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get FreqAI model status from FreqAI Server."""
    try:
        freqai_client = get_freqai_server_client()
        result = await freqai_client.get_model_status(model_name)

        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_name} not found: {result['error']}",
            )

        return {"status": "success", "model_name": model_name, "model_info": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get model status: {str(e)}"
        )


@router.post("/predict/{model_name}")
async def make_freqai_prediction(
    model_name: str,
    features: dict,
    current_user: User = Depends(get_current_active_user),
):
    """Make prediction using FreqAI model."""
    try:
        freqai_client = get_freqai_server_client()
        result = await freqai_client.predict(model_name, features)

        if "error" in result:
            raise HTTPException(
                status_code=500, detail=f"Prediction failed: {result['error']}"
            )

        return {"status": "success", "model_name": model_name, "prediction": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/backtest")
async def run_freqai_backtest(
    strategy_name: str,
    freqai_model: str,
    timerange: str = "20240101-20240102",
    current_user: User = Depends(get_current_active_user),
):
    """Run FreqAI backtesting via Backtesting Server."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8003/freqai-backtest",
                json={
                    "strategy_name": strategy_name,
                    "freqai_model": freqai_model,
                    "timerange": timerange,
                },
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message": f"FreqAI backtest started for {strategy_name} with model {freqai_model}",
                    "backtest_result": result,
                }
            else:
                raise HTTPException(
                    status_code=500, detail=f"Backtesting failed: {response.text}"
                )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Connection to Backtesting Server failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/backtest/{task_id}")
async def get_freqai_backtest_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get FreqAI backtest status from Backtesting Server."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8003/tasks")

            if response.status_code == 200:
                tasks = response.json()
                # Find task by ID
                for task in tasks:
                    if task.get("task_id") == task_id:
                        return {"status": "success", "task": task}

                return {"status": "not_found", "message": f"Task {task_id} not found"}
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get task status: {response.text}",
                )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Connection to Backtesting Server failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/health")
async def freqai_server_health(
    current_user: User = Depends(get_current_active_user),
):
    """Check FreqAI Server health."""
    try:
        freqai_client = get_freqai_server_client()
        health = await freqai_client.health_check()

        return {"status": "success", "freqai_server": health}
    except Exception as e:
        return {"status": "error", "message": f"FreqAI Server not available: {str(e)}"}
