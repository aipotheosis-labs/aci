from pydantic import BaseModel, ConfigDict


class DistributionDatapoint(BaseModel):
    """Model for distribution data visualization."""

    name: str
    value: float


class TimeSeriesDatapoint(BaseModel):
    """Model for time series data visualization."""

    date: str
    model_config = ConfigDict(extra="allow")
