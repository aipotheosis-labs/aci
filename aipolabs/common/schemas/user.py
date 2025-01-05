from uuid import UUID

from pydantic import BaseModel

from aipolabs.common.enums import SubscriptionPlan


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: UUID


class UserCreate(BaseModel):
    auth_provider: str
    auth_user_id: str
    name: str
    email: str
    profile_picture: str | None = None
    plan: SubscriptionPlan = SubscriptionPlan.FREE
