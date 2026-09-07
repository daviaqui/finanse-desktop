from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import TransactionStatus, TransactionType
from app.schemas.category import CategoryResponse


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    type: TransactionType
    status: TransactionStatus = TransactionStatus.PAID
    transaction_date: date
    category_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("A descrição não pode ser vazia")
        return value.strip() if isinstance(value, str) else value


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=160)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    type: TransactionType | None = None
    status: TransactionStatus | None = None
    transaction_date: date | None = None
    category_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("A descrição não pode ser vazia")
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field in ("amount", "type", "status", "transaction_date"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError("Campo obrigatório não pode ser nulo")
        return self


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    amount: Decimal
    type: TransactionType
    status: TransactionStatus
    transaction_date: date
    category_id: UUID | None
    category: CategoryResponse | None
    notes: str | None
    created_at: datetime


class TransactionList(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    pages: int
