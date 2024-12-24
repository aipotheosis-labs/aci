from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aipolabs.common.logging import get_logger
from aipolabs.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)


@router.post("/")
async def link_account(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> None:
    """Link an account of an app to a project"""
    pass
