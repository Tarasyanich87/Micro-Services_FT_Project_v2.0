from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, Body
from pydantic import BaseModel
import asyncio

from management_server.auth.dependencies import get_current_active_user
from management_server.models.models import User
from management_server.services.data_service import DataService

router = APIRouter()

class DownloadDataRequest(BaseModel):
    exchanges: List[str] = ["binance"]
    pairs: List[str]
    days: int = 30
    timeframe: str = "1h"

@router.get("/")
async def get_available_data(current_user: User = Depends(get_current_active_user)):
    """
    Lists available historical data.
    """
    service = DataService()
    # This is a synchronous I/O call, run in executor
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, service.list_available_data)
    return data

@router.post("/download")
async def download_historical_data(
    request: DownloadDataRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Starts a background task to download historical data.
    """
    service = DataService()

    # Define the background task function
    def task():
        success, output = service.run_download_data_process(
            request.exchanges, request.pairs, request.days, request.timeframe
        )
        if success:
            print(f"Data download completed successfully.\n{output}")
        else:
            print(f"Data download failed.\n{output}")

    background_tasks.add_task(task)

    return {"message": "Data download process started in the background."}
