from uuid import UUID

from pydantic import BaseModel


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
