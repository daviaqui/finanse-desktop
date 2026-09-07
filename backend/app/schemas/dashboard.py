from decimal import Decimal

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    income: Decimal
    expenses: Decimal
    balance: Decimal
    pending_expenses: Decimal
    savings_rate: float


class CashFlowItem(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal


class CategoryExpenseItem(BaseModel):
    category: str
    color: str
    amount: Decimal
    percentage: float


class DashboardResponse(BaseModel):
    summary: SummaryResponse
    cash_flow: list[CashFlowItem]
    expenses_by_category: list[CategoryExpenseItem]
