from fastapi import APIRouter

router = APIRouter(tags=["Saúde"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
