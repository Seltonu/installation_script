#!/usr/bin/env python3
"""Pre-seed the Minimon COSMIC applet's settings from ./configs/minimon/.

cosmic-config stores one file per setting (filename = key, contents = a RON
value), under ~/.config/cosmic/<applet-id>/v<N>/. Writing those files ahead of
time means Minimon picks up the saved layout the first time it runs, so this
is safe to run before the applet is installed.

Note the config id carries a "-panel" suffix -- it's the applet's panel
instance, not the bare flatpak/package id.
"""
from utils import *
import shutil
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent / "configs" / "minimon"
TARGET_DIR = (Path.home() / ".config" / "cosmic"
              / "io.github.cosmic_utils.minimon-applet-panel" / "v1")


def configure_minimon() -> int:
    print("-------------------------- Configuring Minimon")

    if not SOURCE_DIR.is_dir():
        msg = f"ERROR: Minimon config source not found: {SOURCE_DIR}"
        error_messages.append(msg)
        print(msg)
        return 1

    settings = sorted(p for p in SOURCE_DIR.iterdir() if p.is_file())
    if not settings:
        msg = "-No Minimon settings found to apply"
        print(msg)
        warning_messages.append(msg)
        return 0

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for src in settings:
        shutil.copy(src, TARGET_DIR / src.name)
    print(f"-Applied {len(settings)} Minimon settings to {TARGET_DIR}")

    # Minimon caches its config in memory, so a running applet would overwrite
    # these on its next save.
    print("-Restart cosmic-panel (or log out) for the settings to take effect")
    return 0


if __name__ == "__main__":
    sys.exit(configure_minimon())
