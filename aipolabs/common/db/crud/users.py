"""
User (Aipolabs direct clients, not end users) CRUD operations
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import Subscription, User
from aipolabs.common.enums import SubscriptionStatus
from aipolabs.common.schemas.user import UserCreate


def create_user(db_session: Session, user_create: UserCreate) -> User:
    user = User(
        auth_provider=user_create.auth_provider,
        auth_user_id=user_create.auth_user_id,
        name=user_create.name,
        email=user_create.email,
        profile_picture=user_create.profile_picture,
    )
    db_session.add(user)
    db_subscription = Subscription(
        entity_id=user.id,
        plan=user_create.plan,
        status=SubscriptionStatus.ACTIVE,
    )
    db_session.add(db_subscription)
    return user


def user_exists(db_session: Session, user_id: UUID) -> bool:
    return db_session.execute(select(User).filter_by(id=user_id)).scalar_one_or_none() is not None


def get_user(db_session: Session, user_id: UUID) -> User | None:
    user: User | None = db_session.execute(select(User).filter_by(id=user_id)).scalar_one_or_none()
    return user


def get_user_by_auth_provider_id(
    db_session: Session, auth_provider: str, auth_user_id: str
) -> User | None:
    user: User | None = db_session.execute(
        select(User).filter_by(auth_provider=auth_provider, auth_user_id=auth_user_id)
    ).scalar_one_or_none()
    return user
