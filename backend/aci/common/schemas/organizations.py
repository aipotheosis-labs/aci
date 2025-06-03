from pydantic import BaseModel

from aci.common.enums import OrganizationRole


class InviteMemberRequest(BaseModel):
    email: str
    role: OrganizationRole
