"""LogTransaction model."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from synthlog.schema.enums import TransactionType


class LogTransaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="id")
    type: TransactionType = Field(default=TransactionType.WEB, alias="type")
    detail: dict[str, Any] | None = Field(default=None, alias="detail")
