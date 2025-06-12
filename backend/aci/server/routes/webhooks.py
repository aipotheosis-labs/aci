import secrets
import string
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session
from svix import Webhook, WebhookVerificationError

from aci.common.db import crud
from aci.common.enums import OrganizationRole
from aci.common.logging_setup import get_logger
from aci.server import config
from aci.server import dependencies as deps
from aci.server.acl import get_propelauth

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
            f"Webhook verification error, "
            f"error={e!s} "
            f"error_type={type(e).__name__} "
            f"svix_id={headers.get('svix-id')} "
            f"svix_timestamp={headers.get('svix-timestamp')} "
            f"svix_signature={headers.get('svix-signature')}"
        )
        return

    if msg["event_type"] != "user.created":
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.error(f"Webhook event is not user.created, event={msg['event']}")
        return

    user = auth.fetch_user_metadata_by_user_id(msg["user_id"], include_orgs=True)
    if user is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        logger.error(f"User not found, user_id={msg['user_id']}")
        return

    logger.info(f"New user has signed up, user_id={user.user_id}")

    # No-Op if user already has a Personal Organization
    # This shouldn't happen because each user can only be created once
    if user.org_id_to_org_info:
        for org_id, org_info in user.org_id_to_org_info.items():
            # TODO: propel auth type hinting bug: org_info is not a dataclass but a dict here
            org_metadata = org_info["org_metadata"]
            if not isinstance(org_metadata, dict):
                logger.error(
                    f"Org metadata is not a dict, org_id={org_id}, org_metadata={org_metadata}"
                )
                response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                return

            if org_metadata["personal"] is True:
                response.status_code = status.HTTP_409_CONFLICT
                logger.error(
                    f"User already has a personal organization, "
                    f"user_id={user.user_id} "
                    f"org_id={org_id}"
                )
                return

    org = auth.create_org(
        name=f"Personal {_generate_secure_random_alphanumeric_string()}",
        max_users=1,
    )
    logger.info(
        f"Created a default personal org for new user, user_id={user.user_id}, org_id={org.org_id}"
    )

    auth.update_org_metadata(org_id=org.org_id, metadata={"personal": True})
    logger.info(
        f"Updated org metadata (personal=True) for default personal org, "
        f"user_id={user.user_id}, "
        f"org_id={org.org_id}"
    )

    auth.add_user_to_org(user_id=user.user_id, org_id=org.org_id, role=OrganizationRole.OWNER)
    logger.info(
        f"Added new user to default personal org, user_id={user.user_id}, org_id={org.org_id}"
    )

    org_id_uuid = _convert_org_id_to_uuid(org.org_id)
    project = crud.projects.create_project(db_session, org_id_uuid, "Default Project")

    # Create a default Agent for the project
    agent = crud.projects.create_agent(
        db_session,
        project.id,
        name="Default Agent",
        description="Default Agent",
        allowed_apps=[],
        custom_instructions={},
    )
    db_session.commit()

    logger.info(
        f"Created default project and agent for new user, "
        f"user_id={user.user_id}, "
        f"org_id={org.org_id} "
        f"project_id={project.id} "
        f"agent_id={agent.id}"
    )


def _generate_secure_random_alphanumeric_string(length: int = 6) -> str:
    charset = string.ascii_letters + string.digits

    secure_random_base64 = "".join(secrets.choice(charset) for _ in range(length))
    return secure_random_base64


def _convert_org_id_to_uuid(org_id: str | UUID) -> UUID:
    if isinstance(org_id, str):
        return UUID(org_id)
    elif isinstance(org_id, UUID):
        return org_id
    else:
        raise TypeError(f"org_id must be a str or UUID, got {type(org_id).__name__}")
