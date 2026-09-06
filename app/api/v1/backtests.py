from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_backtest_service
from app.modules.backtest.runner import BacktestService
from app.modules.backtest.schemas import BacktestRequest

router = APIRouter()
BacktestDep = Annotated[BacktestService, Depends(get_backtest_service)]


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_backtest(request: BacktestRequest, service: BacktestDep) -> dict:
    return await service.start(request)


@router.get("")
async def list_backtests(service: BacktestDep) -> list[dict]:
    return service.list()


@router.get("/{run_id}")
async def backtest(run_id: str, service: BacktestDep) -> dict:
    return service.get(run_id)


@router.post("/{run_id}/cancel")
async def cancel_backtest(run_id: str, service: BacktestDep) -> dict:
    return await service.cancel(run_id)


@router.get("/{run_id}/trades")
async def backtest_trades(run_id: str, service: BacktestDep) -> list[dict]:
    return service.records(run_id, "trades")


@router.get("/{run_id}/equity")
async def backtest_equity(run_id: str, service: BacktestDep) -> list[dict]:
    return service.records(run_id, "equity")
