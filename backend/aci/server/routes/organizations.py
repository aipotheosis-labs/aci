from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from propelauth_fastapi import User

from aci.common.enums import OrganizationRole
from aci.common.logging_setup import get_logger
from aci.server import acl

router = APIRouter()
logger = get_logger(__name__)

auth = acl.get_propelauth()


@router.post("/invite", status_code=status.HTTP_204_NO_CONTENT)
async def invite_member(
    user: Annotated[User, Depends(auth.require_user)],
    org_id: Annotated[UUID, Header(alias="X-ACI-ORG-ID")],
    email: str,
    role: OrganizationRole = OrganizationRole.MEMBER,
) -> None:
    """
    Invite a member to the organization.
    Only organization owners and admins can invite new members.
    """
    logger.info(
        "inviting member to organization",
        extra={
            "user_id": user.user_id,
            "org_id": org_id,
            "invitee_email": email,
            "role": role,
        },
    )

    # Only owners and admins can invite members
    acl.require_org_member_with_minimum_role(user, org_id, OrganizationRole.ADMIN)

    # Create the invitation
    auth.create_org_invitation(
        org_id=str(org_id),
        email=email,
        role=role,
    )


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user: Annotated[User, Depends(auth.require_user)],
    org_id: Annotated[UUID, Header(alias="X-ACI-ORG-ID")],
    member_id: str,
) -> None:
    """
    Remove a member from the organization.
    Only organization owners can remove members.
    Members cannot remove themselves - they should use the leave endpoint instead.
    """
    logger.info(
        "removing member from organization",
        extra={
            "user_id": user.user_id,
            "org_id": org_id,
            "member_id": member_id,
        },
    )

    # Only owners can remove members
    acl.require_org_member_with_minimum_role(user, org_id, OrganizationRole.OWNER)

    # Prevent removing yourself
    if member_id == user.user_id:
        raise ValueError(
            "Cannot remove yourself from the organization. Use the leave endpoint instead."
        )

    # Remove the member
    auth.remove_user_from_org(
        org_id=str(org_id),
        user_id=member_id,
    )


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_organization(
    user: Annotated[User, Depends(auth.require_user)],
    org_id: Annotated[UUID, Header(alias="X-ACI-ORG-ID")],
) -> None:
    """
    Leave the organization.
    Members can leave organizations they are part of.
    Organization owners cannot leave if they are the only owner.
    """
    logger.info(
        "leaving organization",
        extra={
            "user_id": user.user_id,
            "org_id": org_id,
        },
    )

    # Check if user is the only owner
    org = user.get_org(str(org_id))
    if org.user_is_role(OrganizationRole.OWNER):
        # Get all owners
        owners = [member for member in org.members if member.role == OrganizationRole.OWNER]
        if len(owners) <= 1:
            raise ValueError(
                "Cannot leave the organization as the only owner. Please transfer ownership or add another owner first."
            )

    # Leave the organization
    auth.remove_user_from_org(
        org_id=str(org_id),
        user_id=user.user_id,
    )
