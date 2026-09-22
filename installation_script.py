from utils import *
import getpass
import time

# -------------------------- Packages --------------------------

ppas_to_install = [
    # "ppa:papirus/papirus",               # papirus-icon-theme + papirus-folders
]

apt_packages = [
    "steam", "lutris",# "papirus-icon-theme", "papirus-folders",
    "ffmpeg", "lm-sensors", "tree", "exfat-fuse", # "code",
    # virt-manager pulls in libvirt + qemu-system-x86 + qemu-utils on its own.
    "spice-vdagent", "virt-manager", "virt-viewer",
    # fastfetch, the maintained successor to the abandoned neofetch. Not
    # packaged for 24.04, so --ignore-missing skips it until 26.04.
    "fastfetch"
]
# Flathub and the COSMIC applet repo are separate remotes -- a package can only
# be installed from the remote that actually carries it.
flatpak_packages = [
    "com.bambulab.BambuStudio",              # Bambu Studio
    "com.usebottles.bottles",                # Bottles
    "org.gnome.Cheese",                      # Cheese
    "org.chromium.Chromium",                 # Chromium
    "org.darktable.Darktable",               # Darktable
    "com.discordapp.Discord",                # Discord
    "org.flameshot.Flameshot",               # Flameshot
    "com.github.tchx84.Flatseal",            # Flatseal
    "org.gnome.gitlab.YaLTeR.Identity",      # Identity
    "org.kde.kdenlive",                      # Kdenlive
    "org.kde.krita",                         # Krita
    "com.mojang.Minecraft",                  # Minecraft
    "io.missioncenter.MissionCenter",        # Mission Center
    "io.mpv.Mpv",                            # mpv
    "com.obsproject.Studio",                 # OBS Studio
    "md.obsidian.Obsidian",                  # Obsidian
    "org.pulseaudio.pavucontrol",            # PulseAudio Volume Control
    "com.rawtherapee.RawTherapee",           # RawTherapee
    "com.slack.Slack",                       # Slack
    "com.spotify.Client",                    # Spotify
    "org.videolan.VLC",                      # VLC
    "xyz.xclicker.xclicker",                # XClicker
    "io.github.aandrew_me.ytdn",             # ytDownloader
    "us.zoom.Zoom"                           # Zoom
]
cosmic_flatpak_packages = [
    "io.github.cosmic_utils.minimon-applet", # Minimon (system monitor applet)
    "io.github.TopiCsarno.YapCap"            # YapCap (AI usage applet)
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
git_name = git_email = None
option_generate_sshkey = input("[1/2] Generate SSH key? y/n ").lower()
if (option_generate_sshkey == "y"):
    git_name = input("Enter your global full name for Git: ")
    git_email = input("Enter your global email for Git: ")

option_configure_directories = input("[2/2] Do you want to configure SMB directories?\
    \nWARNING: Symlink will FORCE OVERWRITE user home folders. (y/n): ").lower()
if (option_configure_directories == "y"):
    smb_username = input("Enter your SMB username: ")
    smb_password = getpass.getpass("Enter your SMB password: ")

_ = input("----- Press Enter to Begin -----")

# -------------------------- Begin --------------------------
start_time = time.time()

print("-------------------------- Run Initial Updates")
run_command("sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y && flatpak update -y")

print("-------------------------- Install PPAs")
for ppa in ppas_to_install:
    # add-apt-repository stores "ppa:owner/name" as "owner-ubuntu-name-<codename>.sources",
    # so match on that slug rather than on the ppa: string itself.
    ppa_slug = ppa.removeprefix("ppa:").replace("/", "-ubuntu-")
    if (not any(ppa_slug in f for f in os.listdir("/etc/apt/sources.list.d"))):
        result = run_command(f"sudo add-apt-repository -y {ppa}")
    else:
        print(f"-PPA {ppa} already installed")
if (ppas_to_install):
    run_command("sudo apt update")

# -------------------------- Configure NAS Directories --------------------------
print("-------------------------- Configure NAS Directories")
if (option_configure_directories == "y"):
    # Passed via the environment, not argv -- command lines are world-readable
    # through /proc, process environments are not.
    os.environ["SMB_USERNAME"] = smb_username
    os.environ["SMB_PASSWORD"] = smb_password
    result = run_script("configure_directories.py")
    os.environ.pop("SMB_PASSWORD", None)
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

# Flatpak remotes on Pop!_OS are user-scoped, so these must NOT run under sudo.
# Both remotes are assumed to already exist -- Pop!_OS sets them up. A "Remote
# not found" error here means one needs adding with `flatpak remote-add --user`.
run_command(f"flatpak install --user flathub -y {' '.join(flatpak_packages)}")
run_command(f"flatpak install --user cosmic -y {' '.join(cosmic_flatpak_packages)}")

# -------------------------- Run Program Configurations --------------------------
print("-------------------------- Configuring programs")
result = run_script("configure_flameshot.py")
if result["returncode"] != 0:
    error_messages.append("ERROR: Flameshot configuration failed.")

# result = run_script("configure_vscode.py")
# if result["returncode"] != 0:
#     error_messages.append("ERROR: VSCode configuration failed.")

result = run_script("configure_firefox.py")
if result["returncode"] != 0:
    error_messages.append("ERROR: Firefox configuration failed.")

result = run_script("configure_minimon.py")
if result["returncode"] != 0:
    error_messages.append("ERROR: Minimon configuration failed.")

result = run_script("configure_scripts.py")
if result["returncode"] != 0:
    error_messages.append("ERROR: Custom scripts setup failed.")

# -------------------------- Install Services --------------------------
print("-------------------------- Installing services")
run_command("bash ./services/wave3-audio-fix.sh")
run_command("bash ./services/kanto-audio-fix.sh")

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
if (git_name and git_email):
    run_command(f"git config --global user.name '{git_name}'")
    run_command(f"git config --global user.email '{git_email}'")
else:
    print("-Skipping Git identity, no name/email collected")
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
        print(f"\t-{str(warning).strip()}")

if (error_messages):
    print(f"-{len(error_messages)} errors have occured: ")
    for error in error_messages:
        print(f"\t-{str(error).strip()}")
else:
    print("-Success: No errors.")

run_time = int(time.time() - start_time)
minutes = run_time // 60
seconds = run_time % 60

print(f"Setup complete. Runtime {minutes}m {seconds}s")
