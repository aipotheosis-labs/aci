from datetime import datetime
from typing import Annotated, Any, Literal, TypedDict, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from opensearchpy import NotFoundError, OpenSearch, RequestError
from pydantic import BaseModel

from aci.common.logging_setup import get_logger
from aci.server.config import OPENSEARCH_LOG_INDEX_PATTERN
from aci.server.dependencies import RequestContext, get_opensearch, get_request_context

router = APIRouter()
logger = get_logger(__name__)


class FunctionExecutionLogEntry(BaseModel):
    log_search_type: Literal["function_execution"] = "function_execution"
    timestamp: datetime
    project_id: UUID
    agent_id: UUID | None = None
    function_execution_app_name: str | None = None
    function_execution_function_name: str | None = None
    function_execution_input: str | None = None
    function_execution_linked_account_owner_id: str | None = None
    function_execution_result_success: bool | None = None
    function_execution_result_error: str | None = None
    function_execution_result_data: str | None = None


class LogSearchResponse(BaseModel):
    logs: list[FunctionExecutionLogEntry]
    total: int
    page: int
    page_size: int


class OpenSearchHit(TypedDict):
    _source: dict[str, Any]


class OpenSearchHits(TypedDict):
    hits: list[OpenSearchHit]
    total: dict[str, int]


class OpenSearchResponse(TypedDict):
    hits: OpenSearchHits


@router.get("/search", response_model=LogSearchResponse)
async def search_logs(
    context: Annotated[RequestContext, Depends(get_request_context)],
    opensearch: Annotated[OpenSearch, Depends(get_opensearch)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of results per page"),
    app_name: str | None = Query(None, description="Filter by app name"),
    function_name: str | None = Query(None, description="Filter by function name"),
    log_search_type: str | None = Query(None, description="Filter by log search type"),
) -> LogSearchResponse:
    """
    Search logs with optional query string and request ID.
    TODO: currently only supports function execution logs.
    TODO: add support for other log types in this unified endpoint.
    """
    project_id = context.project.id
    org_id = context.project.org_id
    log_search_type = log_search_type or "function_execution"
    try:
        from_index = (page - 1) * page_size

        # Build filter conditions
        filter_conditions = [
            {"term": {"log_search_type.keyword": log_search_type}},
            {"term": {"project_id.keyword": str(project_id)}},
            {"term": {"org_id.keyword": str(org_id)}},
        ]

        if app_name:
            filter_conditions.append({"term": {"function_execution_app_name.keyword": app_name}})
        if function_name:
            filter_conditions.append(
                {"term": {"function_execution_function_name.keyword": function_name}}
            )

        # Basic search query
        search_body = {
            "sort": [{"@timestamp": {"order": "desc"}}],
            "from": from_index,
            "size": page_size,
            "query": {"bool": {"filter": filter_conditions}},
        }

        response = cast(
            OpenSearchResponse,
            opensearch.search(
                index=OPENSEARCH_LOG_INDEX_PATTERN,
                body=search_body,
            ),
        )

        hits = cast(list[OpenSearchHit], response["hits"]["hits"])  # type: ignore
        total = response["hits"]["total"]["value"]

        logs = []
        for hit in hits:
            source = hit["_source"]
            logs.append(
                FunctionExecutionLogEntry(
                    timestamp=datetime.fromisoformat(
                        source.get("@timestamp") or source.get("timestamp") or ""
                    ),
                    project_id=UUID(
                        source.get("project_id", "00000000-0000-0000-0000-000000000000")
                    ),
                    agent_id=UUID(source.get("agent_id")) if source.get("agent_id") else None,
                    log_search_type=source.get("log_search_type", "function_execution"),
                    function_execution_app_name=source.get("function_execution_app_name"),
                    function_execution_function_name=source.get("function_execution_function_name"),
                    function_execution_input=source.get("function_execution_input"),
                    function_execution_linked_account_owner_id=source.get(
                        "function_execution_linked_account_owner_id"
                    ),
                    function_execution_result_success=source.get(
                        "function_execution_result_success"
                    ),
                    function_execution_result_error=source.get("function_execution_result_error"),
                    function_execution_result_data=source.get("function_execution_result_data"),
                )
            )

        return LogSearchResponse(logs=logs, total=total, page=page, page_size=page_size)

    except NotFoundError as e:
        logger.error(f"Log index not found: {e!s}")
        raise HTTPException(status_code=404, detail=f"Log index not found: {e!s}") from e
    except RequestError as e:
        logger.error(f"OpenSearch request error: {e!s}")
        error_detail = {
            "error": str(e),
            "query": search_body if "search_body" in locals() else None,
            "status_code": getattr(e, "status_code", None),
            "error_type": getattr(e, "error", None),
        }
        raise HTTPException(status_code=400, detail=error_detail) from e
    except Exception as e:
        logger.error(f"Unexpected error during log search: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
