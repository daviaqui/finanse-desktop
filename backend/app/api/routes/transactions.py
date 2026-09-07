from datetime import date
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.core.exceptions import ApiError
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionList,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.categories import user_owns_category

router = APIRouter(prefix="/transactions", tags=["Lançamentos"])


@router.get("", response_model=TransactionList)
def list_transactions(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    transaction_type: TransactionType | None = None,
    transaction_status: TransactionStatus | None = None,
    category_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> TransactionList:
    filters = [Transaction.user_id == current_user.id]
    if search:
        filters.append(
            or_(
                Transaction.description.ilike(f"%{search}%"),
                Transaction.notes.ilike(f"%{search}%"),
            )
        )
    if transaction_type:
        filters.append(Transaction.type == transaction_type)
    if transaction_status:
        filters.append(Transaction.status == transaction_status)
    if category_id:
        filters.append(Transaction.category_id == category_id)
    if date_from:
        filters.append(Transaction.transaction_date >= date_from)
    if date_to:
        filters.append(Transaction.transaction_date <= date_to)

    total = db.scalar(select(func.count(Transaction.id)).where(*filters)) or 0
    statement = (
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(*filters)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(statement))
    return TransactionList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: DbSession, current_user: CurrentUser) -> Transaction:
    if payload.category_id and not user_owns_category(db, current_user, payload.category_id):
        raise ApiError(status_code=422, detail="Categoria inválida", code="invalid_category")
    transaction = Transaction(user_id=current_user.id, **payload.model_dump())
    db.add(transaction)
    db.commit()
    statement = (
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction.id)
    )
    return db.scalar(statement)  # type: ignore[return-value]


def get_user_transaction(transaction_id: UUID, db: DbSession, current_user: CurrentUser) -> Transaction:
    transaction = db.scalar(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    )
    if not transaction:
        raise ApiError(
            status_code=404,
            detail="Lançamento não encontrado",
            code="transaction_not_found",
        )
    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: UUID, db: DbSession, current_user: CurrentUser) -> Transaction:
    return get_user_transaction(transaction_id, db, current_user)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: UUID,
    payload: TransactionUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Transaction:
    transaction = get_user_transaction(transaction_id, db, current_user)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("category_id") and not user_owns_category(db, current_user, changes["category_id"]):
        raise ApiError(status_code=422, detail="Categoria inválida", code="invalid_category")
    for key, value in changes.items():
        setattr(transaction, key, value)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    transaction = get_user_transaction(transaction_id, db, current_user)
    db.delete(transaction)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
