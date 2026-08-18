"""AutoZyte API request/response contracts."""

from pydantic import BaseModel, Field


class HypothesisRequest(BaseModel):
    vin: str | None = Field(default=None, example="SYNWP020140002")
    year: int | None = Field(default=None, ge=1900, le=2100)
    make: str | None = Field(default=None, example="Porsche")
    model: str | None = Field(default=None, example="911")
    engine: str | None = None
    complaint: str | None = Field(default=None, example="AOS / oil smell")
    mileage: int | None = Field(default=None, ge=0)
