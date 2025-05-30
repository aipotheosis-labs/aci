from pydantic import BaseModel, Field


class PlanFeatures(BaseModel):
    linked_accounts: int
    api_calls_monthly: int
    agent_credentials: int
    developer_seats: int
    custom_oauth: bool
    log_retention_days: int
    projects: int


class PlanUpdate(BaseModel, extra="forbid"):
    stripe_product_id: str | None = Field(None)
    stripe_monthly_price_id: str | None = Field(None)
    stripe_yearly_price_id: str | None = Field(None)
    features: PlanFeatures | None = Field(None)
    is_public: bool | None = Field(None)
