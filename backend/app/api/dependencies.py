from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import PROFILE_ID
from app.db.session import get_db
from app.models.user import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession) -> User:
    user = db.get(User, PROFILE_ID)
    if user is None:
        raise RuntimeError("Perfil local ausente")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
