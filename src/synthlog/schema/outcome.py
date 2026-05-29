"""LogOutcome model."""

from pydantic import BaseModel, ConfigDict, Field

from synthlog.schema.enums import OutcomeResult


class LogOutcome(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    result: OutcomeResult = Field(alias="result")
    reason: str | None = Field(default=None, alias="reason")
