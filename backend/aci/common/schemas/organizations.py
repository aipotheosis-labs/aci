from pydantic import BaseModel, EmailStr

from aci.common.enums import OrganizationRole


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: OrganizationRole
