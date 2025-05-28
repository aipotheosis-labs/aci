import logging
from datetime import datetime
from typing import Annotated, Any, TypedDict, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from opensearchpy import NotFoundError, OpenSearch, RequestError
from pydantic import BaseModel

from aci.server.config import OPENSEARCH_LOG_INDEX_PATTERN
from aci.server.dependencies import RequestContext, get_opensearch, get_request_context

router = APIRouter()
logger = logging.getLogger(__name__)


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    project_id: UUID
    agent_id: UUID | None = None
    function_id: UUID | None = None
    metadata: dict = {}


class LogSearchResponse(BaseModel):
    logs: list[LogEntry]
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
    keyword: str | None = Query(None, description="Search query string"),
    request_id: str | None = Query(None, description="Request ID to search for"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of results per page"),
) -> LogSearchResponse:
    """
    Search logs with optional query string and request ID.
    """
    try:
        from_index = (page - 1) * page_size

        # Basic search query
        search_body = {
            "sort": [{"@timestamp": {"order": "desc"}}],
            "from": from_index,
            "size": page_size,
            "query": {"bool": {"must": [{"match": {"level": "INFO"}}]}},
        }

        # Add query if provided
        if keyword:
            search_body["query"]["bool"]["must"].append({"match": {"message": keyword}})  # type: ignore

        # Add request_id if provided
        if request_id:
            search_body["query"]["bool"]["must"].append({"term": {"request_id": request_id}})  # type: ignore

        logger.debug(f"Executing OpenSearch query with body: {search_body}")

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
                LogEntry(
                    timestamp=datetime.fromisoformat(
                        source.get("@timestamp") or source.get("timestamp") or ""
                    ),
                    level=source.get("level", "INFO"),
                    message=source.get("message", ""),
                    project_id=UUID(
                        source.get("project_id", "00000000-0000-0000-0000-000000000000")
                    ),
                    agent_id=UUID(source.get("agent_id")) if source.get("agent_id") else None,
                    function_id=UUID(source.get("function_id"))
                    if source.get("function_id")
                    else None,
                    metadata=source.get("metadata", {}),
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
