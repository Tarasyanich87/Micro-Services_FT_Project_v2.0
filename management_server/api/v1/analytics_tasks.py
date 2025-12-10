<<<<<<< HEAD
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from management_server.services.backtesting_service import BacktestingService, get_backtesting_service
from management_server.services.hyperopt_service import HyperoptService, get_hyperopt_service
=======
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any

from management_server.services.backtesting_service import backtesting_service
>>>>>>> origin/refactor/full-system-rewrite
from management_server.auth.dependencies import get_current_active_user
from management_server.models.models import User

router = APIRouter()

class BacktestRequest(BaseModel):
    strategy: str
    pair: str
    timeframe: str

<<<<<<< HEAD
class HyperoptRequest(BaseModel):
    strategy: str
    epochs: int = 100
    spaces: str = "all"

@router.post("/backtest", status_code=202)
def run_backtest_endpoint(
    request: BacktestRequest,
    service: BacktestingService = Depends(get_backtesting_service),
    current_user: User = Depends(get_current_active_user)
):
    """Initiate a new backtest task."""
    result = service.run_backtest(request.strategy, request.pair, request.timeframe)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.get("/backtest/status/{task_id}")
def get_backtest_status(
    task_id: str,
    service: BacktestingService = Depends(get_backtesting_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get the status of a backtest task."""
    status = service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@router.get("/backtests")
def get_all_backtests(
    service: BacktestingService = Depends(get_backtesting_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get all backtest tasks."""
    return service.get_all_tasks()

@router.get("/backtest/result/{task_id}")
def get_backtest_result(
    task_id: str,
    service: BacktestingService = Depends(get_backtesting_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get the result of a completed backtest task."""
    task = service.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Task is not completed yet")

    try:
        with open(task['output_file'], 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to read result file: {e}")

@router.post("/hyperopt", status_code=202)
def run_hyperopt_endpoint(
    request: HyperoptRequest,
    service: HyperoptService = Depends(get_hyperopt_service),
    current_user: User = Depends(get_current_active_user)
):
    """Initiate a new hyperopt task."""
    result = service.run_hyperopt(request.strategy, request.epochs, request.spaces)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.get("/hyperopt/status/{task_id}")
def get_hyperopt_status(
    task_id: str,
    service: HyperoptService = Depends(get_hyperopt_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get the status of a hyperopt task."""
    status = service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@router.get("/hyperopts")
def get_all_hyperopts(
    service: HyperoptService = Depends(get_hyperopt_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get all hyperopt tasks."""
    return service.get_all_tasks()
=======
@router.post("/backtest", response_model=Dict[str, Any])
async def run_backtest_endpoint(
    request: BacktestRequest,
    # Using BackgroundTasks here to acknowledge the request immediately
    # while the (potentially long) backtest runs in the background.
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint to trigger a Freqtrade backtest.
    """

    # A simple approach: run in the background.
    # A better approach would use a real task queue like Celery.
    background_tasks.add_task(
        backtesting_service.run_backtest,
        request.strategy,
        request.pair,
        request.timeframe
    )

    return {
        "status": "initiated",
        "message": f"Backtest for strategy '{request.strategy}' on pair '{request.pair}' has been initiated."
    }

# In the future, you would add endpoints here to check the status of a task
# and retrieve its results once completed.
# For example:
# @router.get("/backtest/results/{task_id}")
# async def get_backtest_results(task_id: str, ...):
#     ...
>>>>>>> origin/refactor/full-system-rewrite
