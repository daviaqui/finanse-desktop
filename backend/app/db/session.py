from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import DB_PATH


class Base(DeclarativeBase):
    pass


engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}, poolclass=NullPool)


@event.listens_for(engine, "connect")
def configure_sqlite(connection, _):
    connection.create_function(
        "lower", 1, lambda value: value.casefold() if value is not None else None, deterministic=True
    )
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    # FastAPI sync generator entry/exit may run on different worker threads.
    # Serialization is handled by the ASGI request gate in main.py.
    with SessionLocal() as db:
        try:
            yield db
        except BaseException:
            db.rollback()
            raise
