from pydantic import BaseModel

from aci.common.schemas.plans import PlanFeatures


class PlanInfo(BaseModel):
    """plan info"""

    name: str
    features: PlanFeatures


class QuotaUsageResponse(BaseModel):
    """complete quota usage response"""

    projects_used: int
    linked_accounts_used: int  # unique account owner IDs across org
    agent_credentials_used: int  # total org secrets in secrets table
    plan: PlanInfo
