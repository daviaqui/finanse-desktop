"""Exercise the packaged executable with disposable synthetic data and no Python PATH."""

import json
import os
import secrets
import socket
import subprocess
import tempfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

root = Path(__file__).resolve().parents[1]
executable = (
    root / "dist" / ("finanse-backend.exe" if os.name == "nt" else "finanse-backend")
)
http = build_opener(ProxyHandler({}))


def launch(directory):
    token = secrets.token_hex(32)
    process = subprocess.Popen(
        [str(executable)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PATH": ""},
    )
    process.stdin.write(json.dumps({"token": token, "data_dir": str(directory)}) + "\n")
    process.stdin.flush()
    import queue
    import threading

    output = queue.Queue()
    threading.Thread(
        target=lambda: output.put(process.stdout.readline()), daemon=True
    ).start()
    try:
        line = output.get(timeout=30)
    except queue.Empty:
        process.kill()
        raise RuntimeError(
            "Sidecar startup timeout: " + process.communicate()[1]
        ) from None
    if not line:
        raise RuntimeError(process.communicate()[1])
    message = json.loads(line)
    print("Sidecar:", message, flush=True)
    return process, token, message


def call(port, token, path, method="GET", data=None):
    body = None if data is None else json.dumps(data).encode()
    request = Request(
        f"http://127.0.0.1:{port}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with http.open(request, timeout=10) as response:
            return response.status, json.loads(response.read() or b"null")
    except HTTPError as error:
        return error.code, json.loads(error.read())


with tempfile.TemporaryDirectory(prefix="finanse-smoke-") as temp:
    directory = Path(temp) / "profile"
    process, token, ready = launch(directory)
    try:
        assert ready["event"] == "ready", ready
        port = ready["port"]
        assert call(port, "", "/health")[0] == 401
        assert call(port, token, "/health")[0] == 200
        assert len(call(port, token, "/api/v1/categories")[1]) == 8
        status, item = call(
            port,
            token,
            "/api/v1/transactions",
            "POST",
            {
                "description": "Smoke sintético",
                "amount": "123.45",
                "type": "income",
                "transaction_date": "2026-09-06",
            },
        )
        assert status == 201, item
        duplicate, _, error = launch(directory)
        assert error["event"] == "error" and "já está aberto" in error["message"], error
        assert duplicate.wait(timeout=10) != 0
        other, other_token, other_ready = launch(Path(temp) / "other")
        assert other_ready["event"] == "ready" and other_ready["port"] != port
        assert call(port, other_token, "/health")[0] == 401
        other.stdin.close()
        assert other.wait(timeout=10) == 0
        backup_path = str(Path(temp) / "backup.sqlite3")
        assert (
            call(
                port, token, "/api/v1/maintenance/backup", "POST", {"path": backup_path}
            )[0]
            == 200
        )
        assert (
            call(port, token, f"/api/v1/transactions/{item['id']}", "DELETE")[0] == 204
        )
        assert (
            call(
                port,
                token,
                "/api/v1/maintenance/restore",
                "POST",
                {"path": backup_path, "confirmed": True},
            )[0]
            == 200
        )
        process.stdin.write("shutdown\n")
        process.stdin.flush()
        assert process.wait(timeout=10) == 0
        process, new_token, ready = launch(directory)
        assert ready["event"] == "ready", ready
        assert call(ready["port"], token, "/health")[0] == 401
        assert (
            call(ready["port"], new_token, "/api/v1/transactions")[1]["items"][0][
                "amount"
            ]
            == "123.45"
        )
        # Closing parent pipe simulates parent disappearance.
        process.stdin.close()
        assert process.wait(timeout=10) == 0
        with socket.socket() as probe:
            assert probe.connect_ex(("127.0.0.1", ready["port"])) != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
print(
    "PASS: frozen backend, authentication, dynamic ports, duplicate lock, CRUD, backup/restore, persistence, credential rotation and shutdown/parent EOF."
)
