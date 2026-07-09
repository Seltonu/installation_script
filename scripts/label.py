#!/usr/bin/env python3
"""label - quick CLI label printing for Brother QL-1110NWB.

Print:
  label <text...>                       use saved defaults
  label -font <name|#> <text...>        one-off font
  label -px <pixels|auto> <text...>     one-off font size in px (14+; 56~=3mm)
  label -mm <mm|auto> <text...>         one-off font size in mm cap height
  label -orient <h|v> <text...>         one-off orientation
  label -tape <name|#|DK> <text...>     one-off tape (mm name, #, or DK-code)
  label -calibrate <px|mm> <text...>    one-off calibration shift
  label -n <count> <text...>            print N copies (cuts between each)
  label -preview <text...>              preview (image viewer) instead of printing
  label "Line one\\nLine two"            \\n forces a line break

Save defaults (no print):
  label -font <name>                    set default font
  label -px <pixels|auto>               set default font size (px)
  label -mm <mm|auto>                   set default font size (mm)
  label -orient <h|v>                   set default orientation
  label -tape <name>                    set default tape
  label -calibrate <px|mm>              set default printer calibration

List/show:
  label -font                           list fonts
  label -px                             show current font size
  label -orient                         show current orientation
  label -tape                           list tapes

Calibration:
  label -calibrate                      run the guided recalibration flow
  label -ruler                          print a ruler at the current calibration
  label -ruler -calibrate <px>          print a ruler at a given calibration

Config:
  label -config                         show effective settings + file path
  label -reset                          wipe all saved defaults

Short forms also work: -f, -o, -p, -c.
"""
import os
import subprocess
import sys
from pathlib import Path

# === Bootstrap ============================================================
# First run creates an isolated venv, then re-execs into it so the imports
# below resolve there. To rebuild from scratch: rm -rf ~/.venvs/label
_VENV         = Path.home() / ".venvs" / "label"
_VENV_PY      = _VENV / "bin" / "python3"
_REQUIREMENTS = ("brother_ql_inventree", "Pillow", "zeroconf")

if sys.executable != str(_VENV_PY):
    if not _VENV_PY.exists():
        print(f"label: first-run setup, creating venv at {_VENV}", file=sys.stderr)
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(_VENV)])
        except subprocess.CalledProcessError:
            sys.exit("label: failed to create venv. "
                     "Install the venv module: sudo apt install python3-venv")
        subprocess.check_call(
            [str(_VENV_PY), "-m", "pip", "install", "--quiet", *_REQUIREMENTS]
        )
    os.execv(str(_VENV_PY), [str(_VENV_PY), __file__, *sys.argv[1:]])

import json
import socket
import time

from PIL import Image, ImageDraw, ImageFont
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster

# === Persistence ==========================================================
PRINTER_IP_CACHE = Path.home() / ".cache" / "label" / "printer_ip"
CONFIG_FILE      = Path.home() / ".config" / "label" / "config.json"

# === Printer ==============================================================
PRINTER_IP        = None              # hardcode "X.X.X.X" or leave None to auto-discover
MODEL             = "QL-1110NWB"
PORT              = 9100
DISCOVERY_TIMEOUT = 4

# === Defaults (used when no config file exists) ==========================
DEFAULT_TAPE        = "17x54"
DEFAULT_FONT_NAME   = "sans-bold"
DEFAULT_FONT_SIZE   = "auto"          # "auto" or pixel int
DEFAULT_ORIENTATION = "horizontal"    # "horizontal" or "vertical"
DEFAULT_CALIBRATION_PX = 14           # ~1.2mm; calibrated for THIS printer's
                                      # mechanical alignment via the ruler
                                      # test (printer drifts content ~1.2mm
                                      # toward the leading edge). Survives
                                      # -reset since it's a hardware property
                                      # not a user preference. Re-measure
                                      # any time with `label -ruler` and
                                      # override via `label -calibrate <px|mm>`.

# When a continuous tape is used and no explicit/saved override exists,
# fall back to these instead of the die-cut defaults.
CONTINUOUS_DEFAULT_FONT_SIZE   = 56            # ~3.5mm cap height at 300 DPI
CONTINUOUS_DEFAULT_ORIENTATION = "vertical"

# === Tapes (300 DPI) ======================================================
# name → (long_axis_px, short_axis_px). Short axis = tape width (fixed).
# Names match brother_ql's identifiers (run `brother_ql info labels` to verify).
# For continuous tapes, the long-axis value is only a fallback — actual print
# length is computed from text content.
TAPES = {
    # Die-cut labels:
    "17x54":    (566, 165),    # DK-1204 / DK-11204
    "17x87":    (956, 165),    # DK-1203 / DK-11203
    "23x23":    (202, 202),    # DK-1221 / DK-11221 (square)
    "29x42":    (425, 306),    # (no standard DK code)
    "29x90":    (991, 306),    # DK-1201 / DK-11201 (std address)
    "39x90":    (991, 413),    # DK-1208 / DK-11208 (large address; brother_ql calls it 39x90)
    "39x48":    (495, 425),    # (no standard DK code)
    "52x29":    (578, 271),    # (no standard DK code)
    "54x29":    (598, 271),    # DK-1226 / DK-11226
    "60x86":    (954, 672),    # DK-1234 / DK-11234 (name badge)
    "62x29":    (696, 271),    # DK-1209 / DK-11209 (small address)
    "62x100":   (1109, 696),   # DK-1202 / DK-11202 (shipping)
    "102x51":   (526, 1164),   # DK-1240 / DK-11240
    "102x152":  (1660, 1164),  # DK-1241 / DK-11241 (4×6 shipping)
    "103x164":  (1822, 1200),  # DK-1247 / DK-11247 (large shipping)
    # Continuous tapes (fallback length only — auto-extended at print time):
    "12":       (400, 106),
    "29":       (600, 306),
    "38":       (700, 413),
    "50":       (700, 554),
    "54":       (700, 590),
    "62":       (700, 696),
    "102":      (1500, 1164),

    # --- Round labels (NOT YET SUPPORTED) ---------------------------------
    # The current renderer assumes a rectangular canvas; round labels would
    # clip in the corners. To enable: uncomment the entries here AND in
    # _TAPE_DK below, then teach render() to mask to a circle.
    # "d12":    (94, 94),       # DK-1219 / DK-11219 (12mm round)
    # "d24":    (236, 236),     # DK-1218 / DK-11218 (24mm round)
    # "d58":    (618, 618),     # 58mm round
}

