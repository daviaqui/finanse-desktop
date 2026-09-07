import logging
from datetime import date
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.main import app


def test_expected_errors_follow_the_public_contract(client: TestClient, auth_headers: dict[str, str]) -> None:
    missing_credentials = client.get("/api/v1/categories")
    assert missing_credentials.status_code == 401
    assert missing_credentials.json() == {
        "detail": "Acesso local não autorizado",
        "code": "authentication_required",
    }

    validation = client.post(
        "/api/v1/categories",
        headers=auth_headers,
        json={"name": "   ", "color": "#123456", "icon": "circle"},
    )
    assert validation.status_code == 422
    assert validation.json() == {
        "detail": "Verifique os campos informados",
        "code": "validation_error",
    }

    payload = {"name": "Mercado", "color": "#123456", "icon": "cart"}
    assert client.post("/api/v1/categories", headers=auth_headers, json=payload).status_code == 201
    conflict = client.post("/api/v1/categories", headers=auth_headers, json=payload)
    assert conflict.status_code == 409
    assert conflict.json() == {
        "detail": "Você já possui uma categoria com esse nome",
        "code": "category_name_conflict",
    }

    missing_transaction = client.get(f"/api/v1/transactions/{uuid4()}", headers=auth_headers)
    assert missing_transaction.status_code == 404
    assert missing_transaction.json() == {
        "detail": "Lançamento não encontrado",
        "code": "transaction_not_found",
    }


def test_unmapped_integrity_error_uses_safe_fallback(auth_headers: dict[str, str], monkeypatch: Any) -> None:
    def fail_commit(_self: Session) -> None:
        raise IntegrityError("INSERT", {}, RuntimeError("constraint details"))

    monkeypatch.setattr(Session, "commit", fail_commit)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json={
                "description": "Supermercado",
                "amount": "10.00",
                "type": "expense",
                "transaction_date": date.today().isoformat(),
            },
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Conflito com dados existentes",
        "code": "data_integrity_conflict",
    }


def test_unexpected_error_is_logged_but_hidden_from_client(
    auth_headers: dict[str, str], monkeypatch: Any, caplog: Any
) -> None:
    def fail_commit(_self: Session) -> None:
        raise RuntimeError("database host and internal details")

    monkeypatch.setattr(Session, "commit", fail_commit)

    with caplog.at_level(logging.ERROR, logger="app.api.error_handlers"):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/transactions",
                headers=auth_headers,
                json={
                    "description": "Supermercado",
                    "amount": "10.00",
                    "type": "expense",
                    "transaction_date": date.today().isoformat(),
                },
            )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Erro interno do servidor",
        "code": "internal_server_error",
    }
    assert "database host and internal details" not in response.text
    assert "Unexpected error while processing POST /api/v1/transactions" in caplog.text


def test_web_auth_and_documentation_are_disabled(client, auth_headers):
    for path in ("/docs", "/openapi.json", "/api/v1/auth/me"):
        assert client.get(path, headers=auth_headers).status_code == 404
