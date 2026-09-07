import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import DB_PATH, PROFILE_ID
from app.db.migrations import APPLICATION_ID, initialize, migrate
from app.services.backup import backup, restore, validate


def transaction(client, headers, **changes):
    payload = {
        "description": "Teste",
        "amount": "0.10",
        "type": "expense",
        "status": "paid",
        "transaction_date": "2026-09-06",
    }
    payload.update(changes)
    response = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_money_dashboard_and_periods(client, auth_headers):
    category = client.get("/api/v1/categories", headers=auth_headers).json()[0]
    transaction(client, auth_headers, type="income", amount="100.00")
    for value in ["0.10", "0.20", "0.30"]:
        transaction(client, auth_headers, amount=value, category_id=category["id"])
    transaction(client, auth_headers, amount="7.89", status="pending")
    transaction(client, auth_headers, amount="99.99", type="income", status="pending")
    transaction(client, auth_headers, amount="1.01", transaction_date="2026-08-31")
    transaction(client, auth_headers, amount="22.00", transaction_date="2026-10-01")
    data = client.get("/api/v1/dashboard?month=9&year=2026", headers=auth_headers).json()
    assert data["summary"] == {
        "income": "100.00",
        "expenses": "0.60",
        "balance": "99.40",
        "pending_expenses": "7.89",
        "savings_rate": 99.4,
    }
    assert data["cash_flow"][-2]["expenses"] == "1.01"
    assert data["cash_flow"][-1]["expenses"] == "0.60"
    assert data["expenses_by_category"][0]["amount"] == "0.60"
    with sqlite3.connect(DB_PATH) as db:
        assert set(db.execute("SELECT typeof(amount) FROM transactions")) == {("integer",)}
    maximum = transaction(client, auth_headers, amount="999999999999.99")
    assert maximum["amount"] == "999999999999.99"


@pytest.mark.parametrize("amount", ["0", "-1.00", "0.001", "1000000000000.00", "NaN", "Infinity"])
def test_invalid_money(client, auth_headers, amount):
    result = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"description": "x", "amount": amount, "type": "expense", "transaction_date": "2026-09-06"},
    )
    assert result.status_code == 422


def test_crud_filters_pagination_and_deleted_category(client, auth_headers):
    category = client.post("/api/v1/categories", headers=auth_headers, json={"name": "Café especial"}).json()
    item = transaction(client, auth_headers, description="Café especial", category_id=category["id"])
    transaction(client, auth_headers, description="Outro", status="pending")
    page = client.get("/api/v1/transactions?page_size=1", headers=auth_headers).json()
    assert page["pages"] == 2 and page["total"] == 2
    second = client.get("/api/v1/transactions?page_size=1&page=2", headers=auth_headers).json()
    assert second["items"][0]["id"] != page["items"][0]["id"]
    filtered = client.get(
        "/api/v1/transactions",
        headers=auth_headers,
        params={
            "search": "especial",
            "category_id": category["id"],
            "transaction_type": "expense",
            "transaction_status": "paid",
            "date_from": "2026-09-01",
            "date_to": "2026-09-30",
        },
    ).json()
    assert filtered["total"] == 1
    assert (
        client.patch(
            f"/api/v1/transactions/{item['id']}",
            headers=auth_headers,
            json={"amount": "1.23", "status": "pending"},
        ).json()["amount"]
        == "1.23"
    )
    for field in ["amount", "type", "status", "transaction_date"]:
        assert (
            client.patch(
                f"/api/v1/transactions/{item['id']}", headers=auth_headers, json={field: None}
            ).status_code
            == 422
        )
    assert client.delete(f"/api/v1/categories/{category['id']}", headers=auth_headers).status_code == 204
    saved = client.get(f"/api/v1/transactions/{item['id']}", headers=auth_headers).json()
    assert saved["category_id"] is None and saved["category"] is None
    assert client.delete(f"/api/v1/transactions/{item['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/v1/transactions/{item['id']}", headers=auth_headers).status_code == 404


def test_profile_defaults_persist_without_reseeding(client, auth_headers):
    categories = client.get("/api/v1/categories", headers=auth_headers).json()
    assert len(categories) == 8
    client.delete(f"/api/v1/categories/{categories[0]['id']}", headers=auth_headers)
    transaction(client, auth_headers)
    initialize()
    assert len(client.get("/api/v1/categories", headers=auth_headers).json()) == 7
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["total"] == 1
    assert (
        client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json={
                "description": "x",
                "amount": "1.00",
                "type": "expense",
                "transaction_date": "2026-09-06",
                "category_id": str(uuid4()),
            },
        ).status_code
        == 422
    )


def test_backup_restore_and_confirmation(client, auth_headers, tmp_path):
    item = transaction(client, auth_headers, amount="123.45")
    path = tmp_path / "backup.sqlite3"
    assert (
        client.post("/api/v1/maintenance/backup", headers=auth_headers, json={"path": str(path)}).status_code
        == 200
    )
    assert validate(path) == "desktop_002"
    client.delete(f"/api/v1/transactions/{item['id']}", headers=auth_headers)
    denied = client.post("/api/v1/maintenance/restore", headers=auth_headers, json={"path": str(path)})
    assert denied.status_code == 422
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["total"] == 0
    response = client.post(
        "/api/v1/maintenance/restore", headers=auth_headers, json={"path": str(path), "confirmed": True}
    )
    assert response.status_code == 200, response.text
    assert Path(response.json()["recovery_path"]).exists()
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["items"][0]["amount"] == "123.45"
    initialize()
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["total"] == 1


