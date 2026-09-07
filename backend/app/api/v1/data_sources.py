from __future__ import annotations

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from backend.app.api.deps import PerformanceServiceDep
from backend.app.domain.models import CorrelationResult, DataSourceConnection

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


class CreateDataSourceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    dialect: str = Field(
        min_length=1,
        max_length=32,
        description="A display label only (Snowflake/BigQuery/Postgres/...).",
    )
    connection_uri: str = Field(
        min_length=1,
        description="Write-only. Never returned by this or any other endpoint.",
    )
    query: str = Field(
        min_length=1,
        description="Must return columns: external_ad_id, ctr, spend, "
        "conversions, impressions, metric_date.",
    )


class RefreshResult(BaseModel):
    rows_fetched: int


@router.post("", response_model=DataSourceConnection, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    payload: CreateDataSourceRequest, service: PerformanceServiceDep
) -> DataSourceConnection:
    return await service.create_connection(
        payload.name, payload.dialect, payload.connection_uri, payload.query
    )


@router.get("", response_model=list[DataSourceConnection])
async def list_data_sources(service: PerformanceServiceDep) -> list[DataSourceConnection]:
    return await service.list_connections()


@router.get("/{connection_id}", response_model=DataSourceConnection)
async def get_data_source(
    connection_id: str, service: PerformanceServiceDep
) -> DataSourceConnection:
    return await service.get_connection(connection_id)


@router.delete(
    "/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_data_source(
    connection_id: str, service: PerformanceServiceDep
) -> Response:
    await service.delete_connection(connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{connection_id}/test", response_model=DataSourceConnection)
async def test_data_source(
    connection_id: str, service: PerformanceServiceDep
) -> DataSourceConnection:
    return await service.test_connection(connection_id)


@router.post("/{connection_id}/refresh", response_model=RefreshResult)
async def refresh_data_source(
    connection_id: str, service: PerformanceServiceDep
) -> RefreshResult:
    count = await service.refresh_metrics(connection_id)
    return RefreshResult(rows_fetched=count)


@router.get("/{connection_id}/correlation", response_model=CorrelationResult)
async def get_correlation(
    connection_id: str, service: PerformanceServiceDep
) -> CorrelationResult:
    return await service.get_correlation(connection_id)
