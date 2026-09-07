from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.category import Category


def test_category_input_and_conflicts_are_consistent(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    categories_before = client.get("/api/v1/categories", headers=auth_headers).json()

    blank = client.post(
        "/api/v1/categories",
        headers=auth_headers,
        json={"name": "   ", "color": "#123456", "icon": "circle"},
    )
    assert blank.status_code == 422
    assert len(client.get("/api/v1/categories", headers=auth_headers).json()) == len(categories_before)

    first = client.post(
        "/api/v1/categories",
        headers=auth_headers,
        json={"name": "  Mercado  ", "color": "#123456", "icon": "cart"},
    )
    assert first.status_code == 201
    assert first.json()["name"] == "Mercado"

    duplicate = client.post(
        "/api/v1/categories",
        headers=auth_headers,
        json={"name": " Mercado ", "color": "#abcdef", "icon": "circle"},
    )
    assert duplicate.status_code == 409

    second = client.post(
        "/api/v1/categories",
        headers=auth_headers,
        json={"name": "Viagens", "color": "#abcdef", "icon": "plane"},
    )
    renamed = client.put(
        f"/api/v1/categories/{second.json()['id']}",
        headers=auth_headers,
        json={"name": " Mercado ", "color": "#abcdef", "icon": "plane"},
    )
    assert renamed.status_code == 409


def test_category_database_conflict_is_409_and_rolls_back(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: Any,
) -> None:
    payload = {"name": "Mercado", "color": "#123456", "icon": "cart"}
    created = client.post("/api/v1/categories", headers=auth_headers, json=payload)
    assert created.status_code == 201

    original_scalar = Session.scalar
    original_rollback = Session.rollback
    rollback_calls = 0

    def bypass_category_check(self: Session, statement: Any, *args: Any, **kwargs: Any) -> Any:
        selected_entity = statement.column_descriptions[0].get("entity")
        if selected_entity is Category:
            return None
        return original_scalar(self, statement, *args, **kwargs)

    def tracked_rollback(self: Session) -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        original_rollback(self)

    monkeypatch.setattr(Session, "scalar", bypass_category_check)
    monkeypatch.setattr(Session, "rollback", tracked_rollback)

    conflict = client.post("/api/v1/categories", headers=auth_headers, json=payload)
    assert conflict.status_code == 409
    assert rollback_calls >= 1

    monkeypatch.setattr(Session, "scalar", original_scalar)
    categories = client.get("/api/v1/categories", headers=auth_headers)
    assert categories.status_code == 200


def test_transaction_description_is_trimmed_and_cannot_be_blank(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    payload = {
        "description": "   ",
        "amount": "10.00",
        "type": "expense",
        "transaction_date": date.today().isoformat(),
    }
    blank = client.post("/api/v1/transactions", headers=auth_headers, json=payload)
    assert blank.status_code == 422

    payload["description"] = "  Supermercado  "
    created = client.post("/api/v1/transactions", headers=auth_headers, json=payload)
    assert created.status_code == 201
    assert created.json()["description"] == "Supermercado"

    for invalid_description in ("   ", None):
        update = client.patch(
            f"/api/v1/transactions/{created.json()['id']}",
            headers=auth_headers,
            json={"description": invalid_description},
        )
        assert update.status_code == 422


def test_unexpected_transaction_failure_rolls_back(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: Any,
) -> None:
    original_commit = Session.commit
    original_rollback = Session.rollback
    rollback_calls = 0

    def fail_commit(_self: Session) -> None:
        raise RuntimeError("database unavailable")

    def tracked_rollback(self: Session) -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        original_rollback(self)

    monkeypatch.setattr(Session, "commit", fail_commit)
    monkeypatch.setattr(Session, "rollback", tracked_rollback)

    with pytest.raises(RuntimeError, match="database unavailable"):
        client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json={
                "description": "Supermercado",
                "amount": "10.00",
                "type": "expense",
                "transaction_date": date.today().isoformat(),
            },
        )
    assert rollback_calls >= 1

    monkeypatch.setattr(Session, "commit", original_commit)
    listing = client.get("/api/v1/transactions", headers=auth_headers)
    assert listing.json()["total"] == 0


def test_transactions_and_dashboard(client: TestClient, auth_headers: dict[str, str]) -> None:
    categories = client.get("/api/v1/categories", headers=auth_headers).json()
    salary = next(item for item in categories if item["name"] == "Salário")
    food = next(item for item in categories if item["name"] == "Alimentação")
    today = date.today().isoformat()

    income = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "description": "Salário",
            "amount": "5000.00",
            "type": "income",
            "status": "paid",
            "transaction_date": today,
            "category_id": salary["id"],
        },
    )
    expense = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "description": "Supermercado",
            "amount": "750.50",
            "type": "expense",
            "status": "paid",
            "transaction_date": today,
            "category_id": food["id"],
        },
    )
    assert income.status_code == 201
    assert expense.status_code == 201

    listing = client.get("/api/v1/transactions", headers=auth_headers).json()
    assert listing["total"] == 2
    assert listing["items"][0]["description"] in {"Salário", "Supermercado"}

    dashboard = client.get("/api/v1/dashboard", headers=auth_headers).json()
    assert dashboard["summary"]["income"] == "5000.00"
    assert dashboard["summary"]["expenses"] == "750.50"
    assert dashboard["summary"]["balance"] == "4249.50"
    assert dashboard["expenses_by_category"][0]["category"] == "Alimentação"

    deleted = client.delete(f"/api/v1/transactions/{expense.json()['id']}", headers=auth_headers)
    assert deleted.status_code == 204
