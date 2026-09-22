#!/usr/bin/env python3
"""Mount the NAS SMB shares and repoint the XDG user dirs at them.

The goal is that Documents/Music/Pictures/Videos are the same folders on
every machine, transparently. Local copies get renamed to "Local <name>"
rather than deleted, so nothing is lost.

Three things this deliberately does NOT do:

  * No password in /etc/fstab. Credentials go in a root-only file (0600)
    under /etc/samba/credentials/ that fstab merely references.
  * No secrets on argv. Command lines are world-readable via /proc, so
    credentials come from SMB_USERNAME / SMB_PASSWORD in the environment
    (how installation_script.py passes them) or an interactive prompt.
  * No boot-time mounting. Entries are noauto + x-systemd.automount, so the
    share mounts on first access instead of at boot. An unreachable NAS
    (laptop away from home, WiFi not up yet) can't hang startup.

That last point also means fstab can be written before credentials exist --
the mount just fails until they do. Re-running is safe: the fstab block is
replaced wholesale, not appended to.

Usage:
    python3 configure_directories.py            # prompts for credentials
    SMB_USERNAME=me SMB_PASSWORD=pw python3 configure_directories.py
"""
from utils import *
import getpass
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# -------------------------- Configuration --------------------------

SMB_SHARES = [
    # The first entry is the one the XDG user dirs are pointed at.
    {"server": "vault.local", "share": "home",        "mount_point": "/mnt/vault/home"},
    {"server": "vault.local", "share": "photography", "mount_point": "/mnt/vault/photography"},
]

# XDG key -> folder name. Mostly the capitalised key, but not always
# (DOWNLOAD/Downloads, PUBLICSHARE/Public), so spell them all out.
XDG_REMOTE_DIRS = {"DOCUMENTS": "Documents", "MUSIC": "Music",
                   "PICTURES": "Pictures", "VIDEOS": "Videos"}
XDG_LOCAL_DIRS  = {"DESKTOP": "Desktop", "DOWNLOAD": "Downloads",
                   "TEMPLATES": "Templates", "PUBLICSHARE": "Public"}

CREDENTIALS_DIR = Path("/etc/samba/credentials")
FSTAB           = Path("/etc/fstab")
USER_DIRS_FILE  = Path.home() / ".config" / "user-dirs.dirs"

BLOCK_START = "# --- installation_script: NAS shares (managed, edits will be overwritten) ---"
BLOCK_END   = "# --- installation_script: end NAS shares ---"

# noauto + x-systemd.automount => mount on first access, never at boot.
MOUNT_OPTIONS = (
    "_netdev,noauto,x-systemd.automount,x-systemd.idle-timeout=60,"
    "x-systemd.mount-timeout=10,nofail,file_mode=0644,dir_mode=0755"
)


# -------------------------- Helpers --------------------------

def install_as_root(content: str, dest: Path, mode: str) -> bool:
    """Write content to a root-owned file, without ever putting it on a shell
    command line. `install` sets ownership and permissions atomically."""
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            handle.write(content)
            tmp = handle.name
        result = run_command(
            f"sudo install -m {mode} -o root -g root {tmp} {dest}", print_stdout=False
        )
        return result["returncode"] == 0
    finally:
        if tmp:
            os.unlink(tmp)


def credentials_path(server: str) -> Path:
    return CREDENTIALS_DIR / server.replace("/", "_")


def write_credentials(server: str, username: str, password: str) -> bool:
    run_command(f"sudo mkdir -p {CREDENTIALS_DIR}", print_stdout=False)
    run_command(f"sudo chmod 0700 {CREDENTIALS_DIR}", print_stdout=False)
    body = f"username={username}\npassword={password}\n"
    if install_as_root(body, credentials_path(server), "0600"):
        print(f"-Credentials written to {credentials_path(server)} (root-only, 0600)")
        return True
    err = f"Failed to write credentials for {server}"
    error_messages.append(err)
    print(f"-ERROR: {err}")
    return False


def build_fstab_block() -> str:
    """One fstab line per share, with uid/gid resolved now -- fstab is not a
    shell, so $(id -u) would be written literally and fail to parse."""
    uid, gid = os.getuid(), os.getgid()
    lines = [BLOCK_START]
    for share in SMB_SHARES:
        options = f"credentials={credentials_path(share['server'])},uid={uid},gid={gid},{MOUNT_OPTIONS}"
        lines.append(
            f"//{share['server']}/{share['share']} {share['mount_point']} cifs {options} 0 0"
        )
    lines.append(BLOCK_END)
    return "\n".join(lines) + "\n"


