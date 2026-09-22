#!/usr/bin/env python3
from utils import *
import configparser

# -------------------------- Configure Flameshot --------------------------
# Reads the provided Flameshot file and copies it onto the machine

print("-------------------------- Configuring Flameshot")

if (not is_package_installed("org.flameshot.Flameshot")):
    # User-scoped: Pop!_OS has no system-level flatpak remotes, so this must
    # not run under sudo.
    run_command("flatpak install --user flathub -y org.flameshot.Flameshot")

# Flameshot exposes some settings configuration via command line, set those here
run_command("flatpak run org.flameshot.Flameshot config --autostart true --trayicon false --maincolor '#4287f5'")

# Some configuration options are not exposed via cmd line arg,
# and must be modified in the config file directly. Config file
# is copied/overwritten with the local copy

# The flatpak is not granted xdg-config/flameshot, so it reads its ini from
# inside the sandbox -- writing to ~/.config/flameshot has no effect on it.
# The native path is only written if a non-flatpak Flameshot is also present.
flameshot_settings_file = "./configs/flameshot/flameshot.ini"
flatpak_settings_path = f"{USER_HOME}/.var/app/org.flameshot.Flameshot/config/flameshot/flameshot.ini"
native_settings_path  = f"{USER_HOME}/.config/flameshot/flameshot.ini"

copy_and_overwrite(flameshot_settings_file, flatpak_settings_path)
if (os.path.isdir(os.path.dirname(native_settings_path))):
    copy_and_overwrite(flameshot_settings_file, native_settings_path)

if (is_gnome_session()):
    # Set custom flameshot keybind for Gnome
    run_command("gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings \"['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/Flameshot/']\"")
    run_command("gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/Flameshot/ name 'Flameshot'")
    run_command("gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/Flameshot/ command 'flatpak run org.flameshot.Flameshot gui'")
    run_command("gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/Flameshot/ binding 'Print'")

    # Remove the default Screenshot tool Print keybinding
    run_command("gsettings set org.gnome.shell.keybindings show-screenshot-ui \"[]\"")
    print("-Flameshot default keybind set for Gnome")
