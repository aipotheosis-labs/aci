from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from aci.common.db.sql_models import Subscription
from aci.common.logging_setup import get_logger
from aci.common.schemas.subscription import SubscriptionUpdate

logger = get_logger(__name__)


def get_subscription_by_org_id(db_session: Session, org_id: UUID) -> Subscription | None:
    """
    Get a subscription by organization ID.
    """
    statement = (
        select(Subscription)
        .filter_by(org_id=org_id)
        .with_for_update()  # lock the row for the duration of the transaction
    )
    return db_session.execute(statement).scalar_one_or_none()


def get_subscription_by_stripe_id(
    db_session: Session, stripe_subscription_id: str
) -> Subscription | None:
    """
    Get a subscription by Stripe subscription ID.
    """
    statement = (
        select(Subscription)
        .filter_by(stripe_subscription_id=stripe_subscription_id)
        .with_for_update()  # lock the row for the duration of the transaction
    )
    return db_session.execute(statement).scalar_one_or_none()


def update_subscription_by_stripe_id(
    db_session: Session, stripe_subscription_id: str, subscription_update: SubscriptionUpdate
) -> Subscription | None:
    """
    Update subscription status based on Stripe subscription ID.
    """
    update_data = subscription_update.model_dump(exclude_unset=True)
    if not update_data:
        logger.info(
            "No fields to update for subscription",
            extra={"stripe_subscription_id": stripe_subscription_id},
        )
        # Need to fetch the subscription to return it
        return get_subscription_by_stripe_id(db_session, stripe_subscription_id)

    statement = (
        update(Subscription)
        .filter_by(stripe_subscription_id=stripe_subscription_id)
        .values(**update_data)
        .returning(Subscription)  # Return the updated object
    )
    result = db_session.execute(statement)
    updated_subscription = result.scalar_one_or_none()
    db_session.flush()  # Ensure changes are persisted before potential refresh

    if updated_subscription:
        # No need to refresh as returning() fetches the updated state
        logger.info(
            "Updated subscription",
            extra={"stripe_subscription_id": stripe_subscription_id},
        )
    else:
        logger.warning(
            "Subscription not found for stripe_subscription_id during update attempt.",
            extra={"stripe_subscription_id": stripe_subscription_id},
        )
    return updated_subscription


def delete_subscription_by_stripe_id(db_session: Session, stripe_subscription_id: str) -> None:
    """
    Mark a subscription as deleted by Stripe subscription ID. Returns True if marked, False otherwise.
    """
    subscription = get_subscription_by_stripe_id(db_session, stripe_subscription_id)
    if not subscription:
        logger.warning(
            f"Subscription not found for stripe_subscription_id={stripe_subscription_id} during delete attempt."
        )
        return

    db_session.delete(subscription)
    db_session.flush()
    logger.info(
        "Deleted subscription",
        extra={"stripe_subscription_id": stripe_subscription_id},
    )
