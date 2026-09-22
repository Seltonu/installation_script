# Label Printer CLI

A simple CLI for printing thermal labels on a Brother QL-1110NWBc from Linux. Designed for ergonomic everyday use — type `label Flour` and walk to the printer.

## What this is

A single Python script (`label`) that takes text on the command line, auto-fits it onto a label, and sends raster data directly to a Brother QL-series label printer over the network. Bypasses CUPS entirely.

## Hardware

- **Printer**: Brother QL-1110NWBc (treated as QL-1110NWB by software — the `c` is a SKU revision, not a different protocol)
- **Connection**: WiFi infrastructure mode, joined to home WiFi via the printer's web admin (`http://<printer-ip>`, login `admin` / `initpass`)
- **Default labels**: DK-1204 (0.66" × 2.1", 17×54mm die-cut)

### Setting the printer's mode (one-time)

The printer was reconfigured via its built-in web UI:
1. Browse to printer IP → Network → Wireless LAN
2. Set Selected Interface to **Infrastructure and Wireless Direct**
3. Configure home WiFi credentials in the Wireless tab

### iOS quirk worth knowing

The QL-1110NWBc's Bluetooth is **not MFi-certified**. iOS will let you "pair" it but no iOS app can actually communicate with it over Bluetooth. From iPhone/iPad you must use WiFi via the Brother iPrint&Label app. (Not relevant to this CLI tool, but explains why Bluetooth setup felt broken.)

## System environment

- Linux (Pop!_OS 24.04, Debian-based, Python 3.12, COSMIC desktop)
- Python venv at `~/.venvs/label/`
- Script at `~/.local/bin/label` (copied there by `configure_scripts.py` from this repo). Available on PATH after the next login (Pop!_OS `~/.profile` adds `~/.local/bin` automatically when it exists).
- Script invoked from launcher with `:label <text>` prefix

## Dependencies

The script is self-bootstrapping: on first run it creates `~/.venvs/label/`
and installs `brother_ql_inventree`, `Pillow`, and `zeroconf` into it, then
re-execs itself with the venv's Python. Subsequent runs just re-exec — no
setup cost. To rebuild from scratch, `rm -rf ~/.venvs/label` and run
`label` again.

The only system requirement is the `python3-venv` apt package (so
`python3 -m venv` works on Debian-based distros). It ships by default on
Pop!_OS. If first-run bootstrap ever fails because it's missing, the
script prints a message telling you to run `sudo apt install python3-venv`.

### Why `brother_ql_inventree` and not `brother_ql`

The original `brother_ql` (pklaus) on PyPI is effectively abandoned. Despite its README claiming QL-1110NWB support, the model isn't actually in its registry — calling `BrotherQLRaster("QL-1110NWB")` throws `BrotherQLUnknownModel`. The `brother_ql_inventree` fork (matmair) does include the model and works.

That fork was **archived in March 2026** but remains feature-complete for our use. The InvenTree project still ships it as a dependency. Archived ≠ broken; if it ever truly breaks on a future Pillow/Python release, it'll need a community pickup or a small in-house fork.

## Configuration & state

| Path | Purpose |
|------|---------|
| `~/.config/label/config.json` | Persistent defaults: `default_font`, `label_size` |
| `~/.cache/label/printer_ip` | Cached printer IP — auto-purged & rediscovered on connection failure |

The script also has hardcoded constants near the top (model, port, paths to fonts, layout ratios). Edit those directly when needed.

## Usage

```bash
# Print
label Flour
label Brown Rice Flour
label "Aged Cheddar\nJan 2026"        # \n forces a line break

# Save defaults (no print, just persists to config.json)
label -f gothic                        # save default font
label -size 17x54                      # save default size
label -f gothic -size 23x23            # save both

# One-off override (defaults unchanged)
label -f italic Flour
label -size 62x100 "Big shipping label"

# List options (current default marked)
label -f
label -size

# Numeric indices also work after listing
label -f 7 Flour
```

