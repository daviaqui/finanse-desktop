"""SQLite online backups; restore is staged, validated, then transactionally applied."""

import os
import sqlite3
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import DATA_DIR, DB_PATH, PROFILE_ID
from app.db.migrations import APPLICATION_ID, LATEST_REVISION, migrate
from app.schemas.category import CategoryResponse
from app.schemas.transaction import TransactionCreate

MAX_BACKUP_BYTES = 256 * 1024 * 1024


def readonly(path: Path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def validate(path: Path) -> str:
    if not path.is_file() or not 512 <= path.stat().st_size <= MAX_BACKUP_BYTES:
        raise ValueError("Arquivo ausente ou tamanho inválido (limite: 256 MiB)")
    with readonly(path) as db:
        db.execute("PRAGMA trusted_schema=OFF")
        if db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("Selecione um backup do FinanSee Desktop")
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("O backup está corrompido")
        revision = db.execute("SELECT version_num FROM alembic_version").fetchall()
        if revision not in [[("desktop_001",)], [(LATEST_REVISION,)]]:
            raise ValueError("Versão de backup incompatível; use a versão correspondente do aplicativo")
        revision = revision[0][0]
        # Reject extra tables, views, triggers and altered constraints, not just table names.
        with tempfile.TemporaryDirectory(prefix="finanse-schema-") as temp:
            reference = Path(temp) / "reference.sqlite3"
            migrate(reference, revision)
            query = "SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            with sqlite3.connect(reference) as expected:
                if db.execute(query).fetchall() != expected.execute(query).fetchall():
                    raise ValueError("Estrutura de backup incompatível")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("O backup contém referências inválidas")
        profiles = db.execute("SELECT id, is_active FROM users").fetchall()
        if profiles != [(PROFILE_ID.hex, 1)]:
            raise ValueError("Perfil do backup incompatível")
        db.row_factory = sqlite3.Row
        for row in db.execute("SELECT * FROM categories"):
            if row["user_id"] != PROFILE_ID.hex:
                raise ValueError("Categoria com perfil inválido")
            CategoryResponse.model_validate(dict(row))
        for row in db.execute("SELECT *, typeof(amount) AS amount_type FROM transactions"):
            if row["user_id"] != PROFILE_ID.hex or row["amount_type"] != "integer":
                raise ValueError("Lançamento inválido")
            UUID(row["id"])
            datetime.fromisoformat(row["created_at"])
            datetime.fromisoformat(row["updated_at"])

            data = dict(row)
            data.update(
                amount=Decimal(row["amount"]) / 100, type=row["type"].lower(), status=row["status"].lower()
            )
            TransactionCreate.model_validate(data)
    return revision


def selected_path(value: str, *, writing: bool = False) -> Path:
    requested = Path(value).expanduser()
    if not requested.is_absolute():
        raise ValueError("Escolha um caminho absoluto")
    path = requested.resolve()
    internal = path == DATA_DIR or DATA_DIR in path.parents
    recovery = (
        path.parent == DATA_DIR
        and path.suffix == ".sqlite3"
        and path.name.startswith(("pre-restore-", "pre-upgrade-"))
    )
    if internal and (writing or not recovery):
        raise ValueError("Escolha um backup fora dos arquivos internos do aplicativo")
    return path


def snapshot(target: Path) -> None:
    # Build alongside target so os.replace is atomic even across filesystems.
    descriptor, temporary = tempfile.mkstemp(prefix=".finanse-", suffix=".sqlite3", dir=target.parent)
    os.close(descriptor)
    temp = Path(temporary)
    try:
        with readonly(DB_PATH) as source, sqlite3.connect(temp) as destination:
            source.backup(destination)
            destination.execute("PRAGMA journal_mode=DELETE")
        with temp.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)


def backup(value: str) -> None:
    snapshot(selected_path(value, writing=True))


def restore(value: str) -> Path:
    source_path = selected_path(value)
    # Never migrate or write to the selected source file.
    validate(source_path)
    with tempfile.TemporaryDirectory(prefix="restore-", dir=DATA_DIR) as temp:
        staged = Path(temp) / "validated.sqlite3"
        with readonly(source_path) as source, sqlite3.connect(staged) as destination:
            source.backup(destination)
        validate(staged)
        migrate(staged)
        validate(staged)
        recovery = DATA_DIR / f"pre-restore-{uuid4().hex}.sqlite3"
        snapshot(recovery)
        # Request gate ensures every ORM session is closed. SQLite backup updates the
        # live database in one write transaction, preserving its inode/WAL coherently.
        with readonly(staged) as source, sqlite3.connect(DB_PATH) as destination:
            source.backup(destination)
            destination.execute("PRAGMA journal_mode=WAL")
        return recovery
