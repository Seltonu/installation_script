#!/bin/bash

echo "-------------------------- Flameshot Configuration --------------------------"

# Flameshot is a screenshotting tool with drawing capabilities
flameshot config --autostart true --trayicon false --maincolor \#4287f5

# Some configuration options are not exposed via cmd line arg,
# and must be modified in the config file directly.

# Path to the Flameshot configuration file
config_file="$HOME/.config/flameshot/flameshot.ini"

# Check if the Flameshot configuration file exists
if [ -e "$config_file" ]; then
    # Disable desktop notifications (if not already disabled)
    if ! grep -q 'enabled=false' "$config_file"; then
        echo "[Notifications]" >> "$config_file"
        echo "enabled=false" >> "$config_file"
        echo "Flameshot: Desktop notifications disabled."
    else
        echo "Flameshot: Desktop notifications are already disabled."
    fi

    # Disable the welcome message (if not already disabled)
    if ! grep -q 'FirstRun=false' "$config_file"; then
        echo "[App]" >> "$config_file"
        echo "FirstRun=false" >> "$config_file"
        echo "Flameshot: Welcome message on launch disabled."
    else
        echo "Flameshot: Welcome message on launch is already disabled."
    fi

    # Change gnomescreenshot keybind to 'flameshot' screenshotting tool instead
    gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name 'Flameshot'
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command 'flameshot gui'
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding '<Print>'

else
    echo "Flameshot configuration file not found at: $config_file"
    exit 1
fi


printf "Flameshot configuration complete.\n"