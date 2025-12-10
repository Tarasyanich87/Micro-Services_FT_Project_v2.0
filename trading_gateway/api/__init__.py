from fastapi import APIRouter
from .endpoints import freqai, bots

main_api_router = APIRouter()

main_api_router.include_router(freqai.router, prefix="/freqai", tags=["FreqAI"])
main_api_router.include_router(bots.router, prefix="/bots", tags=["Bot Management"])
