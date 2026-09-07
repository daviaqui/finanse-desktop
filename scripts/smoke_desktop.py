"""Linux WebDriver smoke test against the actual packaged Tauri window.

Requires tauri-driver and WebKitWebDriver on PATH and a graphical desktop.
All application data goes into a temporary profile. No source-project access.
"""

import base64
import json
from http.client import HTTPException
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

root = Path(__file__).resolve().parents[1]
application = root / "src-tauri/target/release/finanse-desktop"
http = build_opener(ProxyHandler({}))
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]


def request(method, path, data=None):
    req = Request(
        f"http://127.0.0.1:{port}{path}",
        method=method,
        data=None if data is None else json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with http.open(req, timeout=60) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(error.read().decode()) from error
    value = payload.get("value", payload)
    if isinstance(value, dict) and value.get("error"):
        raise RuntimeError(value)
    return value


def wait(check, timeout=60):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except (RuntimeError, URLError, HTTPException, OSError) as error:
            last = error
        time.sleep(0.25)
    raise RuntimeError(f"Timeout: {last}")


artifacts = root / "build" / "validation"
artifacts.mkdir(parents=True, exist_ok=True)
with (
    tempfile.TemporaryDirectory(prefix="finanse-window-") as temp,
    (artifacts / "desktop.log").open("w") as log,
):
    env = {
        **os.environ,
        "XDG_DATA_HOME": temp + "/data",
        "XDG_CONFIG_HOME": temp + "/config",
        "XDG_CACHE_HOME": temp + "/cache",
    }
    driver = subprocess.Popen(
        ["tauri-driver", "--port", str(port)], env=env, stdout=log, stderr=log
    )
    session = None
    try:
        wait(lambda: request("GET", "/status"))
        session = request(
            "POST",
            "/session",
            {
                "capabilities": {
                    "alwaysMatch": {
                        "browserName": "wry",
                        "tauri:options": {"application": str(application)},
                    }
                }
            },
        )["sessionId"]
        prefix = f"/session/{session}"

        def js(script, *args):
            return request(
                "POST", prefix + "/execute/sync", {"script": script, "args": list(args)}
            )

        def element(css):
            return request(
                "POST", prefix + "/element", {"using": "css selector", "value": css}
            )["element-6066-11e4-a52e-4f735466cecf"]

        def click(css):
            wait(lambda: element(css))
            # This host's WebKit driver lacks pointer injection. Dispatch a DOM
            # click in the actual WebView, preserving the real React/IPC/backend.
            js("document.querySelector(arguments[0]).click()", css)

        def navigate(route):
            if js(
                "return getComputedStyle(document.querySelector('.mobile-header')).display !== 'none'"
            ):
                click(".mobile-header button:first-child")
            click(f'a[href="#/{route}"]')
            title = {
                "categorias": "Categorias",
                "lancamentos": "Lançamentos",
                "dados": "Backup e dados",
            }[route]
            wait(
                lambda: js(
                    "return document.querySelector('h1')?.innerText === arguments[0]",
                    title,
                )
            )

        def fill(css, text):
            wait(lambda: element(css))
            js(
                "const el=document.querySelector(arguments[0]); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, arguments[1]); el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true}));",
                css,
                text,
            )

        wait(lambda: js("return document.body.innerText.includes('Saldo do mês')"))
        assert js("return document.querySelectorAll('.summary-card').length") == 4
        assert (
            js("return document.querySelectorAll('input[type=password]').length") == 0
        )
        screenshot = request("GET", prefix + "/screenshot")
        (artifacts / "dashboard.png").write_bytes(base64.b64decode(screenshot))
        print(
            "PASS: actual Tauri startup, dashboard, Portuguese UI and offline fonts",
            flush=True,
        )

        navigate("categorias")
        wait(
            lambda: js(
                "return document.querySelectorAll('.category-card').length === 8"
            )
        )
        click(".page-heading .button.primary")
        fill("#category-name", "Categoria desktop teste")
        click(".form-actions .primary")
        wait(
            lambda: js(
                "return document.querySelectorAll('.category-card').length === 9"
            )
        )

        navigate("lancamentos")
        click(".page-heading .button.primary")
        fill("#description", "Lançamento desktop teste")
        fill("#amount", "12345")
        click(".form-actions .primary")
        wait(
            lambda: js(
                "return document.querySelectorAll('.data-table tbody tr').length === 1"
            )
        )
        assert js(
            "return document.querySelector('.data-table').innerText.includes('123,45')"
        )
        click('button[title="Editar"]')
        fill("#description", "Lançamento alterado")
        click(".form-actions .primary")
        wait(
            lambda: js(
                "return document.querySelector('.data-table')?.innerText.includes('Lançamento alterado')"
            )
        )
        fill(".search-input input", "inexistente")
        wait(
            lambda: js(
                "return document.body.innerText.includes('Nenhum lançamento encontrado')"
            )
        )
        # WebKit clear must emit input for React's controlled field.
        fill(".search-input input", "Lançamento")
        wait(
            lambda: js(
                "return document.querySelectorAll('.data-table tbody tr').length === 1"
            )
        )
        screenshot = request("GET", prefix + "/screenshot")
        (artifacts / "transactions.png").write_bytes(base64.b64decode(screenshot))
        click('button[title="Excluir"]')
        click(".form-actions .primary")
        wait(
            lambda: js(
                "return document.body.innerText.includes('Nenhum lançamento encontrado')"
            )
        )
        print(
            "PASS: category creation and transaction create/edit/search/delete through real UI",
            flush=True,
        )

        navigate("dados")
        wait(
            lambda: js(
                "return document.querySelector('.data-path')?.innerText.includes('com.finanse.desktop')"
            )
        )
        assert temp in js("return document.querySelector('.data-path').innerText")
        if os.environ.get("FINANSE_NATIVE_PROBE"):
            native = ["python3", str(root / "scripts/native_dialog_probe.py")]
            backup_file = str(Path(temp) / "native-backup.sqlite3")
            click(".data-panel button")
            subprocess.run([*native, "save", backup_file], check=True)
            wait(
                lambda: js(
                    "return document.body.innerText.includes('Backup salvo com sucesso')"
                )
            )
            assert Path(backup_file).is_file()
            navigate("categorias")
            click(".page-heading .button.primary")
            fill("#category-name", "Criada depois do backup")
            click(".form-actions .primary")
            wait(
                lambda: js(
                    "return document.querySelectorAll('.category-card').length === 10"
                )
            )
            navigate("dados")
            click(".data-panel button.secondary")
            subprocess.run([*native, "open"], check=True)
            subprocess.run([*native, "confirm"], check=True)
            wait(
                lambda: js(
                    "return document.body.innerText.includes('Dados restaurados com sucesso')"
                )
            )
            wait(
                lambda: js(
                    "return !document.querySelector('.data-panel button').disabled"
                )
            )
            navigate("categorias")
            wait(
                lambda: js(
                    "return document.querySelectorAll('.category-card').length === 9"
                )
            )
            assert not js(
                "return document.body.innerText.includes('Criada depois do backup')"
            )
            navigate("dados")
            print("PASS: native restore replaced data and refreshed the UI", flush=True)
        resources = js("return performance.getEntriesByType('resource').map(r=>r.name)")
        assert all(not name.startswith("https://") for name in resources), resources
        assert js("return localStorage.getItem('finansee_token')") is None
        duplicate = subprocess.run(
            [str(application)], env=env, timeout=15, capture_output=True
        )
        assert duplicate.returncode == 0
        print(
            "PASS: data location, no remote assets, no stored credential, duplicate launch exits",
            flush=True,
        )
    finally:
        if session:
            try:
                request("DELETE", f"/session/{session}")
            except Exception:
                pass
        driver.terminate()
        driver.wait(timeout=15)
        lock_path = Path(temp) / "data/com.finanse.desktop/desktop.lock"
        if lock_path.exists():
            import fcntl

            def released():
                with lock_path.open("rb") as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(lock, fcntl.LOCK_UN)
                return True

            wait(released, timeout=15)
            print(
                "PASS: closing the desktop releases the backend profile lock",
                flush=True,
            )
print("Desktop smoke complete. Screenshots and log: build/validation/")
