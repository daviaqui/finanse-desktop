import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

APPLICATION_ID = 0x46494E41
LATEST_REVISION = "desktop_002"


def migrate(path: Path, revision: str = "head") -> None:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "migrations"))
    engine = create_engine(f"sqlite:///{path}")
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, revision)
    finally:
        engine.dispose()
    with sqlite3.connect(path) as db:
        db.execute(f"PRAGMA application_id={APPLICATION_ID}")


def initialize() -> None:
    from app.core.config import DATA_DIR, DB_PATH, PROFILE_ID
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.services.categories import create_default_categories

    DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as db:
            if db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
                raise RuntimeError("O arquivo local não é um banco FinanSee Desktop")
            version = db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        if version not in ("desktop_001", LATEST_REVISION):
            raise RuntimeError("Versão de banco incompatível; use a versão correspondente do aplicativo")
        if version != LATEST_REVISION:
            # Preserve a consistent pre-upgrade copy before applying any migration.
            with (
                sqlite3.connect(DB_PATH) as source,
                sqlite3.connect(DATA_DIR / f"pre-upgrade-{version}.sqlite3") as target,
            ):
                source.backup(target)
    migrate(DB_PATH)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA journal_mode=WAL")
    with SessionLocal() as db:
        if db.get(User, PROFILE_ID) is None:
            if db.query(User).count():
                raise RuntimeError("Banco contém um perfil incompatível")
            user = User(
                id=PROFILE_ID, name="Meu perfil", email="local@finanse.example", password_hash="disabled"
            )
            db.add(user)
            db.flush()
            create_default_categories(db, user)
            db.commit()
