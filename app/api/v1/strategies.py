from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_strategy_loader
from app.modules.strategies.loader import StrategyLoader
from app.modules.strategies.schemas import (
    StrategyCreate,
    StrategyInfo,
    StrategySource,
    StrategySourceUpdate,
)

router = APIRouter()
StrategyDep = Annotated[StrategyLoader, Depends(get_strategy_loader)]


@router.get("", response_model=list[StrategyInfo])
async def list_strategies(loader: StrategyDep) -> list[StrategyInfo]:
    return loader.list()


@router.post("", response_model=StrategySource, status_code=status.HTTP_201_CREATED)
async def create_strategy(request: StrategyCreate, loader: StrategyDep) -> StrategySource:
    return loader.create(request.name, request.source)


@router.post("/reload", response_model=list[StrategyInfo])
async def reload_strategies(loader: StrategyDep) -> list[StrategyInfo]:
    return loader.list()


@router.get("/{name}", response_model=StrategyInfo)
async def strategy(name: str, loader: StrategyDep) -> StrategyInfo:
    return loader.get_info(name)


@router.get("/{name}/source", response_model=StrategySource)
async def strategy_source(name: str, loader: StrategyDep) -> StrategySource:
    return loader.source(name)


@router.put("/{name}/source", response_model=StrategySource)
async def save_strategy(
    name: str, request: StrategySourceUpdate, loader: StrategyDep
) -> StrategySource:
    return loader.save(name, request.source)


@router.post("/{name}/validate", response_model=StrategyInfo)
async def validate_strategy(name: str, loader: StrategyDep) -> StrategyInfo:
    return loader.get_info(name)
