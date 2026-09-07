"""Frozen entry point. Private stdin boot configuration, OS-assigned loopback port."""

import json
import os
import socket
import sys
import threading
from pathlib import Path


def main():
    # Credential never appears in process arguments, logs or a disk file.
    config = json.loads(sys.stdin.readline())
    os.environ["FINANSE_TOKEN"] = config["token"]
    os.environ["FINANSE_DATA_DIR"] = config["data_dir"]
    directory = Path(config["data_dir"])
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        os.umask(0o077)
    from filelock import FileLock, Timeout

    lock = FileLock(directory / "desktop.lock")
    try:
        lock.acquire(timeout=0)
    except Timeout:
        raise RuntimeError("O Finanse Desktop já está aberto para este perfil") from None
    try:
        from app.db.migrations import initialize

        initialize()
        import uvicorn

        from app.main import app

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(
                app, log_level="warning", access_log=False, lifespan="off", timeout_graceful_shutdown=5
            )
        )

        def parent_watch():
            # EOF also covers parent crashes; explicit shutdown covers normal exits.
            sys.stdin.readline()
            server.should_exit = True

        def ready_watch():
            import time

            while not server.started and not server.should_exit:
                time.sleep(0.025)
            if server.started:
                print(json.dumps({"event": "ready", "port": port}), flush=True)

        threading.Thread(target=parent_watch, daemon=True).start()
        threading.Thread(target=ready_watch, daemon=True).start()
        server.run(sockets=[sock])
        sock.close()
    finally:
        lock.release()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"event": "error", "message": str(exc)}), flush=True)
        sys.exit(1)
