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
| `configure_directories.py` | Mounts SMB shares from the home NAS and repoints the XDG user dirs at them. Credentials live in a root-only file, never in `/etc/fstab`. |
| `configure_firefox.py` | Drops a `user.js`, sets DuckDuckGo as default, sets default zoom. |
| `configure_flameshot.py` | Installs the flatpak, copies its config, binds it to PrintScreen. |
| `configure_gnome.py` | GNOME / Nautilus dconf tweaks, dock favorites, idle settings. Only runs on a GNOME session; silently skipped on COSMIC. |
| `configure_minimon.py` | Pre-seeds the Minimon COSMIC applet's settings. Safe to run before Minimon is installed. |
| `configure_scripts.py` | Deploys each CLI in `scripts/` to `~/.local/bin/<name>` (no `.py`) so they're on PATH. |
| `configs/` | Static config files referenced by the configure scripts (Firefox `user.js`, Flameshot ini, Minimon settings, …). |
| `services/*.sh` | Hardware-specific systemd user services (Wave:3 mic fix, Kanto ORA audio fix). Each detects its USB device and self-skips if absent. |
| `scripts/` | Custom personal CLIs. Source-of-truth for anything that ends up in `~/.local/bin`. |
| `deprecated/` | Superseded shell versions of the configure scripts, kept for reference. Nothing here is called by the installer. |

## Custom CLIs (`scripts/`)

Two layouts work, both deploying as the command `<name>`:

```
scripts/<name>.py           loose single-file script
scripts/<name>/<name>.py    script with its own README/assets alongside it
```

Give it a `#!/usr/bin/env python3` shebang, then run `python3
configure_scripts.py` to (re-)deploy. Names starting with `_` are skipped.
Start loose, promote to a folder once it grows docs — `label` is the
worked example.

If a script needs third-party packages, it should self-bootstrap its own
venv at `~/.venvs/<name>/` on first run rather than relying on a
system-wide install (see `scripts/label/label.py` for the pattern). This keeps
each CLI isolated, leaves the system Python untouched, and means
re-deploying the script is just a file copy — no setup cost.

The only system requirement is the `python3-venv` apt package, which
ships by default on Pop!_OS. If a script ever fails to bootstrap because
it's missing, install it with `sudo apt install python3-venv`.

## NAS shares

`configure_directories.py` makes Documents/Music/Pictures/Videos the same
folders on every machine. Displaced local folders are renamed to
`Local <name>` rather than deleted.

- The SMB password is typed interactively and stored in
  `/etc/samba/credentials/<server>` (0600, root-only). `/etc/fstab` only
  references that path, so no secret is ever written to a world-readable
  file or passed on a command line.
- Entries are `noauto,x-systemd.automount`, so shares mount on **first
  access**, not at boot. An unreachable NAS can't hang startup, and the
  fstab entries can be written before the credentials exist.
- Re-running is safe: the managed fstab block is replaced, not appended to.
- Every `configure_*.py` must stay executable with a `#!/usr/bin/env python3`
  shebang — the installer invokes them as `./script.py`, so a missing exec
  bit fails the step with a bare "Permission denied".

## Notes

- `~/.local/bin` is added to PATH by Pop!_OS's stock `~/.profile` only if
  the directory exists at login time. On a fresh install, log out and
  back in (or reboot) after the installer finishes so new commands are
  picked up.
- `.bash_aliases` is overwritten wholesale by the installer — anything
  custom in there will be lost on re-run.
- Flatpak remotes on Pop!_OS are **user-scoped**, so flatpak installs must
  not run under `sudo`. Minimon and YapCap live on the `cosmic` remote, not
  Flathub — they're installed from a separate list for that reason. Both
  remotes are assumed to exist already; if a fresh install errors with
  "Remote not found", add it with `flatpak remote-add --user`.
- If the system clock is wrong (e.g. a VM snapshot restored with a date in
  the past), SSL certificate verification fails *silently* and parts of the
  script break in confusing ways — adding PPAs especially. Check `date`
  first if something inexplicable is failing.
