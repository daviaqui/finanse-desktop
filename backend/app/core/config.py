import os
from pathlib import Path
from uuid import UUID

PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
DATA_DIR = Path(os.environ["FINANSE_DATA_DIR"]).resolve()
DB_PATH = DATA_DIR / "finanse.sqlite3"
TOKEN = os.environ["FINANSE_TOKEN"]
if len(TOKEN) < 32:
    raise RuntimeError("Credencial de inicialização inválida")
