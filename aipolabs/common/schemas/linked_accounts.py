from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from aipolabs.common.db.sql_models import MAX_STRING_LENGTH, SecurityScheme


class LinkedAccountOAuth2Create(BaseModel):
    app_id: UUID
    linked_account_owner_id: str


class LinkedAccountAPIKeyCreate(BaseModel):
    app_id: UUID
    linked_account_owner_id: str
    api_key: str


class LinkedAccountDefaultCreate(BaseModel):
    app_id: UUID
    linked_account_owner_id: str


class LinkedAccountOAuth2CreateState(BaseModel):
    project_id: UUID
    app_id: UUID
    linked_account_owner_id: str = Field(..., max_length=MAX_STRING_LENGTH)
    redirect_uri: str
    code_verifier: str
    nonce: str | None = None


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
    app_id: UUID | None = None
    linked_account_owner_id: str | None = None
