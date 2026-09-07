"""Register this local Linux build in the current user's application menu."""

import os
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
binary = root / "src-tauri/target/release/finanse-desktop"
backend = binary.with_name("finanse-backend")
if not all(path.is_file() and os.access(path, os.X_OK) for path in (binary, backend)):
    raise SystemExit(
        "Compile o aplicativo antes de criar o atalho: npm run build:linux"
    )


def exec_quote(value):
    # Freedesktop Exec quoting: escape reserved characters, then desktop-entry escapes.
    value = value.replace("%", "%%")
    for char in ("\\", '"', "`", "$"):
        value = value.replace(char, "\\" + char)
    return '"' + value.replace("\\", "\\\\") + '"'


entry = "\n".join(
    [
        "[Desktop Entry]",
        "Type=Application",
        "Name=Finanse Desktop",
        "Comment=Finanças pessoais offline",
        f"Exec={exec_quote(str(binary))}",
        f"Icon={root / 'src-tauri/icons/128x128.png'}",
        "Terminal=false",
        "Categories=Office;Finance;",
        "StartupWMClass=finanse-desktop",
        "StartupNotify=true",
        "",
    ]
)
local_entry = root / "Finanse Desktop.desktop"
local_entry.write_text(entry)
local_entry.chmod(0o755)
validator = shutil.which("desktop-file-validate")
if validator:
    subprocess.run([validator, str(local_entry)], check=True)

data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
applications = data_home / "applications"
applications.mkdir(parents=True, exist_ok=True)
installed = applications / "com.finanse.desktop.desktop"
if installed.exists() and installed.read_text() != entry:
    raise SystemExit(
        f"Já existe outro atalho neste local; ele foi preservado: {installed}"
    )
installed.write_text(entry)
installed.chmod(0o644)
updater = shutil.which("update-desktop-database")
if updater:
    subprocess.run([updater, str(applications)], check=True)
print(f"Atalho criado: {installed}")
