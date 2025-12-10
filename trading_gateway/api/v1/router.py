from fastapi import APIRouter
from . import bots

api_router = APIRouter()
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
# WebSocket routes are added directly to the app in core/app.py
