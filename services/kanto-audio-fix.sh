#!/bin/bash
# Kanto ORA Audio Fix Installer for Pop!_OS / Ubuntu
#
# Fixes the issue where Kanto ORA speakers don't output audio on Digital
# Stereo (IEC958) until you manually switch to Analog and back.
#
# Usage: ./install-kanto-fix.sh [--uninstall]
#
# HOW TO REPLICATE:
# 1. Find USB device: lsusb | grep -i <device>
# 2. List cards: pactl list cards short
# 3. List profiles: pactl list cards | grep -A 50 "<card_name>"
# 4. Test toggle: pactl set-card-profile <card_name> <profile>

set -e

SCRIPT="$HOME/.local/bin/fix-kanto-audio.sh"
SERVICE="$HOME/.config/systemd/user/kanto-audio-fix.service"

uninstall() {
    echo "Uninstalling Kanto ORA audio fix..."
    systemctl --user stop kanto-audio-fix.service 2>/dev/null || true
    systemctl --user disable kanto-audio-fix.service 2>/dev/null || true
    rm -f "$SCRIPT" "$SERVICE"
    systemctl --user daemon-reload
    echo "Uninstalled!"
}

install() {
    echo "Installing Kanto ORA audio fix..."
    mkdir -p "$(dirname "$SCRIPT")" "$(dirname "$SERVICE")"

    cat > "$SCRIPT" << 'EOF'
#!/bin/bash
sleep 3
CARD=$(pactl list cards short 2>/dev/null | grep -i "usb" | grep -iE "kanto|ora" | head -1 | awk '{print $2}')
[ -z "$CARD" ] && { logger "Kanto ORA not found"; exit 1; }
pactl set-card-profile "$CARD" output:analog-stereo
sleep 1
pactl set-card-profile "$CARD" output:iec958-stereo
logger "Kanto ORA fix applied: $CARD"
EOF
    chmod +x "$SCRIPT"

    cat > "$SERVICE" << EOF
[Unit]
Description=Kanto ORA Digital Audio Fix
After=pipewire.service wireplumber.service

[Service]
Type=oneshot
ExecStart=$SCRIPT
RemainAfterExit=yes

[Install]
WantedBy=default.target
EOF

    systemctl --user daemon-reload
    systemctl --user enable kanto-audio-fix.service

    echo ""
    echo "Installation complete!"
    echo "The Kanto ORA will toggle Analog→Digital on each login."
    echo ""
    echo "To test now:   $SCRIPT"
    echo "To uninstall:  $0 --uninstall"
}

# Main
case "${1:-}" in
    --uninstall|-u|uninstall|remove) uninstall ;;
    *) install ;;
esac
