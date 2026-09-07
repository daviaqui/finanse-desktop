"""Run using the development virtualenv Python, from any working directory."""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
try:
    target = subprocess.check_output(
        ["rustc", "--print", "host-tuple"], text=True
    ).strip()
except FileNotFoundError:
    # Allows independent sidecar validation before installing the Rust toolchain.
    targets = {
        ("Linux", "x86_64"): "x86_64-unknown-linux-gnu",
        ("Windows", "AMD64"): "x86_64-pc-windows-msvc",
    }
    target = targets[(platform.system(), platform.machine())]
extension = ".exe" if sys.platform == "win32" else ""
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "finanse-backend",
        "--distpath",
        str(root / "dist"),
        "--workpath",
        str(root / "build" / "pyinstaller"),
        "--specpath",
        str(root / "build"),
        "--paths",
        str(root / "backend"),
        "--collect-submodules",
        "app",
        "--collect-submodules",
        "uvicorn",
        "--hidden-import",
        "alembic.ddl.sqlite",
        "--exclude-module",
        "alembic.testing",
        "--exclude-module",
        "pytest",
        "--hidden-import",
        "sqlalchemy.dialects.sqlite",
        "--add-data",
        f"{root / 'backend' / 'migrations'}:migrations",
        str(root / "backend" / "sidecar.py"),
    ],
    check=True,
    cwd=root,
)
target_dir = root / "src-tauri" / "binaries"
target_dir.mkdir(exist_ok=True)
shutil.copy2(
    root / "dist" / f"finanse-backend{extension}",
    target_dir / f"finanse-backend-{target}{extension}",
)
print(f"Sidecar pronto: {target}")
