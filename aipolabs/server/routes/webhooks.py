import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session
from svix import Webhook, WebhookVerificationError

from aipolabs.common.db import crud
from aipolabs.common.enums import OrganizationRole
from aipolabs.common.logging_setup import get_logger
from aipolabs.server import config
from aipolabs.server import dependencies as deps
from aipolabs.server.acl import get_propelauth

# Create router instance
router = APIRouter()
logger = get_logger(__name__)

auth = get_propelauth()


@router.post("/auth/user-created", status_code=status.HTTP_204_NO_CONTENT)
async def handle_user_created_webhook(
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
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "svix_id": headers.get("svix-id"),
                "svix_timestamp": headers.get("svix-timestamp"),
                "svix_signature": headers.get("svix-signature"),
            },
        )
        return

    if msg["event_type"] != "user.created":
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.error(
            "webhook event is not user.created",
            extra={"event": msg["event"]},
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

    logger.info(
        "a new user has signed up",
        extra={"user_id": user.user_id},
    )

    # No-Op if user already has a Personal Organization
    # This shouldn't happen because each user can only be created once
    if user.org_id_to_org_info:
        for user_org in user.org_id_to_org_info.values():
            if user_org.org_metadata.get("personal") is True:
                response.status_code = status.HTTP_409_CONFLICT
                logger.error(
                    "user already has a personal organization",
                    extra={"user_id": user.user_id, "org_id": user_org.org_id},
                )
                return

    org = auth.create_org(
        name=f"Personal {_generate_secure_random_alphanumeric_string()}",
        max_users=1,
    )
    auth.update_org_metadata(org_id=org.org_id, metadata={"personal": True})
    auth.add_user_to_org(user_id=user.user_id, org_id=org.org_id, role=OrganizationRole.OWNER)

    logger.info(
        "created a default personal org for new user",
        extra={
            "user_id": user.user_id,
            "org_id": org.org_id,
        },
    )

    project = crud.projects.create_project(db_session, org.org_id, "Default Project")

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

    logger.info(
        "created default project for new user",
        extra={
            "user_id": user.user_id,
            "org_id": org.org_id,
            "project_id": project.id,
        },
    )


def _generate_secure_random_alphanumeric_string(length: int = 6) -> str:
    charset = string.ascii_letters + string.digits

    secure_random_base64 = "".join(secrets.choice(charset) for _ in range(length))
    return secure_random_base64
