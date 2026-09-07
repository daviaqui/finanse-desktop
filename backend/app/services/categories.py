from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.user import User

DEFAULT_CATEGORIES = [
    ("Moradia", "#8b5cf6", "house"),
    ("Alimentação", "#f97316", "utensils"),
    ("Transporte", "#3b82f6", "car"),
    ("Saúde", "#ef4444", "heart"),
    ("Lazer", "#ec4899", "party-popper"),
    ("Salário", "#10b981", "briefcase"),
    ("Investimentos", "#06b6d4", "trending-up"),
    ("Outros", "#64748b", "circle"),
]


def create_default_categories(db: Session, user: User) -> None:
    db.add_all(
        [
            Category(user_id=user.id, name=name, color=color, icon=icon)
            for name, color, icon in DEFAULT_CATEGORIES
        ]
    )


def user_owns_category(db: Session, user: User, category_id: object) -> bool:
    return (
        db.scalar(select(Category.id).where(Category.id == category_id, Category.user_id == user.id))
        is not None
    )
