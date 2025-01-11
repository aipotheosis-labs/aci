"""
User (Aipolabs direct clients, not end users) CRUD operations
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import Subscription, User
from aipolabs.common.enums import SubscriptionStatus
from aipolabs.common.exceptions import UnexpectedDatabaseException
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.user import UserCreate

logger = get_logger(__name__)


def create_user(db_session: Session, user_create: UserCreate) -> User:
    """
    Create a user and a subscription for them.
    User existence (by identity_provider and user_id_by_provider) check should be done before calling this function.
    """
    try:
        user = User(
            identity_provider=user_create.identity_provider,
            user_id_by_provider=user_create.user_id_by_provider,
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
    except Exception:
        logger.exception("error creating user")
        raise UnexpectedDatabaseException()


def get_user(db_session: Session, identity_provider: str, user_id_by_provider: str) -> User | None:
    """
    Get a user by identity provider and user id by provider.
    """
    # TODO: should try/except in the caller
    try:
        user: User | None = db_session.execute(
            select(User).filter_by(
                identity_provider=identity_provider, user_id_by_provider=user_id_by_provider
            )
        ).scalar_one_or_none()
        return user
    except Exception:
        logger.exception("error getting user")
        raise UnexpectedDatabaseException()


def get_user_by_id(db_session: Session, user_id: UUID) -> User | None:
    """
    Get a user by ID.
    """
    user: User | None = db_session.execute(select(User).filter_by(id=user_id)).scalar_one_or_none()
    return user
