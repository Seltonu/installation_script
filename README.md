# installation_script

Personal setup automation for fresh Pop!_OS installs (also fine on other
Ubuntu/Debian-based distros, but only tested on Pop!_OS).

## Usage

```bash
python3 installation_script.py
```

Asks a few questions up front (hostname, SSH key, SMB credentials), then
runs unattended: package installs (apt + flatpak), GNOME tweaks, app
configuration, hardware-specific audio fixes, and bash aliases.

Every `configure_*.py` is also runnable on its own, so you can re-apply
just one piece without re-running the whole installer.

## Layout

| Path | What it does |
|---|---|
| `installation_script.py` | Top-level orchestrator. Asks questions, installs packages, calls each `configure_*.py`. |
| `utils.py` | Shared helpers: `run_command`, `run_script`, `copy_and_overwrite`, `is_gnome_session`, etc. |
| `configure_directories.py` | Mounts SMB shares from the home NAS via `/etc/fstab`. |
| `configure_firefox.py` | Drops a `user.js`, sets DuckDuckGo as default, sets default zoom. |
| `configure_flameshot.py` | Installs the flatpak, copies its config, binds it to PrintScreen. |
| `configure_gnome.py` | GNOME / Nautilus dconf tweaks, dock favorites, idle settings. |
| `configure_scripts.py` | Copies every `scripts/*.py` into `~/.local/bin/<name>` (no `.py`) so they're on PATH. |
| `configs/` | Static config files referenced by the configure scripts (Firefox `user.js`, Flameshot ini, …). |
| `services/*.sh` | Hardware-specific systemd user services (Wave:3 mic fix, Kanto ORA audio fix). Each detects its USB device and self-skips if absent. |
| `scripts/` | Custom personal CLIs. Source-of-truth for anything that ends up in `~/.local/bin`. |

## Custom CLIs (`scripts/`)

Drop a `<name>.py` in `scripts/`, give it a `#!/usr/bin/env python3`
shebang, then `python3 configure_scripts.py` to (re-)deploy it as the
command `<name>` in `~/.local/bin/`.

If a script needs third-party packages, it should self-bootstrap its own
venv at `~/.venvs/<name>/` on first run rather than relying on a
system-wide install (see `scripts/label.py` for the pattern). This keeps
each CLI isolated, leaves the system Python untouched, and means
re-deploying the script is just a file copy — no setup cost.

The only system requirement is the `python3-venv` apt package, which
ships by default on Pop!_OS. If a script ever fails to bootstrap because
it's missing, install it with `sudo apt install python3-venv`.

## Notes

- `~/.local/bin` is added to PATH by Pop!_OS's stock `~/.profile` only if
  the directory exists at login time. On a fresh install, log out and
  back in (or reboot) after the installer finishes so new commands are
  picked up.
- `.bash_aliases` is overwritten wholesale by the installer — anything
  custom in there will be lost on re-run.
