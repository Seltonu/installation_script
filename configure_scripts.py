#!/usr/bin/env python3
"""Install custom user CLIs from ./scripts/ into ~/.local/bin/.

Each scripts/<name>.py becomes the command `<name>`. Files starting with
`_` are skipped. Re-running overwrites — safe and idempotent.
"""
from utils import *
import shutil
import stat
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
TARGET_DIR  = Path.home() / ".local" / "bin"


def install_scripts() -> int:
    if not SCRIPTS_DIR.is_dir():
        msg = f"ERROR: scripts directory not found: {SCRIPTS_DIR}"
        error_messages.append(msg)
        print(msg)
        return 1

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    installed = []
    for src in sorted(SCRIPTS_DIR.glob("*.py")):
        if src.name.startswith("_"):
            continue
        dest = TARGET_DIR / src.stem
        shutil.copy(src, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        installed.append(dest.name)
        print(f"-Installed: {dest}")

    if not installed:
        print("-No scripts found to install")
        return 0

    if str(TARGET_DIR) not in os.environ.get("PATH", "").split(":"):
        msg = (f"-{TARGET_DIR} is not in current PATH; "
               "log out and back in to pick it up automatically")
        print(msg)
        warning_messages.append(msg)

    return 0


if __name__ == "__main__":
    sys.exit(install_scripts())
