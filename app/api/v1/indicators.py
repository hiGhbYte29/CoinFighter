from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_indicator_service
from app.modules.indicators.schemas import IndicatorCatalog
from app.modules.indicators.service import IndicatorService

router = APIRouter()
IndicatorDep = Annotated[IndicatorService, Depends(get_indicator_service)]


@router.get("/catalog", response_model=IndicatorCatalog)
async def catalog(service: IndicatorDep) -> IndicatorCatalog:
    """返回前端可以配置的技术指标及参数定义。"""
    return service.catalog()
