from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from aipolabs.common.db.sql_models import SecurityScheme


class AccountCreate(BaseModel):
    integration_id: UUID
    account_name: str
    credentials: dict | None = None


class AccountCreateOAuth2State(BaseModel):
    integration_id: UUID
    project_id: UUID
    app_id: UUID
    # TODO: limit max length of account_name etc
    account_name: str
    iat: int
    nonce: str


class LinkedAccountPublic(BaseModel):
    id: UUID
    project_app_integration_id: UUID
    project_id: UUID
    app_id: UUID
    account_name: str
    security_scheme: SecurityScheme
    # NOTE: unnecessary to expose the security credentials
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ListLinkedAccountsFilters(BaseModel):
    """
    Filters for listing linked accounts.
    """

    app_id_or_name: str | None = Field(
        default=None,
        description="unique id or name of the app",
    )
    account_name: str | None = Field(
        default=None,
        description="the accountname used when linking the account",
    )
