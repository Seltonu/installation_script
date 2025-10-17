from utils import *
import getpass
import time

# -------------------------- Packages --------------------------

ppas_to_install = ["ppa:papirus/papirus"]

apt_packages = [
    "steam", "lutris",# "papirus-icon-theme", "papirus-folders",
    "ffmpeg", "neofetch", "code", "lm-sensors", "tree", "exfat-fuse",
    "qemu", "spice-vdagent", "virglrenderer", "virt-manager", "virt-viewer"
]
flatpak_packages = [
    "com.discordapp.Discord", "com.spotify.Client", "org.kde.kdenlive", "org.kde.krita",
    "org.flameshot.Flameshot", "com.slack.Slack", "io.mpv.Mpv", "com.obsproject.Studio",
    "com.mojang.Minecraft", "org.darktable.Darktable", "com.rawtherapee.RawTherapee",
    "org.gnome.Cheese", "com.github.tchx84.Flatseal", "org.pulseaudio.pavucontrol",
    "org.chromium.Chromium", "io.github.aandrew_me.ytdn", "org.gnome.gitlab.YaLTeR.Identity",
    "io.missioncenter.MissionCenter"
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
option_generate_sshkey = input("[1/2] Generate SSH key? y/n ").lower()
if (option_generate_sshkey == "y"):
    git_name = input("Enter your global full name for Git")
    git_email = input("Enter your global email for Git")

option_configure_directories = input("[2/2] Do you want to configure SMB directories?\
    \nWARNING: Symlink will FORCE OVERWRITE user home folders. (y/n): ").lower()
if (option_configure_directories == "y"):
    smb_username = input("Enter your SMB username: ")
    smb_password = getpass.getpass("Enter your SMB password: ")

_ = input("----- Press Enter to Begin -----")

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
if (is_gnome_session()):
    result = run_script("configure_gnome.py")
    if result["returncode"] != 0:
        error_messages.append("ERROR: Gnome configuration failed.")
#
# -------------------------- Install Software --------------------------
print("-------------------------- Install packages")
run_command(f"sudo apt install -y --ignore-missing {' '.join(apt_packages)}")
run_command(f"sudo flatpak install flathub -y {' '.join(flatpak_packages)}")

# -------------------------- Run Program Configurations --------------------------
print("-------------------------- Configuring programs")
result = run_script("configure_flameshot.py")
if result["returncode"] != 0:
    error_messages.append("ERROR: Flameshot configuration failed.")

result = run_script("configure_vscode.py")
if result["returncode"] != 0:
    error_messages.append("ERROR: VSCode configuration failed.")

result = run_script("configure_firefox.py")
if result["returncode"] != 0:
    error_messages.append("ERROR: Firefox configuration failed.")



print("--------------------------")
print("Program configurations complete.")

# -------------------------- Bash Aliases --------------------------
# WARNING: this will overwrite any existing .bash_aliases file!
with open(os.path.expanduser("~/.bash_aliases"), 'w') as bash_aliases:
    bash_aliases.write("alias upup='sudo apt update && sudo apt upgrade -y && sudo apt autoremove && flatpak update -y'\n")
    bash_aliases.write("alias upups='sudo apt update && sudo apt upgrade -y && sudo apt autoremove && flatpak update -y && shutdown now'\n")
    bash_aliases.write("alias upupr='sudo apt update && sudo apt upgrade -y && sudo apt autoremove && flatpak update -y && sudo reboot now'\n")
    bash_aliases.write("alias apt-fix='sudo dpkg --configure -a'\n")
run_command("source ~/.bash_aliases") # Make the command useable without needing to reboot
print("-Bash aliases file updated")


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
