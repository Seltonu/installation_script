#!/bin/bash
# Elgato Wave:3 Boot Fix Installer
# Mutes microphone and sets gain to 55% on login
#
# Usage: ./install-wave3-fix.sh [--uninstall]
#
# HOW TO REPLICATE:
# 1. Find USB device: lsusb | grep -i <device>
# 2. Find stable card name: cat /proc/asound/cards
# 3. List controls: amixer -c <card_name> contents
# 4. Monitor changes: alsactl monitor (then toggle controls to see numids)
# 5. Test commands: amixer -c <card_name> cset numid=<N> <value>

set -e

SCRIPT="$HOME/.local/bin/fix-wave3-audio.sh"
SERVICE="$HOME/.config/systemd/user/wave3-audio-fix.service"

uninstall() {
    echo "Uninstalling Elgato Wave:3 audio fix..."
    systemctl --user stop wave3-audio-fix.service 2>/dev/null || true
    systemctl --user disable wave3-audio-fix.service 2>/dev/null || true
    rm -f "$SCRIPT" "$SERVICE"
    systemctl --user daemon-reload
    echo "Uninstalled!"
}

install() {
    echo "Installing Elgato Wave:3 audio fix..."
    mkdir -p "$(dirname "$SCRIPT")" "$(dirname "$SERVICE")"

    cat > "$SCRIPT" << 'EOF'
#!/bin/bash
sleep 2
grep -q "Wave3" /proc/asound/cards 2>/dev/null || { logger "Wave:3 not found"; exit 1; }
amixer -c Wave3 cset numid=5 0      # Mute mic
amixer -c Wave3 cset numid=6 55%    # Set gain to 55%
logger "Wave:3 fix applied"
EOF
    chmod +x "$SCRIPT"

    cat > "$SERVICE" << EOF
[Unit]
Description=Elgato Wave:3 Audio Fix
After=pipewire.service wireplumber.service

[Service]
Type=oneshot
ExecStart=$SCRIPT
RemainAfterExit=yes

[Install]
WantedBy=default.target
EOF

    systemctl --user daemon-reload
    systemctl --user enable wave3-audio-fix.service

    echo ""
    echo "Installation complete!"
    echo "The Wave:3 will be muted with 55% gain on each login."
    echo ""
    echo "To test now:   $SCRIPT"
    echo "To uninstall:  $0 --uninstall"
}

# Main
case "${1:-}" in
    --uninstall|-u|uninstall|remove) uninstall ;;
    *) install ;;
esac
