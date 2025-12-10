from fastapi import APIRouter

from . import (
    auth,
    bots,
    strategies,
    analytics,
    advanced_trading,
    freqai,
    freqai_models,
    exchanges,
    emergency,
    data,
    hyperopt,
    audit,
    monitoring,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(bots.router, prefix="/bots", tags=["Bot Management"])
api_router.include_router(
    freqai_models.router, prefix="/freqai/models", tags=["FreqAI Models"]
)
api_router.include_router(exchanges.router, prefix="/exchanges", tags=["Exchanges"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["Emergency"])
api_router.include_router(
    strategies.router, prefix="/strategies", tags=["Strategy Management"]
)
api_router.include_router(hyperopt.router, prefix="/hyperopt", tags=["Hyperopt"])
api_router.include_router(analytics.router, prefix="/analytics")
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(
    advanced_trading.router, prefix="/advanced", tags=["Advanced Trading"]
)
api_router.include_router(freqai.router, prefix="/freqai", tags=["FreqAI"])
api_router.include_router(data.router, prefix="/data", tags=["Historical Data"])
