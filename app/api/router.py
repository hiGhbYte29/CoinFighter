from fastapi import APIRouter

from app.api.v1 import backtests, datasets, health, market, strategies

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
