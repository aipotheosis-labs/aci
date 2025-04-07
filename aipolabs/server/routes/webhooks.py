import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session
from svix import Webhook, WebhookVerificationError

from aipolabs.common.db import crud
from aipolabs.common.logging_setup import get_logger
from aipolabs.server import config, quota_manager
from aipolabs.server import dependencies as deps
from aipolabs.server.acl import setup_propelauth

# Create router instance
router = APIRouter()
logger = get_logger(__name__)

auth = setup_propelauth()


@router.post("/user-signup", status_code=status.HTTP_204_NO_CONTENT)
async def handle_user_signup_webhook(
    request: Request,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    response: Response,
) -> None:
    headers = request.headers
    payload = await request.body()

    # Verify the message following: https://docs.svix.com/receiving/verifying-payloads/how#python-fastapi
    try:
        wh = Webhook(config.SVIX_SIGNING_SECRET)
        msg = wh.verify(payload, dict(headers))
    except WebhookVerificationError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.error(
            "webhook verification error",
            extra={"error": e},
        )
        return

    user = auth.fetch_user_metadata_by_user_id(msg["user_id"])
    if user is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        logger.error(
            "user not found",
            extra={"user_id": msg["user_id"]},
        )
        return

    # TODO: If user already has a Personal Organization, do nothing
    # TODO: metadata: personal: true
    org = auth.create_org(
        name=f"Personal {_generate_secure_random_alphanumeric_string()}",
        max_users=10,
    )
    auth.add_user_to_org(user.user_id, org.org_id, "Owner")

    quota_manager.enforce_project_creation_quota(db_session, org.org_id)

    project = crud.projects.create_project(db_session, org.org_id, "Default Project")
    db_session.commit()

    # Create a default Agent for the project
    crud.projects.create_agent(
        db_session,
        project.id,
        name="Default Agent",
        description="Default Agent",
        allowed_apps=[],
        custom_instructions={},
    )
    db_session.commit()


def _generate_secure_random_alphanumeric_string(length: int = 6) -> str:
    charset = string.ascii_letters + string.digits

    secure_random_base64 = "".join(secrets.choice(charset) for _ in range(length))
    return secure_random_base64
