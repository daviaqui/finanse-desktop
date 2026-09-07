from collections import defaultdict
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.dashboard import (
    CashFlowItem,
    CategoryExpenseItem,
    DashboardResponse,
    SummaryResponse,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

MONTH_NAMES = [
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
]


def shift_month(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: DbSession,
    current_user: CurrentUser,
    month: int = Query(default_factory=lambda: date.today().month, ge=1, le=12),
    year: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2200),
) -> DashboardResponse:
    selected_month = date(year, month, 1)
    period_end = shift_month(selected_month, 1)
    cash_flow_start = shift_month(selected_month, -5)

    transactions = list(
        db.scalars(
            select(Transaction)
            .options(selectinload(Transaction.category))
            .where(
                Transaction.user_id == current_user.id,
                Transaction.transaction_date >= cash_flow_start,
                Transaction.transaction_date < period_end,
            )
        )
    )

    income = Decimal("0")
    expenses = Decimal("0")
    pending_expenses = Decimal("0")
    cash_flow: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal("0"), "expenses": Decimal("0")}
    )
    category_totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))

    for item in transactions:
        month_key = item.transaction_date.strftime("%Y-%m")
        is_selected = selected_month <= item.transaction_date < period_end
        if item.status == TransactionStatus.PAID:
            key = "income" if item.type == TransactionType.INCOME else "expenses"
            cash_flow[month_key][key] += item.amount
            if is_selected and item.type == TransactionType.INCOME:
                income += item.amount
            elif is_selected and item.type == TransactionType.EXPENSE:
                expenses += item.amount
                category = item.category
                category_name = category.name if category else "Sem categoria"
                category_color = category.color if category else "#94a3b8"
                category_totals[(category_name, category_color)] += item.amount
        elif is_selected and item.type == TransactionType.EXPENSE:
            pending_expenses += item.amount

    total_category_expenses = sum(category_totals.values(), Decimal("0"))
    expenses_by_category = [
        CategoryExpenseItem(
            category=name,
            color=color,
            amount=amount,
            percentage=round(float(amount / total_category_expenses * 100), 1)
            if total_category_expenses
            else 0,
        )
        for (name, color), amount in sorted(category_totals.items(), key=lambda pair: pair[1], reverse=True)
    ]

    flow_items = []
    for offset in range(-5, 1):
        current = shift_month(selected_month, offset)
        values = cash_flow[current.strftime("%Y-%m")]
        flow_items.append(
            CashFlowItem(
                month=f"{MONTH_NAMES[current.month - 1]}/{str(current.year)[2:]}",
                income=values["income"],
                expenses=values["expenses"],
            )
        )

    savings_rate = round(float((income - expenses) / income * 100), 1) if income else 0
    return DashboardResponse(
        summary=SummaryResponse(
            income=income,
            expenses=expenses,
            balance=income - expenses,
            pending_expenses=pending_expenses,
            savings_rate=savings_rate,
        ),
        cash_flow=flow_items,
        expenses_by_category=expenses_by_category,
    )
