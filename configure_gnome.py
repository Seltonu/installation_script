from utils import *

print("-------------------------- Configuring Gnome")

# -------------------------- Configure Gnome Settings --------------------------
# Flameshot keybind set in configure_flameshot.py
# NOTE: Running gsettings commands with sudo will silently fail because the exitcode is a false success. The result is "0: command not found".

gnome_settings = [
    ("org.gnome.shell favorite-apps", "['org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop', 'firefox.desktop',\
        'com.discordapp.Discord.desktop', 'com.spotify.Client.desktop', 'steam.desktop', 'code.desktop', 'com.slack.Slack.desktop']"),
    ("org.gnome.desktop.session idle-delay", "900"), #set screen off time to 15 minutes
    ("org.gnome.desktop.interface clock-show-weekday", "true"),
    ("org.gnome.desktop.interface clock-show-seconds", "true"),
    ("org.gnome.desktop.calendar show-weekdate", "true"),
    ("org.gnome.desktop.wm.preferences button-layout", "':minimize,maximize,close'"),
    ("org.gnome.nautilus.preferences show-image-thumbnails", "'always'"),
    ("org.gnome.nautilus.preferences recursive-search", "'always'"),
    ("org.gnome.nautilus.preferences default-folder-viewer", "'icon-view'"),
    ("org.gnome.nautilus.preferences open-folder-on-dnd-hover", "false"),
    ("org.gnome.nautilus.preferences show-directory-item-counts", "'always'")
]

if (is_package_installed("papirus-icon-theme")):
    run_command("gsettings set org.gnome.desktop.interface icon-theme 'Papirus'")
if (is_package_installed("papirus-folders")):
    run_command("papirus-folders -C paleorange")

if (is_gnome_session()):
    for setting, value in gnome_settings:
        run_command(f"gsettings set {setting} {value}")
else:
    print("-Skipping Gnome configuration, Gnome is not the current DE.")
    warning_messages.append("Skipped Gnome configuration. Gnome is not the current DE.")