# Brother part-number aliases (case-insensitive). Each tape has two product
# codes: DK-1xxx (standard) and DK-11xxx (durable variant for the QL-11xx
# series); both refer to the same physical label.
_TAPE_DK = {
    "1201":  "29x90",
    "1202":  "62x100",
    "1203":  "17x87",
    "1204":  "17x54",
    "1208":  "39x90",
    "1209":  "62x29",
    "1221":  "23x23",
    "1226":  "54x29",
    "1234":  "60x86",
    "1240":  "102x51",
    "1241":  "102x152",
    "1247":  "103x164",
    # Round labels (commented out until rendering supports them):
    # "1218": "d24",
    # "1219": "d12",
}
TAPE_ALIASES = {f"dk-{k}":  v for k, v in _TAPE_DK.items()}
TAPE_ALIASES.update({f"dk-1{k}": v for k, v in _TAPE_DK.items()})

# === Fonts ================================================================
FONTS = {
    "sans-bold":   "/usr/share/fonts/opentype/fira/FiraSans-Bold.otf",
    "mono-bold":   "/usr/share/fonts/opentype/fira/FiraMono-Bold.otf",
    "serif-bold":  "/usr/share/fonts/opentype/urw-base35/C059-Bold.otf",
    "bookman":     "/usr/share/fonts/opentype/urw-base35/URWBookman-Demi.otf",
    "gothic":      "/usr/share/fonts/opentype/urw-base35/URWGothic-Demi.otf",
    "slab":        "/usr/share/fonts/truetype/roboto-slab/RobotoSlab-Bold.ttf",
    "italic":      "/usr/share/fonts/opentype/urw-base35/Z003-MediumItalic.otf",
    "narrow":      "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf",
    "display":     "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf",
    "heavy":       "/usr/share/fonts/opentype/fira/FiraSansCompressed-ExtraBold.otf",
}

# === Layout knobs =========================================================
PAD                   = 10
LINE_SPACING          = 6
SIZE_STEP             = 2
MIN_FONT_SIZE         = 14     # absolute floor: validation for explicit
                               # -px/-mm input AND the last-resort auto-fit
                               # ceiling. ~1mm cap height — small but lets
                               # cramped multi-line layouts still fit.
MAX_FONT_SIZE         = 500
MAX_LINES             = 3
DOTS_PER_MM           = 300 / 25.4   # 300 DPI ≈ 11.81 dots/mm
CAP_HEIGHT_RATIO      = 0.7    # cap height ≈ 70% of em height (font-dependent)
MAX_FONT_RATIO        = 0.85   # auto-fit upper bound, as fraction of short axis
WRAP_THRESHOLD_RATIO  = 0.42   # below this, single-line auto-fit yields to wrapping
# ==========================================================================


