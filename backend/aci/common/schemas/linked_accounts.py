from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aci.common.db.sql_models import MAX_STRING_LENGTH, SecurityScheme


class LinkedAccountCreateBase(BaseModel):
    app_name: str
    linked_account_owner_id: str


class LinkedAccountOAuth2Create(LinkedAccountCreateBase):
    after_oauth2_link_redirect_url: str | None = None


class LinkedAccountAPIKeyCreate(LinkedAccountCreateBase):
    api_key: str


class LinkedAccountDefaultCreate(LinkedAccountCreateBase):
    pass


class LinkedAccountNoAuthCreate(LinkedAccountCreateBase):
    pass


class LinkedAccountUpdate(BaseModel):
    enabled: bool | None = None


class LinkedAccountOAuth2CreateState(BaseModel):
    project_id: UUID
    app_name: str
    linked_account_owner_id: str = Field(..., max_length=MAX_STRING_LENGTH)
    redirect_uri: str
    code_verifier: str
    after_oauth2_link_redirect_url: str | None = None


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
    last_used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LinkedAccountsList(BaseModel):
    app_name: str | None = None
    linked_account_owner_id: str | None = None
