"""Portable checks; run with the project virtualenv Python."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
commands = [
    [sys.executable, "-m", "pytest", "-q", "backend/tests"],
    [sys.executable, "-m", "ruff", "check", "backend", "scripts"],
    [npm, "--prefix", "frontend", "run", "lint"],
    [npm, "--prefix", "frontend", "test"],
    [npm, "--prefix", "frontend", "run", "build"],
    ["cargo", "fmt", "--manifest-path", "src-tauri/Cargo.toml", "--", "--check"],
    [
        "cargo",
        "clippy",
        "--manifest-path",
        "src-tauri/Cargo.toml",
        "--",
        "-D",
        "warnings",
    ],
    ["cargo", "test", "--manifest-path", "src-tauri/Cargo.toml"],
]
for command in commands:
    subprocess.run(command, cwd=root, check=True)
