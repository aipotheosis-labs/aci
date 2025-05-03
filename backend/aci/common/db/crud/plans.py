from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from aci.common.db.sql_models import Plan
from aci.common.schemas.plans import PlanFeatures, PlanUpdate


def get_by_name(db: Session, name: str) -> Plan | None:
    """Get a plan by its name."""
    stmt = select(Plan).where(Plan.name == name)
    return db.execute(stmt).scalar_one_or_none()


def get_by_id(db: Session, id: UUID) -> Plan | None:
    """Get a plan by its id."""
    stmt = select(Plan).where(Plan.id == id)
    return db.execute(stmt).scalar_one_or_none()


def get_by_stripe_price_id(db: Session, stripe_price_id: str) -> Plan | None:
    """Get a plan by its Stripe price id."""
    stmt = select(Plan).where(
        (Plan.stripe_monthly_price_id == stripe_price_id)
        | (Plan.stripe_yearly_price_id == stripe_price_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def create(
    db: Session,
    name: str,
    stripe_product_id: str,
    stripe_monthly_price_id: str,
    stripe_yearly_price_id: str,
    features: PlanFeatures,
    is_public: bool,
) -> Plan:
    """Create a new plan."""
    plan = Plan(
        name=name,
        stripe_product_id=stripe_product_id,
        stripe_monthly_price_id=stripe_monthly_price_id,
        stripe_yearly_price_id=stripe_yearly_price_id,
        features=features.model_dump(),
        is_public=is_public,
    )
    db.add(plan)
    db.flush()
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan: Plan, plan_update: PlanUpdate) -> Plan:
    """Update an existing plan using a Pydantic model.

    Args:
        db: The database session.
        plan: The existing Plan ORM object to update.
        plan_update: Pydantic model containing the fields to update.

    Returns:
        The updated Plan ORM object.
    """
    update_data = plan_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(plan, field, value)

    db.flush()
    db.refresh(plan)
    return plan
