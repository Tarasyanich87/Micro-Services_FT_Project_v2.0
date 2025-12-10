from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from trading_gateway.services.ft_rest_client_service import ft_rest_client_service

router = APIRouter()

@router.post("/{bot_name}/start", response_model=Dict[str, Any])
async def start_bot(bot_name: str):
    try:
        return await ft_rest_client_service.start_bot(bot_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bot_name}/stop", response_model=Dict[str, Any])
async def stop_bot(bot_name: str):
    try:
        return await ft_rest_client_service.stop_bot(bot_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bot_name}/status", response_model=Dict[str, Any])
async def get_bot_status(bot_name: str):
    try:
        return await ft_rest_client_service.get_bot_status(bot_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/all", response_model=Dict[str, Dict[str, Any]])
async def get_all_bots_status():
    try:
        return await ft_rest_client_service.get_all_bots_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