def update_fstab() -> bool:
    """Replace our managed block in /etc/fstab, leaving everything else alone."""
    try:
        existing = FSTAB.read_text().splitlines(keepends=True)
    except OSError as exc:
        err = f"Could not read {FSTAB}: {exc}"
        error_messages.append(err)
        print(f"-ERROR: {err}")
        return False

    # Drop the previous managed block, plus any legacy hand-rolled entries for
    # the same mount points (earlier versions of this script appended them).
    mount_points = {share["mount_point"] for share in SMB_SHARES}
    kept, inside_block = [], False
    for line in existing:
        if line.startswith(BLOCK_START):
            inside_block = True
            continue
        if line.startswith(BLOCK_END):
            inside_block = False
            continue
        if inside_block:
            continue
        fields = line.split()
        if len(fields) >= 3 and fields[1] in mount_points and fields[2] == "cifs":
            print(f"-Removing stale fstab entry for {fields[1]}")
            continue
        kept.append(line)

    while kept and not kept[-1].strip():
        kept.pop()

    run_command(f"sudo cp {FSTAB} {FSTAB}.bak", print_stdout=False)
    new_fstab = "".join(kept) + "\n" + build_fstab_block()
    if not install_as_root(new_fstab, FSTAB, "0644"):
        err = f"Failed to write {FSTAB} (backup at {FSTAB}.bak)"
        error_messages.append(err)
        print(f"-ERROR: {err}")
        return False
    print(f"-Updated {FSTAB} ({len(SMB_SHARES)} shares, backup at {FSTAB}.bak)")
    return True


def activate_mounts() -> None:
    """Generate the automount units and arm them. The shares themselves are
    not mounted until something actually touches the mount point."""
    for share in SMB_SHARES:
        run_command(f"sudo mkdir -p {share['mount_point']}", print_stdout=False)

    run_command("sudo systemctl daemon-reload", print_stdout=False)

    for share in SMB_SHARES:
        unit = subprocess.run(
            ["systemd-escape", "--path", "--suffix=automount", share["mount_point"]],
            capture_output=True, text=True,
        ).stdout.strip()
        if not unit:
            continue
        result = run_command(f"sudo systemctl restart {unit}", print_stdout=False)
        if result["returncode"] == 0:
            print(f"-Automount armed for {share['mount_point']}")
        else:
            msg = f"Automount unit {unit} did not start; share will mount on next boot"
            print(f"-WARNING: {msg}")
            warning_messages.append(msg)


def update_user_dirs() -> None:
    """Point the XDG dirs at the NAS. Written with Python rather than `echo`,
    which used to break on the apostrophe in the file's own comment header."""
    remote_root = SMB_SHARES[0]["mount_point"]
    lines = [
        "# This file is written by xdg-user-dirs-update",
        "# Managed by installation_script.py -- remote dirs live on the NAS.",
        "",
    ]
    for name, folder in XDG_LOCAL_DIRS.items():
        lines.append(f'XDG_{name}_DIR="$HOME/{folder}"')
    for name, folder in XDG_REMOTE_DIRS.items():
        lines.append(f'XDG_{name}_DIR="{remote_root}/{folder}"')

    USER_DIRS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if USER_DIRS_FILE.exists():
        shutil.copy(USER_DIRS_FILE, USER_DIRS_FILE.with_suffix(".dirs.bak"))
    USER_DIRS_FILE.write_text("\n".join(lines) + "\n")
    print(f"-Repointed {len(XDG_REMOTE_DIRS)} XDG dirs at {remote_root}")


def rename_local_dirs() -> None:
    """Move the displaced local folders aside. Skipped if already renamed or
    if the destination exists -- this must never clobber real data."""
    for folder_name in XDG_REMOTE_DIRS.values():
        folder = Path.home() / folder_name
        target = Path.home() / f"Local {folder_name}"
        if not folder.is_dir() or os.path.ismount(folder):
            continue
        if target.exists():
            msg = f"{target} already exists; leaving {folder} alone"
            print(f"-WARNING: {msg}")
            warning_messages.append(msg)
            continue
        shutil.move(str(folder), str(target))
        print(f"-Renamed {folder} -> {target}")


# -------------------------- Main --------------------------

def configure_directories() -> int:
    print("-------------------------- Configuring SMB Directories")

    username = os.environ.get("SMB_USERNAME")
    password = os.environ.get("SMB_PASSWORD")
    if not username or not password:
        if not sys.stdin.isatty():
            err = "No SMB credentials in SMB_USERNAME/SMB_PASSWORD and no terminal to prompt on"
            error_messages.append(err)
            print(f"-ERROR: {err}")
            return 1
        username = input("Enter your SMB username: ")
        password = getpass.getpass("Enter your SMB password: ")

    if not is_package_installed("cifs-utils"):
        run_command("sudo apt install -y --ignore-missing cifs-utils")

    for server in sorted({share["server"] for share in SMB_SHARES}):
        if not write_credentials(server, username, password):
            return 1

    if not update_fstab():
        return 1

    activate_mounts()
    update_user_dirs()
    rename_local_dirs()

    print("-Done. Shares mount on first access; log out and back in for the "
          "new user dirs to show up in the file manager.")
    return 0


if __name__ == "__main__":
    sys.exit(configure_directories())
