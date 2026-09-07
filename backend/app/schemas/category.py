from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str = "#6366f1"
    icon: str = Field(default="circle", max_length=40)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if len(value) != 7 or not value.startswith("#"):
            raise ValueError("A cor deve estar no formato hexadecimal #RRGGBB")
        try:
            int(value[1:], 16)
        except ValueError as exc:
            raise ValueError("A cor deve estar no formato hexadecimal #RRGGBB") from exc
        return value.lower()


class CategoryUpdate(CategoryCreate):
    pass


class CategoryResponse(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
