"""LogActor model."""

from pydantic import BaseModel, ConfigDict, Field


class LogActor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="id")
    type: str = Field(alias="type")
    alternate_id: str | None = Field(default=None, alias="alternateId")
    display_name: str | None = Field(default=None, alias="displayName")
    detail_entry: dict[str, str] | None = Field(default=None, alias="detailEntry")
