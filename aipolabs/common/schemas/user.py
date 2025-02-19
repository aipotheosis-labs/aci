from uuid import UUID

from pydantic import BaseModel

from aipolabs.common.enums import SubscriptionPlan


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: UUID


class UserCreate(BaseModel):
    identity_provider: str
    user_id_by_provider: str
    name: str
    email: str
    profile_picture: str | None = None
    plan: SubscriptionPlan = SubscriptionPlan.FREE


class IdentityProviderUserInfo(BaseModel):
    iss: str
    sub: str
    name: str
    email: str
    picture: str | None = None
