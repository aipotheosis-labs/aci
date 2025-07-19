from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from aci.common.db.sql_models import WebsiteEvaluation
from aci.common.enums import WebsiteEvaluationStatus
from aci.common.logging_setup import get_logger

logger = get_logger(__name__)


def get_website_evaluation_by_url_and_linked_account(
    db_session: Session, linked_account_id: UUID, url: str
) -> WebsiteEvaluation | None:
    statement = select(WebsiteEvaluation).filter_by(linked_account_id=linked_account_id, url=url)
    return db_session.execute(statement).scalar_one_or_none()


def mark_website_evaluation_as_in_progress(
    db_session: Session, linked_account_id: UUID, url: str
) -> WebsiteEvaluation:
    """
    Create or update a website evaluation record with IN_PROGRESS status.

    If an evaluation already exists for this linked_account + URL combination,
    it will be updated. Otherwise, a new record is created.

    Args:
        db_session: Database session
        linked_account_id: ID of the linked account
        url: URL to evaluate

    Returns:
        WebsiteEvaluation record with IN_PROGRESS status

        Note:
        TODO: Consider creating a new WebsiteEvaluation record for each evaluation request
        instead of reusing/updating existing records. This approach would:
        - Provide a complete audit trail of all evaluation attempts
        - Track evaluation history and frequency per URL
        - Allow analysis of evaluation performance over time
        - Preserve original evaluation results even when re-evaluating
        Current implementation reuses records to prevent table bloat, but audit trail
        approach would require implementing a cleanup process for old records.
    """
    # Try to lock the record if it exists, fail immediately if already locked
    statement = (
        select(WebsiteEvaluation)
        .filter_by(linked_account_id=linked_account_id, url=url)
        .with_for_update(nowait=True)
    )
    existing_evaluation = db_session.execute(statement).scalar_one_or_none()

    if existing_evaluation:
        # Reuse existing record - update status and clear result
        existing_evaluation.status = WebsiteEvaluationStatus.IN_PROGRESS
        existing_evaluation.result = ""
        db_session.flush()
        db_session.refresh(existing_evaluation)
        logger.debug(f"Updated existing evaluation record for URL: {url}")
        return existing_evaluation
    else:
        # Create new record
        evaluation = WebsiteEvaluation(
            linked_account_id=linked_account_id,
            url=url,
            status=WebsiteEvaluationStatus.IN_PROGRESS,
            result="",
        )
        db_session.add(evaluation)
        db_session.flush()
        db_session.refresh(evaluation)
        logger.debug(f"Created new evaluation record for URL: {url}")
        return evaluation


def update_website_evaluation_status_and_result(
    db_session: Session, evaluation_id: UUID, status: WebsiteEvaluationStatus, result: str
) -> WebsiteEvaluation:
    """
    Update the status and result of a website evaluation with database locking.

    Args:
        db_session: Database session
        evaluation_id: ID of the evaluation to update
        status: New status (COMPLETED or FAILED)
        result: Evaluation result content or error message

    Returns:
        Updated WebsiteEvaluation record

    Note:
        Uses row-level locking to prevent race conditions when updating evaluation status.
    """
    # Get evaluation with lock to prevent race conditions
    statement = select(WebsiteEvaluation).filter_by(id=evaluation_id).with_for_update()
    evaluation = db_session.execute(statement).scalar_one()

    evaluation.status = status
    evaluation.result = result
    db_session.flush()
    db_session.refresh(evaluation)

    logger.debug(f"Updated evaluation {evaluation_id} to status {status}")
    return evaluation
