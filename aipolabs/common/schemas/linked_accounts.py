from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from aipolabs.common.db.sql_models import SecurityScheme


class LinkedAccountCreate(BaseModel):
    app_id: UUID
    linked_account_owner_id: str
    api_key: str | None = None


class LinkedAccountCreateOAuth2State(BaseModel):
    project_id: UUID
    app_id: UUID
    # TODO: limit max length of linked_account_owner_id etc
    linked_account_owner_id: str
    iat: int
    nonce: str


class LinkedAccountPublic(BaseModel):
    id: UUID
    project_id: UUID
    app_id: UUID
    linked_account_owner_id: str
    security_scheme: SecurityScheme
    # NOTE: unnecessary to expose the security credentials
    enabled: bool
    created_at: datetime
    updated_at: datetime


class LinkedAccountsList(BaseModel):
    """
    Filters for listing linked accounts.
    """

    app_id: UUID | None = None
    linked_account_owner_id: str | None = None
