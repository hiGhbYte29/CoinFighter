from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_dataset_service
from app.modules.datasets.schemas import DatasetDownloadRequest, DatasetMetadata, DatasetValidation
from app.modules.datasets.service import DatasetService

router = APIRouter()
DatasetDep = Annotated[DatasetService, Depends(get_dataset_service)]


@router.get("", response_model=list[DatasetMetadata])
async def list_datasets(service: DatasetDep) -> list[DatasetMetadata]:
    """查询本地保存的全部行情数据集。"""
    return service.list()


@router.post("/download", status_code=status.HTTP_202_ACCEPTED)
async def download(request: DatasetDownloadRequest, service: DatasetDep) -> dict:
    """创建行情数据集下载任务。"""
    return await service.start_download(request)


@router.get("/tasks")
async def list_download_tasks(service: DatasetDep) -> list[dict]:
    """查询全部数据集下载任务。"""
    return service.tasks.list(kind="download")


@router.get("/tasks/{task_id}")
async def download_task(task_id: str, service: DatasetDep) -> dict:
    """查询指定数据集下载任务的状态。"""
    return service.tasks.get(task_id)


@router.get("/{dataset_id}", response_model=DatasetMetadata)
async def dataset(dataset_id: str, service: DatasetDep) -> DatasetMetadata:
    """查询指定数据集的元数据。"""
    return service.get(dataset_id)


@router.get("/{dataset_id}/candles")
async def dataset_candles(
    dataset_id: str,
    service: DatasetDep,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = Query(default=500, ge=1, le=10_000),
) -> list[dict]:
    """分页查询指定数据集的 K 线记录。"""
    return service.candles(dataset_id, start=start, end=end, limit=limit)


@router.post("/{dataset_id}/validate", response_model=DatasetValidation)
async def validate_dataset(dataset_id: str, service: DatasetDep) -> DatasetValidation:
    """校验指定数据集的完整性与有效性。"""
    return service.validate(dataset_id)
