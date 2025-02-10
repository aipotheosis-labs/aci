from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aipolabs.common.db.sql_models import (
    MAX_STRING_LENGTH,
    LinkedAccount,
    SecurityScheme,
)


class LinkedAccountOAuth2Create(BaseModel):
    app_name: str
    linked_account_owner_id: str


class LinkedAccountAPIKeyCreate(BaseModel):
    app_name: str
    linked_account_owner_id: str
    api_key: str


class LinkedAccountDefaultCreate(BaseModel):
    app_name: str
    linked_account_owner_id: str


class LinkedAccountOAuth2CreateState(BaseModel):
    project_id: UUID
    app_name: str
    linked_account_owner_id: str = Field(..., max_length=MAX_STRING_LENGTH)
    redirect_uri: str
    code_verifier: str
    nonce: str | None = None


class LinkedAccountPublic(BaseModel):
    id: UUID
    project_id: UUID
    app_name: str
    linked_account_owner_id: str
    security_scheme: SecurityScheme
    # NOTE: unnecessary to expose the security credentials
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def extract_app_name(cls, data: Any) -> Any:
        if isinstance(data, LinkedAccount):
            data["app_name"] = data.app.name
        return data


class LinkedAccountsList(BaseModel):
    app_name: str | None = None
    linked_account_owner_id: str | None = None
