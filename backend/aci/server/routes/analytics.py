from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from logfire.experimental.query_client import AsyncLogfireQueryClient

from aci.common.db import crud
from aci.common.logging_setup import get_logger
from aci.common.schemas.analytics import DistributionDatapoint, TimeSeriesDatapoint
from aci.server import config
from aci.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)


def _get_project_api_key_ids_sql_list(context: deps.RequestContext) -> str | None:
    project_api_key_ids = crud.projects.get_all_api_key_ids_for_project(
        context.db_session, context.project.id
    )

    if not project_api_key_ids:
        return None

    return ",".join(f"'{key_id}'" for key_id in project_api_key_ids)


@router.get("/app-usage-distribution", response_model=list[DistributionDatapoint])
async def get_app_usage_distribution(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
) -> list[DistributionDatapoint]:
    api_key_ids_sql_list = _get_project_api_key_ids_sql_list(context)

    if not api_key_ids_sql_list:
        return []

    query = f"""
SELECT
  regexp_replace(url_path, '/v1/functions/([^/]+?)(?:__.*)?/execute', '\\1') AS name,
  COUNT(*) AS value
FROM records
WHERE attributes->>'http.user_agent' LIKE '%python%'
  AND attributes->>'fastapi.route.name' = 'execute'
  AND trace_id IN (SELECT trace_id FROM records
WHERE attributes->>'api_key_id' IN ({api_key_ids_sql_list}))
GROUP BY name
ORDER BY value DESC;
    """

    async with AsyncLogfireQueryClient(read_token=config.LOGFIRE_READ_TOKEN) as client:
        json_rows = await client.query_json_rows(
            sql=query, min_timestamp=datetime.now() - timedelta(days=7)
        )
        return [DistributionDatapoint(**row) for row in json_rows["rows"]]


@router.get("/function-usage-distribution", response_model=list[DistributionDatapoint])
async def get_function_usage_distribution(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
) -> list[DistributionDatapoint]:
    api_key_ids_sql_list = _get_project_api_key_ids_sql_list(context)

    if not api_key_ids_sql_list:
        return []

    query = f"""
SELECT
  regexp_replace(url_path, '/v1/functions/([A-Z0-9_]+)/execute', '\\1') AS name,
  COUNT(*) AS value
FROM records
WHERE attributes->>'http.user_agent' LIKE '%python%'
  AND attributes->>'fastapi.route.name' = 'execute'
  AND trace_id IN (SELECT trace_id FROM records
WHERE attributes->>'api_key_id' IN ({api_key_ids_sql_list}))
GROUP BY name
ORDER BY value DESC;
    """

    async with AsyncLogfireQueryClient(read_token=config.LOGFIRE_READ_TOKEN) as client:
        json_rows = await client.query_json_rows(
            sql=query, min_timestamp=datetime.now() - timedelta(days=7)
        )
        return [DistributionDatapoint(**row) for row in json_rows["rows"]]


@router.get("/app-usage-timeseries", response_model=list[TimeSeriesDatapoint])
async def get_app_usage_timeseries(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
) -> list[TimeSeriesDatapoint]:
    api_key_ids_sql_list = _get_project_api_key_ids_sql_list(context)

    if not api_key_ids_sql_list:
        return []

    query = f"""
SELECT
  time_bucket('1d', start_timestamp)::DATE AS x,
  regexp_replace(url_path, '/v1/functions/([^/]+?)(?:__.*)?/execute', '\\1') AS app_name,
  COUNT(*) AS amount
FROM records
WHERE attributes->>'http.user_agent' LIKE '%python%'
  AND attributes->>'fastapi.route.name' = 'execute'
  AND trace_id IN (SELECT trace_id FROM records
WHERE attributes->>'api_key_id' IN ({api_key_ids_sql_list}))
GROUP BY app_name, x
ORDER BY x DESC;
    """

    async with AsyncLogfireQueryClient(read_token=config.LOGFIRE_READ_TOKEN) as client:
        json_rows = await client.query_json_rows(
            sql=query, min_timestamp=datetime.now() - timedelta(days=7)
        )

        # Transform the data format
        raw_rows = json_rows["rows"]
        date_grouped = {}
        for row in raw_rows:
            date = row["x"]
            app = row["app_name"]
            amount = row["amount"]

            if date not in date_grouped:
                date_grouped[date] = {"date": date}

            date_grouped[date][app] = amount

        # Convert to list format and use the TimeSeriesDatapoint model
        return [TimeSeriesDatapoint(**data) for data in date_grouped.values()]


@router.get("/function-usage-timeseries", response_model=list[TimeSeriesDatapoint])
async def get_function_usage_timeseries(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
) -> list[TimeSeriesDatapoint]:
    api_key_ids_sql_list = _get_project_api_key_ids_sql_list(context)

    if not api_key_ids_sql_list:
        return []

    query = f"""
SELECT
  time_bucket('1d', start_timestamp)::DATE AS x,
  regexp_replace(url_path, '/v1/functions/([A-Z0-9_]+)/execute', '\\1') AS function_name,
  COUNT(*) AS amount
FROM records
WHERE attributes->>'http.user_agent' LIKE '%python%'
  AND attributes->>'fastapi.route.name' = 'execute'
  AND trace_id IN (SELECT trace_id FROM records
WHERE attributes->>'api_key_id' IN ({api_key_ids_sql_list}))
GROUP BY function_name, x
ORDER BY x DESC;
    """

    async with AsyncLogfireQueryClient(read_token=config.LOGFIRE_READ_TOKEN) as client:
        json_rows = await client.query_json_rows(
            sql=query, min_timestamp=datetime.now() - timedelta(days=7)
        )

        # Transform the data format
        raw_rows = json_rows["rows"]
        date_grouped = {}
        for row in raw_rows:
            date = row["x"]
            function = row["function_name"]
            amount = row["amount"]

            if date not in date_grouped:
                date_grouped[date] = {"date": date}

            date_grouped[date][function] = amount

        # Convert to list format and use the TimeSeriesDatapoint model
        return [TimeSeriesDatapoint(**data) for data in date_grouped.values()]
