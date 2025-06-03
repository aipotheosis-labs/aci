from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from propelauth_fastapi import User

from aci.common.enums import OrganizationRole
from aci.common.logging_setup import get_logger
from aci.common.schemas.organizations import InviteMemberRequest
from aci.server import acl

router = APIRouter()
logger = get_logger(__name__)

auth = acl.get_propelauth()


@router.post("/invite", status_code=status.HTTP_204_NO_CONTENT)
async def invite_member(
    user: Annotated[User, Depends(auth.require_user)],
    org_id: Annotated[UUID, Header(alias="X-ACI-ORG-ID")],
    body: InviteMemberRequest,
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
            "invitee_email": body.email,
            "role": body.role,
        },
    )

    # Only owners and admins can invite members
    acl.require_org_member_with_minimum_role(user, org_id, OrganizationRole.ADMIN)

    # Create the invitation
    auth.invite_user_to_org(
        org_id=str(org_id),
        email=body.email,
        role=body.role,
    )


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user: Annotated[User, Depends(auth.require_user)],
    org_id: Annotated[UUID, Header(alias="X-ACI-ORG-ID")],
    member_id: str,
) -> None:
    """
    Remove a member from the organization.
    Only organization owners and admins can remove other members.
    Any member can remove themselves.
    """
    logger.info(
        "removing member from organization",
        extra={
            "user_id": user.user_id,
            "org_id": org_id,
            "member_id": member_id,
        },
    )

    # Allow users to remove themselves regardless of role
    if member_id == user.user_id:
        auth.remove_user_from_org(
            org_id=str(org_id),
            user_id=member_id,
        )
        return

    # Only owners and admins can remove other members
    acl.require_org_member_with_minimum_role(user, org_id, OrganizationRole.ADMIN)

    # Remove the member
    auth.remove_user_from_org(
        org_id=str(org_id),
        user_id=member_id,
    )


@router.get("/members", response_model=list[dict], status_code=status.HTTP_200_OK)
async def list_members(
    org_id: Annotated[UUID, Header(alias="X-ACI-ORG-ID")],
) -> list[dict]:
    """
    List all members of the organization.
    Any org member can view the list.
    """
    users_paged = auth.fetch_users_in_org(
        org_id=str(org_id),
        include_orgs=True,
    )
    members = []
    for member in users_paged.users:
        # Get the role for this org from org_id_to_org_info
        org_info = member.org_id_to_org_info.get(str(org_id), {})
        role = org_info.get("user_role", None)
        members.append(
            {
                "user_id": member.user_id,
                "email": member.email,
                "role": role,
                "first_name": getattr(member, "first_name", None),
                "last_name": getattr(member, "last_name", None),
            }
        )
    return members
