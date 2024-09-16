from utils import *
import getpass
import time
# import os

git_name = "Steven Gutierrez"
git_email = "steven.s.gutier@gmail.com"
smb_username = None
smb_password = None
start_time = None
ppas_to_install = ["ppa:papirus/papirus"]

apt_packages = [
    "steam", "lutris", "flameshot", "papirus-icon-theme", "papirus-folders",
    "ffmpeg", "neofetch", "code", "lm-sensors", "tree"
]
flatpak_packages = [
    "com.discordapp.Discord", "com.spotify.Client", "org.kde.kdenlive", "org.kde.krita",
    "org.gnome.Boxes", "com.slack.Slack", "io.mpv.Mpv", "com.obsproject.Studio",
    "com.mojang.Minecraft", "org.darktable.Darktable", "com.rawtherapee.RawTherapee",
    "org.gnome.Cheese", "com.github.tchx84.Flatseal", "org.pulseaudio.pavucontrol",
    "org.chromium.Chromium", "io.github.aandrew_me.ytdn", "org.gnome.gitlab.YaLTeR.Identity",
    "io.missioncenter.MissionCenter"
]
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

# -------------------------- Script Startup --------------------------
# Anything that requires user input should go here, so the script can run without
# prompting the user after this section is complete

print("-------------------------- Installation Script --------------------------")

if (os.geteuid() == 0):
    print("This script must be run as a normal user, not root.")
    exit(1)

# Change device name
device_name = input("Enter name for this machine: ")
run_command(f"hostnamectl set-hostname --static {device_name}")

# Configuration options
option_generate_sshkey = input("Generate SSH key? y/n ").lower()
option_configure_directories = input("Do you want to configure SMB directories?\
    \nWARNING: Symlink will FORCE OVERWRITE user home folders. (y/n): ").lower()


if (option_configure_directories == "y"):
    smb_username = input("Enter your SMB username: ")
    smb_password = getpass.getpass("Enter your SMB password: ")

input("----- Press Enter to Begin -----")

# -------------------------- Begin --------------------------
start_time = time.time()

print("-------------------------- Run Initial Updates")
run_command("sudo apt update && apt upgrade -y && apt autoremove -y && flatpak update -y")

print("-------------------------- Install PPAs")
for ppa in ppas_to_install:
    if (not any(ppa in f for f in os.listdir("/etc/apt/sources.list.d"))):
        result = run_command(f"sudo add-apt-repository -y {ppa}")
    else:
        print(f"-PPA {ppa} already installed")
run_command("sudo apt update")

# -------------------------- Configure NAS Directories --------------------------
print("-------------------------- Configure NAS Directories")
if (option_configure_directories == "y"):        
    result = run_script("configure_directories.sh", f"{smb_username} {smb_password}")
else:
    print("-Configuring SMB directories skipped")
    warning_messages.append("Configuring SMB directories skipped")

# -------------------------- Icon/Folder/Theme --------------------------
print("-------------------------- Configure theme")
run_command("sudo apt install -y papirus-icon-theme papirus-folders")
run_command("gsettings set org.gnome.desktop.interface icon-theme 'Papirus'")
run_command("papirus-folders -C paleorange")

# -------------------------- Install Software --------------------------
print("-------------------------- Install packages")
run_command(f"sudo apt install -y --ignore-missing {' '.join(apt_packages)}")
run_command(f"sudo flatpak install flathub -y {' '.join(flatpak_packages)}")

# -------------------------- Run Program Configurations --------------------------
print("-------------------------- Configuring programs")
result = run_script("configure_flameshot.sh")
if result["returncode"] != 0:
    error_messages.append("ERROR: Flameshot configuration failed.")

result = run_script("configure_vscode.sh")
if result["returncode"] != 0:
    error_messages.append("ERROR: VSCode configuration failed.")

result = run_script("configure_firefox.sh")
if result["returncode"] != 0:
    error_messages.append("ERROR: Firefox configuration failed.")

print("--------------------------")
print("Program configurations complete.")

# -------------------------- Bash Aliases --------------------------
# WARNING: this will overwrite any existing .bash_aliases file!
with open(os.path.expanduser("~/.bash_aliases"), 'w') as bash_aliases:
    bash_aliases.write("alias upup='sudo apt update && sudo apt upgrade -y && sudo apt autoremove && flatpak update -y'\n")
# make the command useable without needing to reboot
run_command("source ~/.bash_aliases")
print("-Bash aliases file updated")

# -------------------------- Configure Gnome Settings --------------------------
print("-------------------------- Configuring Gnome")
if (is_gnome_session()):
    for setting, value in gnome_settings:
        run_command(f"gsettings set {setting} {value}")
else:
    print("-Skipping Gnome configuration, Gnome is not the current DE.")
    warning_messages.append("Skipped Gnome configuration. Gnome is not the current DE.")

# -------------------------- Configure Displays --------------------------
# note, none of this code is likely to be useful anymore with the switch to cosmic
# print("-------------------------- Configuring displays (experimental)")
# result = run_command("xrandr --listmonitors | awk '{print $4}'")
# displays = result.stdout.splitlines()

# for display in displays:
#     result = run_command(f"xrandr | grep '{display}' -A 1 | grep -oP '\\d{{3,}}x\\d{{3,}}'", capture_output=True)
#     mode = result.stdout.strip()
#     if mode:
#         run_command(f"xrandr --output {display} --mode {mode}")

# -------------------------- SSH KEY SETUP --------------------------
print("-------------------------- Configuring SSH key setup")
run_command(f"git config --global user.name '{git_name}'")
run_command(f"git config --global user.email '{git_email}'")
run_command("git config --global init.defaultBranch main")

if (option_generate_sshkey == 'y'):
    print("-Generating SSH key...")
    generation_date = time.strftime("%b %Y")
    ssh_key_path = os.path.expanduser(f"~/.ssh/{device_name}_{generation_date}")
    run_command(f"ssh-keygen -t ed25519 -N '' -f {ssh_key_path} -C '{git_email}'")
    run_command("eval $(ssh-agent -s)")
    run_command(f"ssh-add {ssh_key_path}")
    with open(f"{ssh_key_path}.pub") as ssh_key_file:
        print(ssh_key_file.read())
else:
    print("-Skipping SSH key generation")

# -------------------------- End --------------------------
print("-------------------------- Summary")

if (warning_messages):
    print(f"-{len(warning_messages)} warnings have occured: ")
    for warning in warning_messages:
        print(f"\t-{warning}", end="")

if (error_messages):
    print(f"-{len(error_messages)} errors have occured: ")
    for error in error_messages:
        print(f"\t-{error}", end="")
else:
    print("-Success: No errors.")

run_time = int(time.time() - start_time)
minutes = run_time // 60
seconds = run_time % 60

print(f"Setup complete. Runtime {minutes}m {seconds}s")
