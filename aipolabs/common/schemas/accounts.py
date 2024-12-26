from uuid import UUID

from pydantic import BaseModel


class AccountCreate(BaseModel):
    integration_id: UUID
    account_name: str
    credentials: dict | None = None
