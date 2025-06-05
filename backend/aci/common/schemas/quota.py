from pydantic import BaseModel

from aci.common.schemas.plans import PlanFeatures


class QuotaResourceUsage(BaseModel):
    """single resource quota usage"""

    used: int
    limit: int
    remaining: int


class PlanInfo(BaseModel):
    """plan info"""

    name: str
    features: PlanFeatures


class QuotaUsageResponse(BaseModel):
    """complete quota usage response"""

    projects: QuotaResourceUsage
    linked_accounts: QuotaResourceUsage  # unique account owner IDs across org
    agents_credentials: QuotaResourceUsage  #  total org secrets in secrets table
    plan: PlanInfo