@pytest.mark.parametrize(
    "damage",
    ["garbage", "foreign", "future", "trigger", "invalid_reference", "wrong_profile", "fractional_money"],
)
def test_invalid_restore_preserves_live_data(client, auth_headers, tmp_path, damage):
    transaction(client, auth_headers)
    path = tmp_path / "bad.sqlite3"
    backup(str(path))
    if damage == "garbage":
        path.write_bytes(b"not a database")
    else:
        with sqlite3.connect(path) as db:
            if damage == "foreign":
                db.execute("PRAGMA application_id=0")
            if damage == "future":
                db.execute("UPDATE alembic_version SET version_num='desktop_999'")
            if damage == "trigger":
                db.execute(
                    "CREATE TRIGGER malicious AFTER INSERT ON transactions BEGIN DELETE FROM categories; END"
                )
            if damage == "invalid_reference":
                db.execute("UPDATE transactions SET category_id=?", (uuid4().hex,))
            if damage == "wrong_profile":
                db.execute("UPDATE users SET id=?", (uuid4().hex,))
            if damage == "fractional_money":
                db.execute("PRAGMA ignore_check_constraints=ON")
                db.execute("UPDATE transactions SET amount=0.1")
    with pytest.raises((ValueError, sqlite3.Error)):
        restore(str(path))
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["total"] == 1


def test_fresh_and_existing_migration_and_old_backup(tmp_path):
    path = tmp_path / "old.sqlite3"
    migrate(path, "desktop_001")
    with sqlite3.connect(path) as db:
        db.execute(
            "INSERT INTO users (id,name,email,password_hash,is_active) VALUES (?,?,?,?,1)",
            (PROFILE_ID.hex, "Meu perfil", "local@finanse.example", "disabled"),
        )
        db.execute(
            "INSERT INTO transactions (id,user_id,description,amount,type,status,transaction_date) VALUES (?,?,?,?,'INCOME','PAID','2026-09-01')",
            (uuid4().hex, PROFILE_ID.hex, "Histórico", 12345),
        )
    assert validate(path) == "desktop_001"
    restore(str(path))
    with sqlite3.connect(DB_PATH) as db:
        assert db.execute("SELECT amount FROM transactions").fetchone() == (12345,)
        assert db.execute("SELECT version_num FROM alembic_version").fetchone() == ("desktop_002",)
    assert validate(path) == "desktop_001"  # selected file was not migrated
    migrate(path)
    migrate(path)
    assert validate(path) == "desktop_002"
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID


def test_auth_origin_and_internal_path_protection(client, auth_headers):
    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert (
        client.get("/health", headers={**auth_headers, "Origin": "http://malicious.example"}).status_code
        == 403
    )
    assert client.get("/health", headers=auth_headers).status_code == 200
    with pytest.raises(ValueError):
        backup(str(DB_PATH))
    with pytest.raises(ValueError):
        restore(str(DB_PATH))


def test_startup_upgrades_existing_desktop_and_preserves_history(client, auth_headers):
    transaction(client, auth_headers, amount="7.77")
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DROP INDEX ix_transactions_profile_date")
        db.execute("UPDATE alembic_version SET version_num='desktop_001'")
    initialize()
    assert validate(DB_PATH) == "desktop_002"
    before = DB_PATH.parent / "pre-upgrade-desktop_001.sqlite3"
    assert validate(before) == "desktop_001"
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["items"][0]["amount"] == "7.77"


def test_sqlite_constraints_and_unicode_search(client, auth_headers):
    item = transaction(client, auth_headers, description="CAFÉ", amount="1.01")
    assert client.get("/api/v1/transactions?search=café", headers=auth_headers).json()["total"] == 1
    with sqlite3.connect(DB_PATH) as db:
        for statement in [
            "UPDATE transactions SET amount=-1",
            "UPDATE transactions SET amount=1.5",
            "UPDATE transactions SET type='OTHER'",
            "UPDATE transactions SET status='OTHER'",
        ]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(statement)
    assert client.get(f"/api/v1/transactions/{item['id']}", headers=auth_headers).json()["amount"] == "1.01"


def test_restore_internal_recovery_copy(client, auth_headers, tmp_path):
    transaction(client, auth_headers, description="Antes")
    file = tmp_path / "external.sqlite3"
    backup(str(file))
    transaction(client, auth_headers, description="Depois")
    recovery = restore(str(file))
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["total"] == 1
    restore(str(recovery))
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["total"] == 2


def test_unknown_startup_revision_is_not_modified():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("UPDATE alembic_version SET version_num='desktop_999'")
    with pytest.raises(RuntimeError, match="incompatível"):
        initialize()
    with sqlite3.connect(DB_PATH) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone() == ("desktop_999",)
