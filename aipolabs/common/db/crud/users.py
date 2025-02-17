"""
User (Aipolabs direct clients, not end users) CRUD operations
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import Subscription, User
from aipolabs.common.enums import SubscriptionStatus
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.user import UserCreate

logger = get_logger(__name__)


def create_user(db_session: Session, user_create: UserCreate) -> User:
    """
    Create a user and a subscription for them.
    User existence (by identity_provider and user_id_by_provider) check should be done before calling this function.
    """
    user = User(
        identity_provider=user_create.identity_provider,
        user_id_by_provider=user_create.user_id_by_provider,
        name=user_create.name,
        email=user_create.email,
        profile_picture=user_create.profile_picture,
    )
    db_session.add(user)
    subscription = Subscription(
        entity_id=user.id,
        plan=user_create.plan,
        status=SubscriptionStatus.ACTIVE,
    )
    db_session.add(subscription)
    db_session.flush()
    db_session.refresh(user)
    return user


def get_user(db_session: Session, identity_provider: str, user_id_by_provider: str) -> User | None:
    """
    Get a user by identity provider and user id by provider.
    """
    # TODO: should try/except in the caller?
    user: User | None = db_session.execute(
        select(User).filter_by(
            identity_provider=identity_provider, user_id_by_provider=user_id_by_provider
        )
    ).scalar_one_or_none()
    return user


def get_user_by_id(db_session: Session, user_id: UUID) -> User | None:
    """
    Retrieve a user by their unique identifier.
    
    This function queries the database using the given session to locate a user record with
    an id matching the provided UUID. If a matching user is found, the corresponding User
    object is returned; otherwise, None is returned.
    
    Parameters:
        db_session (Session): An active SQLAlchemy session for executing database operations.
        user_id (UUID): The unique identifier of the user to retrieve.
    
    Returns:
        User | None: The User object if found, or None if no user matches the provided id.
    """
    user: User | None = db_session.execute(select(User).filter_by(id=user_id)).scalar_one_or_none()
    return user


def get_total_number_of_users(db_session: Session) -> int:
    """
    Count the total number of user records in the database.
    
    This function executes a SQL query to count the number of user IDs in the User table using SQLAlchemy's ORM capabilities. The count is retrieved as a scalar value and returned as an integer.
    
    Parameters:
        db_session (Session): A SQLAlchemy session object used for database interaction.
    
    Returns:
        int: The total number of users present in the database.
    
    Raises:
        Any exceptions raised by the database layer during query execution should be handled by the caller.
    """
    return int(db_session.execute(select(func.count(User.id))).scalar_one())
