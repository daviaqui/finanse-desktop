import sqlite3

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import DATA_DIR
from app.core.exceptions import ApiError
from app.services.backup import backup, restore

router = APIRouter(prefix="/maintenance", tags=["Dados locais"])


class FileRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4096)
    confirmed: bool = False


@router.get("/info")
def info():
    return {"data_dir": str(DATA_DIR)}


@router.post("/backup")
def create_backup(payload: FileRequest):
    try:
        backup(payload.path)
        return {"message": "Backup salvo com sucesso."}
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise ApiError(
            status_code=422, detail=f"Não foi possível salvar o backup: {exc}", code="backup_failed"
        ) from exc


@router.post("/restore")
def restore_backup(payload: FileRequest):
    if not payload.confirmed:
        raise ApiError(
            status_code=422, detail="Confirme a substituição dos dados", code="confirmation_required"
        )
    try:
        recovery = restore(payload.path)
        return {"message": "Dados restaurados com sucesso.", "recovery_path": str(recovery)}
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise ApiError(
            status_code=422, detail=f"Backup inválido ou inacessível: {exc}", code="restore_failed"
        ) from exc