### Cosmic Launcher integration

Open Launcher (Super), prefix command with `:`. So: `:label Flour` → enter. `:` runs silently, `t:` opens a terminal first.

## Architecture

Single-file script. Top-level concerns:

1. **Persistence** — `load_config()` / `save_config()` read/write JSON in `~/.config/label/`. Empty/missing file → falls back to script defaults.

2. **Printer discovery** — `resolve_printer()` flow:
   - Hardcoded `PRINTER_IP` (if set) wins.
   - Otherwise check `~/.cache/label/printer_ip` and verify port 9100 is open.
   - Otherwise mDNS browse `_pdl-datastream._tcp.local.` and `_printer._tcp.local.` for "brother"/"ql-"/"brn" hostnames, cache the result.
   - On `ConnectionRefusedError` during send: purge cache, re-resolve once, retry.

3. **Layout** — `best_layout()` is a 3-stage greedy fit:
   - Try 1 line, shrinking from `font_max` (85% of label height) down to `font_wrap` (42%).
   - If still too big, wrap to 2 then 3 lines, retrying from `font_max`.
   - Last resort: shrink 1 line down to `MIN_FONT_SIZE` (16px).
   - **Explicit `\n` overrides everything** — those become the lines verbatim, just sized to fit.

4. **Render → rotate → send** — PIL builds a landscape-oriented image at the label's printable dimensions, rotates `-90°` for the printer's expected orientation, then `brother_ql.conversion.convert` produces raster instructions sent over TCP port 9100.

## Known constraints / quirks

- `brother_ql discover` raises `NotImplementedError` (broken in both pklaus and inventree forks). We use mDNS via `zeroconf` instead.
- mDNS discovery can fail on networks that block multicast — the script falls back to whatever is in the IP cache, then errors out. If discovery never works on a given network, hardcode `PRINTER_IP` at the top of the script.
- Continuous tape sizes (`12`, `29`, `62`, etc.) have an arbitrary fixed length per entry in `LABEL_SIZES`. Change the tuples to make tapes longer/shorter.
- Brother label dimensions in `LABEL_SIZES` are best-guess from Brother specs. To verify exact `dots_printable` values for a given label, run `~/.venvs/label/bin/brother_ql info labels`.
- `Editor Lite` must be off if printing via USB (not relevant for the network path we use).
- iOS Bluetooth doesn't work (see hardware section) — irrelevant to this script, but useful context if the user ever tries to debug the iPrint&Label app.

## Possible next steps

Just ideas — none implemented:

- `-n N` flag to print N copies of the same label.
- `--preset <name>` to save and recall full label templates (font + size + body, e.g. spice jar template).
- QR/barcode embedding (PIL + `qrcode` or `python-barcode`).
- Left/center/right alignment flag (currently always centered).
- Image embedding from a path (`label --img logo.png "Acme Corp"`).
- Auto-detect available fonts from `fc-list` instead of hardcoding paths.
- A small daemon that holds the printer connection open for batch printing.
- Web Based Management of the printer (config sheet, IP, password reset) is at `http://<ip>` if needed.

## Reference

- Active library: <https://github.com/matmair/brother_ql-inventree> (archived but functional; PyPI: `brother_ql_inventree`)
- Original (avoid): <https://github.com/pklaus/brother_ql>
- Brother QL raster protocol: documented in the `brother_ql` README
- Printer's web UI: `http://<printer-ip>` (admin / initpass)
- Hold the printer's **Cutter button** for ~2 seconds while powered on to print a config sheet with the live IP, MAC, SSID, etc.

## The script

Source lives in this repo at `scripts/label.py`. `configure_scripts.py` (in
the repo root) copies it to `~/.local/bin/label` on a fresh install. The
shebang is `#!/usr/bin/env python3` and the script self-bootstraps its
own `~/.venvs/label/` on first run (see Dependencies above).