# --- Config persistence ---------------------------------------------------
def load_config():
    try:
        cfg = json.loads(CONFIG_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    # Migrate legacy key from before the -tape rename.
    if "label_size" in cfg and "default_tape" not in cfg:
        cfg["default_tape"] = cfg.pop("label_size")
    return cfg


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# --- Tape kind ------------------------------------------------------------
def is_continuous(tape_name):
    return "x" not in tape_name


# --- Fonts ----------------------------------------------------------------
def available_fonts():
    return [(n, p) for n, p in FONTS.items() if Path(p).is_file()]


def list_fonts():
    avail = available_fonts()
    if not avail:
        print("No configured fonts found on disk. Edit FONTS in the script.")
        return
    cur = load_config().get("default_font", DEFAULT_FONT_NAME)
    print("Available fonts (use with `label -f <name|#> ...`):\n")
    width = max(len(n) for n, _ in avail)
    for i, (name, path) in enumerate(avail, start=1):
        marker = " (default)" if name == cur else ""
        print(f"  {i:>2}.  {name:<{width}}  {path}{marker}")


def resolve_font(name_or_number):
    avail = available_fonts()
    if name_or_number.isdigit():
        idx = int(name_or_number)
        if not 1 <= idx <= len(avail):
            sys.exit(f"error: font #{idx} out of range (1..{len(avail)}). "
                     f"Run `label -f` to list options.")
        return avail[idx - 1][0], avail[idx - 1][1]
    if name_or_number not in FONTS:
        sys.exit(f"error: unknown font '{name_or_number}'. "
                 f"Run `label -f` to list options.")
    path = FONTS[name_or_number]
    if not Path(path).is_file():
        sys.exit(f"error: font '{name_or_number}' configured but not found at {path}")
    return name_or_number, path


# --- Tapes ----------------------------------------------------------------
def _dk_codes_by_tape():
    """Reverse TAPE_ALIASES: canonical name → list of DK codes (uppercased)."""
    out = {}
    for code, name in TAPE_ALIASES.items():
        out.setdefault(name, []).append(code.upper())
    return out


def list_tapes():
    cfg = load_config()
    cur = cfg.get("default_tape", DEFAULT_TAPE)
    dk = _dk_codes_by_tape()
    print("Available tapes (use mm name, index, or Brother DK code):\n")
    items = list(TAPES.items())
    width = max(len(n) for n, _ in items)
    for i, (name, (la, sa)) in enumerate(items, start=1):
        marker = " (default)" if name == cur else ""
        if is_continuous(name):
            dims = f"{sa:>4}px wide   continuous"
        else:
            dims = f"{la:>4} × {sa:<4}px  die-cut"
        codes = " / ".join(dk.get(name, []))
        codes_part = f"  [{codes}]" if codes else ""
        print(f"  {i:>2}.  {name:<{width}}  {dims}{codes_part}{marker}")


def resolve_tape(name_or_number):
    items = list(TAPES.items())
    # DK code alias (case-insensitive).
    lc = name_or_number.lower()
    if lc in TAPE_ALIASES:
        canonical = TAPE_ALIASES[lc]
        return canonical, TAPES[canonical]
    # Numeric AND not a real tape name (e.g. "62" IS a real tape) → treat as index.
    if name_or_number.isdigit() and name_or_number not in TAPES:
        idx = int(name_or_number)
        if not 1 <= idx <= len(items):
            sys.exit(f"error: tape #{idx} out of range (1..{len(items)}). "
                     f"Run `label -tape` to list options.")
        return items[idx - 1][0], items[idx - 1][1]
    if name_or_number not in TAPES:
        sys.exit(f"error: unknown tape '{name_or_number}'. "
                 f"Run `label -tape` to list options.")
    return name_or_number, TAPES[name_or_number]


# --- Font size ------------------------------------------------------------
def _px_to_mm(px):
    """Approximate cap height in mm for a font size in px at 300 DPI."""
    return round(px * CAP_HEIGHT_RATIO / DOTS_PER_MM, 1)


def _mm_to_px(mm):
    """Convert desired cap height in mm to a font size in px at 300 DPI."""
    return round(mm * DOTS_PER_MM / CAP_HEIGHT_RATIO)


def resolve_font_size(arg):
    """Parse '56', '56px', '3mm', or 'auto' → int (px) or 'auto'."""
    s = str(arg).strip().lower()
    if s == "auto":
        return "auto"

    is_mm = s.endswith("mm")
    if is_mm:
        s = s[:-2].strip()
    elif s.endswith("px"):
        s = s[:-2].strip()

    try:
        raw = float(s)
    except ValueError:
        sys.exit(f"error: invalid font size '{arg}'. "
                 f"Use a number with optional 'px' or 'mm', or 'auto'.")

    v = _mm_to_px(raw) if is_mm else int(raw)
    if not MIN_FONT_SIZE <= v <= MAX_FONT_SIZE:
        sys.exit(f"error: font size must be {MIN_FONT_SIZE}-{MAX_FONT_SIZE}px "
                 f"(~{_px_to_mm(MIN_FONT_SIZE)}-{_px_to_mm(MAX_FONT_SIZE)}mm), "
                 f"got {v}px.")
    return v


def show_font_size():
    cfg = load_config()
    cur = cfg.get("default_font_size", DEFAULT_FONT_SIZE)
    if isinstance(cur, int):
        print(f"Current default font size: {cur}px (~{_px_to_mm(cur)}mm cap height)\n")
    else:
        print(f"Current default font size: {cur}\n")
    print("Set with `label -px <pixels>`, `label -mm <mm>`, or `label -px auto`.")
    print(f"Range: {MIN_FONT_SIZE}-{MAX_FONT_SIZE}px. "
          f"At 300 DPI, rough cap-height guide:")
    print( "   36px  ~= 2mm     - dense receipts, footnotes")
    print( "   56px  ~= 3-4mm   - default for continuous tapes")
    print( "   96px  ~= 6mm     - shelf labels, name badges")
    print( "  150px+ ~= 10mm+   - banners, big shipping headers")
    print(f"\nOn continuous tapes, 'auto' falls back to "
          f"{CONTINUOUS_DEFAULT_FONT_SIZE}px.")


# --- Orientation ----------------------------------------------------------
ORIENT_ALIASES = {
    "h": "horizontal", "horizontal": "horizontal", "landscape": "horizontal",
    "v": "vertical",   "vertical":   "vertical",   "portrait":  "vertical",
}


def resolve_orientation(arg):
    s = str(arg).strip().lower()
    if s not in ORIENT_ALIASES:
        sys.exit(f"error: unknown orientation '{arg}'. "
                 f"Use 'h'/'horizontal' or 'v'/'vertical'.")
    return ORIENT_ALIASES[s]


def show_orientation():
    cfg = load_config()
    cur = cfg.get("default_orientation", DEFAULT_ORIENTATION)
    print(f"Current default orientation: {cur}")
    print("Set with `label -o h` (horizontal) or `label -o v` (vertical).")
    print("Continuous tapes default to vertical when no preference is saved.")


# --- Calibration ---------------------------------------------------------
# Brother printers have small per-unit alignment differences between the
# print head and the gap sensor. brother_ql positions the printable image
# with a fixed model-specific margin (44 dots for QL-1110NWB), but if your
# printer is a few px off, the rendered content will look shifted on the
# physical label even though the preview is centered. This calibration
# shifts the rendered image horizontally (in the pre-rotation canvas) to
# compensate. Use `label -ruler` to re-measure if the printer drifts.

def resolve_calibration(arg):
    """Parse '14', '14px', or '1.2mm' → int px (signed)."""
    s = str(arg).strip().lower()
    is_mm = s.endswith("mm")
    if is_mm:
        s = s[:-2].strip()
    elif s.endswith("px"):
        s = s[:-2].strip()
    try:
        raw = float(s)
    except ValueError:
        sys.exit(f"error: invalid calibration '{arg}'. "
                 f"Use a signed number with optional 'px' or 'mm'.")
    v = round(raw * DOTS_PER_MM) if is_mm else int(raw)
    if abs(v) > 200:
        sys.exit(f"error: calibration must be within ±200px (got {v}).")
    return v


def show_calibration():
    cfg = load_config()
    cur = cfg.get("default_calibration", DEFAULT_CALIBRATION_PX)
    mm = round(cur / DOTS_PER_MM, 2)
    sign = "+" if cur >= 0 else ""
    src = "saved" if "default_calibration" in cfg else "script default"
    print(f"Current calibration: {sign}{cur}px ({sign}{mm}mm) [{src}]\n")
    print("Set with `label -calibrate <px>` (e.g. 14) or `label -calibrate <mm>mm` (e.g. 1.2mm).")
    print("Positive shifts content right in held horizontal-mode view")
    print("(= away from leading edge of tape). Negative shifts left.")
    print("Re-measure your printer's drift any time with `label -ruler`.")


# --- Whole-config view ---------------------------------------------------
def show_config():
    cfg = load_config()
    dk_map = _dk_codes_by_tape()
    rows = [
        ("font",        "default_font",        DEFAULT_FONT_NAME),
        ("font size",   "default_font_size",   DEFAULT_FONT_SIZE),
        ("orientation", "default_orientation", DEFAULT_ORIENTATION),
        ("tape",        "default_tape",        DEFAULT_TAPE),
        ("calibration", "default_calibration", DEFAULT_CALIBRATION_PX),
    ]

    formatted = []
    for label, key, default in rows:
        value  = cfg.get(key, default)
        source = "saved" if key in cfg else "script default"
        if key == "default_tape":
            display = f"{value}mm"
            codes = dk_map.get(value, [])
            if codes:
                display += f"  [{' / '.join(codes)}]"
        elif key == "default_font_size":
            if isinstance(value, int):
                display = f"{value}px (~{_px_to_mm(value)}mm)"
            else:
                display = str(value)
        elif key == "default_calibration":
            mm   = round(value / DOTS_PER_MM, 2)
            sign = "+" if value >= 0 else ""
            display = f"{sign}{value}px ({sign}{mm}mm)"
        else:
            display = str(value)
        formatted.append((label, display, source))

    w = max(len(d) for _, d, _ in formatted)
    print("Current label config:\n")
    for label, display, source in formatted:
        print(f"  {label:<13} {display:<{w}}  ({source})")
    print(f"\nConfig file:      {CONFIG_FILE}")
    if PRINTER_IP_CACHE.exists():
        ip = PRINTER_IP_CACHE.read_text().strip()
        print(f"Printer IP cache: {ip}  ({PRINTER_IP_CACHE})")
    else:
        print(f"Printer IP cache: (none — will mDNS-discover on next print)")
    print("\nNote: continuous tapes apply smart defaults (vertical, "
          f"{CONTINUOUS_DEFAULT_FONT_SIZE}px) when no value is saved.")


# --- Effective per-print settings -----------------------------------------
def effective_settings(cfg, tape_name, font_size_arg, orient_arg):
    """Resolve final font_size + orientation: explicit > saved > tape-aware fallback."""
    is_cont = is_continuous(tape_name)

    if font_size_arg is not None:
        font_size = resolve_font_size(font_size_arg)
    elif "default_font_size" in cfg:
        font_size = cfg["default_font_size"]
        if isinstance(font_size, str) and font_size != "auto":
            font_size = resolve_font_size(font_size)
    elif is_cont:
        font_size = CONTINUOUS_DEFAULT_FONT_SIZE
    else:
        font_size = "auto"

    # 'auto' has no upper bound on continuous tapes, so coerce.
    if is_cont and font_size == "auto":
        font_size = CONTINUOUS_DEFAULT_FONT_SIZE

    if orient_arg is not None:
        orientation = resolve_orientation(orient_arg)
    elif "default_orientation" in cfg:
        orientation = cfg["default_orientation"]
    elif is_cont:
        orientation = CONTINUOUS_DEFAULT_ORIENTATION
    else:
        orientation = DEFAULT_ORIENTATION

    return font_size, orientation


# --- Printer discovery ----------------------------------------------------
def _port_open(host, port=PORT, timeout=1.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def _discover_via_mdns(timeout=DISCOVERY_TIMEOUT):
    try:
        from zeroconf import Zeroconf, ServiceBrowser
    except ImportError:
        return None
    found = []
    class Listener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name, timeout=2000)
            if not info:
                return
            label_str = (name + " " + (info.server or "")).lower()
            if "brother" in label_str or "ql-" in label_str or "brn" in label_str:
                addrs = info.parsed_addresses() if hasattr(info, "parsed_addresses") else []
                if addrs:
                    found.append(addrs[0])
        def update_service(self, *_): pass
        def remove_service(self, *_): pass
    zc = Zeroconf()
    try:
        ServiceBrowser(zc, "_pdl-datastream._tcp.local.", Listener())
        ServiceBrowser(zc, "_printer._tcp.local.", Listener())
        deadline = time.time() + timeout
        while not found and time.time() < deadline:
            time.sleep(0.1)
    finally:
        zc.close()
    return found[0] if found else None


def _read_ip_cache():
    try:
        return PRINTER_IP_CACHE.read_text().strip() or None
    except FileNotFoundError:
        return None


def _write_ip_cache(ip):
    PRINTER_IP_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PRINTER_IP_CACHE.write_text(ip)


def resolve_printer():
    if PRINTER_IP:
        return f"tcp://{PRINTER_IP}"
    cached = _read_ip_cache()
    if cached and _port_open(cached):
        return f"tcp://{cached}"
    print("Discovering printer via mDNS...", file=sys.stderr)
    ip = _discover_via_mdns()
    if not ip:
        sys.exit("error: no Brother printer found on the network.")
    _write_ip_cache(ip)
    return f"tcp://{ip}"


# --- Layout & rendering ---------------------------------------------------
def best_layout(text, font_path, max_w, max_h, explicit_lines, font_max, font_wrap):
    def fits(font, lines):
        line_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
        total_h = line_h * len(lines) + LINE_SPACING * (len(lines) - 1)
        widest = max(font.getlength(l) for l in lines)
        return widest <= max_w and total_h <= max_h

    def split_words(words, n_lines):
        per = max(1, len(words) // n_lines)
        out, i = [], 0
        for k in range(n_lines):
            end = len(words) if k == n_lines - 1 else min(len(words), i + per)
            out.append(" ".join(words[i:end]))
            i = end
        return [l for l in out if l]

    if explicit_lines:
        lines = [l for l in explicit_lines if l]
        for size in range(font_max, MIN_FONT_SIZE - 1, -SIZE_STEP):
            f = ImageFont.truetype(font_path, size)
            if fits(f, lines):
                return f, lines
        return ImageFont.truetype(font_path, MIN_FONT_SIZE), lines

    for size in range(font_max, font_wrap - 1, -SIZE_STEP):
        f = ImageFont.truetype(font_path, size)
        if fits(f, [text]):
            return f, [text]

    words = text.split()
    for n in range(2, MAX_LINES + 1):
        if len(words) < n:
            continue
        lines = split_words(words, n)
        for size in range(font_max, MIN_FONT_SIZE - 1, -SIZE_STEP):
            f = ImageFont.truetype(font_path, size)
            if fits(f, lines):
                return f, lines

    for size in range(font_wrap, MIN_FONT_SIZE - 1, -SIZE_STEP):
        f = ImageFont.truetype(font_path, size)
        if fits(f, [text]):
            return f, [text]

    return ImageFont.truetype(font_path, MIN_FONT_SIZE), [text]


def wrap_text(text, font, max_width):
    """Greedy line wrap to fit within max_width pixels. Honors explicit \\n."""
    out = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            out.append("")
            continue
        line = words[0]
        for word in words[1:]:
            test = f"{line} {word}"
            if font.getlength(test) <= max_width:
                line = test
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def render(text, font_path, font_size, tape_name, tape_dims, orientation, offset=0):
    text = text.replace("\\n", "\n")
    is_cont = is_continuous(tape_name)
    long_axis, short_axis = tape_dims

    # Canvas: text reads along width. In horizontal mode the LONG axis is the
    # text-direction (becomes feed-direction after a -90 rotation for printing).
    # In vertical mode the SHORT axis is the text-direction (lines stack along
    # the LONG axis = feed direction, no rotation needed).
    if orientation == "horizontal":
        canvas_w, canvas_h = long_axis, short_axis
    else:
        canvas_w, canvas_h = short_axis, long_axis

    # Reserve room on both sides of the text region so the offset shift can be
    # applied without clipping content. Continuous tapes auto-extend in the
    # long axis, so the offset is irrelevant there — skip the reservation.
    layout_offset = 0 if is_cont else int(offset)
    text_w = canvas_w - 2 * PAD - 2 * abs(layout_offset)
    text_h = canvas_h - 2 * PAD

    if font_size == "auto":
        # Die-cut auto-fit. Use the shorter dimension for the font ceiling so
        # the same heuristic works in both orientations.
        explicit = text.split("\n") if "\n" in text else None
        flat = text.replace("\n", " ")
        bound = min(canvas_w, canvas_h)
        font_max  = max(40, int(bound * MAX_FONT_RATIO))
        font_wrap = max(30, int(bound * WRAP_THRESHOLD_RATIO))
        font, lines = best_layout(flat, font_path, text_w, text_h,
                                  explicit, font_max, font_wrap)
    else:
        font = ImageFont.truetype(font_path, int(font_size))
        # On continuous + horizontal, the text-axis is unbounded — only wrap
        # at explicit \n. Otherwise wrap to the canvas width.
        if is_cont and orientation == "horizontal":
            lines = text.split("\n")
        else:
            lines = wrap_text(text, font, text_w)

    line_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    total_text_h = line_h * len(lines) + LINE_SPACING * (len(lines) - 1) if lines else 0
    widest_line_w = int(max((font.getlength(l) for l in lines), default=0))

    # Continuous tape auto-length: shrink the long axis to fit text exactly.
    # (The short axis = tape width is always physical and stays fixed.)
    if is_cont:
        if orientation == "horizontal":
            canvas_w = widest_line_w + 2 * PAD
        else:
            canvas_h = total_text_h + 2 * PAD

    img = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(img)
    y = (canvas_h - total_text_h) // 2
    for line in lines:
        # Render centered; the calibration shift is applied post-render so
        # that the preview shows the design as intended, while only the
        # printed bytes carry the offset that compensates for printer drift.
        x = (canvas_w - int(font.getlength(line))) // 2
        draw.text((x, y), line, fill="black", font=font)
        y += line_h + LINE_SPACING
    return img


def preview(img):
    # Unique filename so the viewer opens each preview as its own window
    # instead of refreshing the previous one. /tmp is cleared on reboot.
    out = Path("/tmp") / f"label-preview-{int(time.time() * 1000)}.png"
    img.save(out)
    subprocess.Popen(["xdg-open", str(out)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# --- Calibration ruler ---------------------------------------------------
def render_ruler(tape_dims, calibration_px=0):
    """Render a calibration ruler into a landscape canvas. Always horizontal.

    The ruler's 0-tick is positioned at canvas_w/2 + calibration_px so the
    printed ruler reflects the current calibration. Use the printed label
    + calipers to measure where the 0-tick lands relative to the label
    edges; equal margins on both sides means the calibration cancels the
    printer's drift exactly.
    """
    long_axis, short_axis = tape_dims
    canvas_w, canvas_h = long_axis, short_axis

    avail = available_fonts()
    if not avail:
        sys.exit("error: no fonts available; cannot render ruler.")
    _, font_path = avail[0]
    f_title = ImageFont.truetype(font_path, 20)
    f_num   = ImageFont.truetype(font_path, 20)
    f_edge  = ImageFont.truetype(font_path, 26)

    img  = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(img)

    sign  = "+" if calibration_px >= 0 else ""
    title = f"cal {sign}{calibration_px}px"
    tw    = f_title.getlength(title)
    draw.text(((canvas_w - tw) // 2, 4), title, fill="black", font=f_title)

    # Edge markers — L = leading edge of tape, T = trailing/cut edge.
    draw.text((6, 0), "L", fill="black", font=f_edge)
    tw_t = f_edge.getlength("T")
    draw.text((canvas_w - tw_t - 6, 0), "T", fill="black", font=f_edge)

    y_ruler   = canvas_h - 28
    center_x  = canvas_w // 2 + calibration_px
    mm_extent = int((canvas_w - 20) / DOTS_PER_MM / 2)

    for mm in range(-mm_extent, mm_extent + 1):
        x = center_x + mm * DOTS_PER_MM
        if x < 5 or x >= canvas_w - 5:
            continue
        if mm % 10 == 0:
            h  = 24
            n  = str(abs(mm))
            nw = f_num.getlength(n)
            draw.text((x - nw // 2, y_ruler - h - 22),
                      n, fill="black", font=f_num)
        elif mm % 5 == 0:
            h = 14
        else:
            h = 6
        draw.line([(x, y_ruler), (x, y_ruler - h)], fill="black", width=2)

    # Tall central tick = the 0 reference. Caliper this against label edges.
    draw.line([(center_x, y_ruler - 38), (center_x, y_ruler + 6)],
              fill="black", width=3)
    draw.line(
        [(max(5, int(center_x - mm_extent * DOTS_PER_MM)), y_ruler),
         (min(canvas_w - 5, int(center_x + mm_extent * DOTS_PER_MM)), y_ruler)],
        fill="black", width=2,
    )
    return img


def _send_ruler(tape, dims, calibration_px):
    """Render a ruler and send it. Shared by `-ruler` and the guided flow."""
    img = render_ruler(dims, calibration_px=calibration_px)
    img = img.rotate(-90, expand=True)
    qlr          = BrotherQLRaster(MODEL)
    instructions = convert(qlr, [img], tape, cut=True)
    printer      = resolve_printer()
    send(instructions=instructions, printer_identifier=printer,
         backend_identifier="network")


def print_ruler(args):
    """Action handler for `label -ruler`."""
    cfg = load_config()
    tape_name = args["tape"] or cfg.get("default_tape", DEFAULT_TAPE)
    tape, dims = resolve_tape(tape_name)
    if is_continuous(tape):
        sys.exit("error: ruler requires a die-cut tape (got continuous "
                 f"'{tape}'). Specify with -tape <name> if needed.")

    cal_arg = args["calibration"]
    cal_val = resolve_calibration(cal_arg) if cal_arg is not None else \
              cfg.get("default_calibration", DEFAULT_CALIBRATION_PX)
    _send_ruler(tape, dims, cal_val)


def _ask_mm(prompt):
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit("aborted.")
        raw = raw.rstrip("mm").strip()
        try:
            return float(raw)
        except ValueError:
            print("  please enter a number (e.g. 27.3 or 27.3mm).")


def guided_calibrate(args):
    """Walk the user through measuring printer drift and saving the result.

    Prints a ruler at calibration=0, asks the user to measure both edges
    to the center tick with calipers, computes the drift (and the offset
    needed to cancel it), and offers to save.
    """
    cfg = load_config()
    tape_name = args["tape"] or cfg.get("default_tape", DEFAULT_TAPE)
    tape, dims = resolve_tape(tape_name)
    if is_continuous(tape):
        sys.exit(f"error: calibration needs a die-cut tape (got continuous "
                 f"'{tape}'). Re-run with `label -tape <die-cut-name> "
                 f"-calibrate`.")

    cur = cfg.get("default_calibration", DEFAULT_CALIBRATION_PX)
    src = "saved" if "default_calibration" in cfg else "script default"
    sign = "+" if cur >= 0 else ""
    cur_mm = round(cur / DOTS_PER_MM, 2)
    print(f"Current calibration: {sign}{cur}px ({sign}{cur_mm}mm) [{src}]")
    print()
    print("Guided recalibration:")
    print(f"  1. I'll print one ruler on '{tape}' at calibration=0.")
    print( "  2. You measure both label edges to the center tick (calipers).")
    print( "  3. I'll compute the new value and offer to save.")
    print()
    print(f"Make sure '{tape}' is loaded. Press Enter to print the ruler "
          "(Ctrl+C to abort).")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit("aborted.")

    _send_ruler(tape, dims, calibration_px=0)
    print()
    print("On the printed label, find the tall center tick. With calipers,")
    print("measure the distance (in mm) from each label edge to that tick:")
    print("  - 'L' marker is on the leading edge (came out of printer first).")
    print("  - 'T' marker is on the trailing edge (cut end).")
    print()
    l_edge = _ask_mm("  Distance from L edge to center: ")
    t_edge = _ask_mm("  Distance from T edge to center: ")

    total       = l_edge + t_edge
    true_center = total / 2
    drift_mm    = true_center - l_edge          # +ve = center is closer to L
    new_cal_px  = round(drift_mm * DOTS_PER_MM)
    cal_sign    = "+" if new_cal_px >= 0 else ""
    drift_dir   = "leading" if drift_mm > 0 else "trailing"

    print()
    print(f"Total label length: {total:.2f}mm. True center: {true_center:.2f}mm.")
    if abs(drift_mm) < 0.05:
        print("Center tick is essentially on the true center — printer is "
              "well-aligned at calibration=0.")
    else:
        print(f"Center tick is {abs(drift_mm):.2f}mm off (toward {drift_dir} edge).")
    print(f"Suggested calibration: {cal_sign}{new_cal_px}px "
          f"({cal_sign}{round(drift_mm, 2)}mm).")
    print()

    try:
        save = input("Save as new default? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit("aborted.")

    if save in ("y", "yes"):
        cfg["default_calibration"] = new_cal_px
        save_config(cfg)
        print(f"Saved. Run `label -ruler` to verify alignment.")
    else:
        print("Not saved. Set manually any time with "
              f"`label -calibrate {new_cal_px}`.")


# --- CLI parsing ----------------------------------------------------------
_FLAGS = {
    ("-f", "-font", "--font"):                          "font",
    ("-px", "--px"):                                    "font_size",
    ("-mm", "--mm"):                                    "font_size",
    ("-o", "-orient", "-orientation", "--orientation"): "orientation",
    ("-tape", "--tape"):                                "tape",
    ("-calibrate", "--calibrate"):                      "calibration",
}
_LIST_ACTIONS = {
    "font":        "list_fonts",
    "font_size":   "show_font_size",
    "orientation": "show_orientation",
    "tape":        "list_tapes",
    "calibration": "guided_calibrate",
}
_MM_FLAGS      = ("-mm", "--mm")
_PREVIEW_FLAGS = ("-p", "-preview", "--preview")
_RESET_FLAGS   = ("-reset", "--reset")
_CONFIG_FLAGS  = ("-c", "-config", "--config")
_RULER_FLAGS   = ("-ruler", "--ruler")
_COUNT_FLAGS   = ("-n", "-count", "--count")


def _flag_name(arg):
    for keys, name in _FLAGS.items():
        if arg in keys:
            return name
    return None


def parse_args(argv):
    """Return (args_dict, preview, ruler, text, action).

    action ∈ {help, list_fonts, list_tapes, show_font_size,
              show_orientation, show_calibration, save, print, ruler}
    """
    args = {"font": None, "font_size": None, "orientation": None,
            "tape": None, "calibration": None, "count": None}
    preview_flag = False
    ruler_flag   = False
    rest = list(argv)
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in _RESET_FLAGS:
            return args, False, False, "", "reset"
        if a in _CONFIG_FLAGS:
            return args, False, False, "", "show_config"
        if a in _RULER_FLAGS:
            ruler_flag = True
            i += 1
            continue
        if a in _PREVIEW_FLAGS:
            preview_flag = True
            i += 1
            continue
        if a in _COUNT_FLAGS:
            if i + 1 >= len(rest):
                sys.exit("error: -n requires a count (e.g. `label -n 5 \"Coffee\"`)")
            args["count"] = rest[i + 1]
            i += 2
            continue
        flag = _flag_name(a)
        if flag is None:
            # An unknown dash-prefixed token is almost always a typo'd flag.
            # Exit instead of silently treating it as text and burning a label.
            if a.startswith("-"):
                sys.exit(f"error: unknown flag '{a}'. Run `label` for help.")
            break
        if i + 1 >= len(rest):
            return args, preview_flag, ruler_flag, "", _LIST_ACTIONS[flag]
        val = rest[i + 1]
        if a in _MM_FLAGS:
            val += "mm"   # tag for resolve_font_size to convert
        args[flag] = val
        i += 2

    text = " ".join(rest[i:])

    if ruler_flag:
        return args, preview_flag, True, text, "ruler"
    if not text:
        if all(v is None for v in args.values()) and not preview_flag:
            return args, False, False, "", "help"
        return args, preview_flag, False, "", "save"
    return args, preview_flag, False, text, "print"


# --- Main -----------------------------------------------------------------
def main():
    args, preview_flag, ruler_flag, text, action = parse_args(sys.argv[1:])

    # Validate count early — must be a positive int, only valid when printing.
    count = 1
    if args["count"] is not None:
        if action != "print":
            sys.exit("error: -n only applies when printing (use with text)")
        try:
            count = int(args["count"])
        except ValueError:
            sys.exit(f"error: invalid count '{args['count']}'. "
                     f"Use a positive integer.")
        if count < 1:
            sys.exit(f"error: count must be >= 1 (got {count}).")

    if action == "help":
        sys.exit(__doc__.strip())
    if action == "list_fonts":
        list_fonts(); return
    if action == "list_tapes":
        list_tapes(); return
    if action == "show_font_size":
        show_font_size(); return
    if action == "show_orientation":
        show_orientation(); return
    if action == "show_calibration":
        show_calibration(); return
    if action == "guided_calibrate":
        guided_calibrate(args); return
    if action == "show_config":
        show_config(); return
    if action == "ruler":
        print_ruler(args); return
    if action == "reset":
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            print(f"label: removed {CONFIG_FILE}", file=sys.stderr)
        else:
            print(f"label: no saved defaults to reset", file=sys.stderr)
        return

    cfg = load_config()

    if action == "save":
        if args["font"] is not None:
            name, _ = resolve_font(args["font"])
            cfg["default_font"] = name
            print(f"label: default font set to '{name}'", file=sys.stderr)
        if args["tape"] is not None:
            name, _ = resolve_tape(args["tape"])
            cfg["default_tape"] = name
            print(f"label: default tape set to '{name}'", file=sys.stderr)
        if args["font_size"] is not None:
            v = resolve_font_size(args["font_size"])
            cfg["default_font_size"] = v
            extra = f" (~{_px_to_mm(v)}mm)" if isinstance(v, int) else ""
            print(f"label: default font size set to '{v}'{extra}", file=sys.stderr)
        if args["orientation"] is not None:
            v = resolve_orientation(args["orientation"])
            cfg["default_orientation"] = v
            print(f"label: default orientation set to '{v}'", file=sys.stderr)
        if args["calibration"] is not None:
            v = resolve_calibration(args["calibration"])
            cfg["default_calibration"] = v
            mm = round(v / DOTS_PER_MM, 2)
            sign = "+" if v >= 0 else ""
            print(f"label: default calibration set to {sign}{v}px ({sign}{mm}mm)",
                  file=sys.stderr)
        save_config(cfg)
        return

    # action == "print"
    font_name = args["font"] or cfg.get("default_font", DEFAULT_FONT_NAME)
    tape_name = args["tape"] or cfg.get("default_tape", DEFAULT_TAPE)
    _, font_path = resolve_font(font_name)
    tape, dims   = resolve_tape(tape_name)

    font_size, orientation = effective_settings(
        cfg, tape, args["font_size"], args["orientation"]
    )

    cal_arg = args["calibration"]
    cal_val = resolve_calibration(cal_arg) if cal_arg is not None else \
              cfg.get("default_calibration", DEFAULT_CALIBRATION_PX)

    img = render(text, font_path, font_size, tape, dims, orientation,
                 offset=cal_val)

    if preview_flag:
        preview(img)
        return

    # Apply calibration shift (printer-drift compensation). Layout already
    # reserved 2*|cal| of margin in render(), so this never clips content.
    # Skipped for continuous tapes (auto-length already handles alignment).
    if cal_val and not is_continuous(tape):
        shifted = Image.new(img.mode, img.size, "white")
        shifted.paste(img, (cal_val, 0))
        img = shifted

    # Printer expects portrait orientation; rotate after preview so the
    # preview shows the label the way a human would read it.
    if orientation == "horizontal":
        img = img.rotate(-90, expand=True)

    printer = resolve_printer()
    qlr = BrotherQLRaster(MODEL)
    instructions = convert(qlr, [img] * count, tape, cut=True)

    def _send():
        send(instructions=instructions, printer_identifier=printer,
             backend_identifier="network")

    try:
        _send()
    except Exception:
        if PRINTER_IP is None and PRINTER_IP_CACHE.exists():
            print("label: printer connection failed, rediscovering...", file=sys.stderr)
            PRINTER_IP_CACHE.unlink()
            printer = resolve_printer()
            _send()
        else:
            raise


if __name__ == "__main__":
    main()
