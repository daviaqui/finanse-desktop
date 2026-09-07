from uuid import UUID

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DbSession
from app.core.exceptions import ApiError, CategoryNameConflictError
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categorias"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: DbSession, current_user: CurrentUser) -> list[Category]:
    return list(
        db.scalars(select(Category).where(Category.user_id == current_user.id).order_by(Category.name))
    )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: DbSession, current_user: CurrentUser) -> Category:
    existing = db.scalar(
        select(Category.id).where(
            Category.user_id == current_user.id,
            Category.name == payload.name,
        )
    )
    if existing:
        raise CategoryNameConflictError()
    category = Category(user_id=current_user.id, **payload.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryNameConflictError() from exc
    db.refresh(category)
    return category


def get_user_category(category_id: UUID, db: DbSession, current_user: CurrentUser) -> Category:
    category = db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    )
    if not category:
        raise ApiError(
            status_code=404,
            detail="Categoria não encontrada",
            code="category_not_found",
        )
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID, payload: CategoryUpdate, db: DbSession, current_user: CurrentUser
) -> Category:
    category = get_user_category(category_id, db, current_user)
    existing = db.scalar(
        select(Category.id).where(
            Category.user_id == current_user.id,
            Category.name == payload.name,
            Category.id != category.id,
        )
    )
    if existing:
        raise CategoryNameConflictError()
    for key, value in payload.model_dump().items():
        setattr(category, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryNameConflictError() from exc
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    category = get_user_category(category_id, db, current_user)
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
