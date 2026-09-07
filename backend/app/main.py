import asyncio
import hmac

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.error_handlers import register_error_handlers
from app.api.routes import categories, dashboard, maintenance, transactions
from app.core.config import TOKEN

app = FastAPI(title="FinanSee Desktop", docs_url=None, redoc_url=None, openapi_url=None)


class LocalAccess:
    def __init__(self, app):
        self.app = app
        self.gate = asyncio.Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        supplied = headers.get(b"authorization", b"")
        if not hmac.compare_digest(supplied, f"Bearer {TOKEN}".encode()):
            response = JSONResponse(
                status_code=401,
                content={"detail": "Acesso local não autorizado", "code": "authentication_required"},
            )
            return await response(scope, receive, send)
        # No CORS: only the native Rust bridge may access the service.
        if b"origin" in headers:
            response = JSONResponse(
                status_code=403, content={"detail": "Origem não permitida", "code": "forbidden"}
            )
            return await response(scope, receive, send)
        async with self.gate:
            await self.app(scope, receive, send)


app.add_middleware(LocalAccess)
for router in (categories.router, dashboard.router, transactions.router, maintenance.router):
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


register_error_handlers(app)
