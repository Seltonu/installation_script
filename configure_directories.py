from utils import *
import sys
import getpass
# -------------------------- Configure NAS directories --------------------------
# Setup SMB directories that I want auto-mounted from my NAS
print("-------------------------- Configuring SMB Directories")
smb_user = None
smb_pass = None

# Check if username and password were provided via arguments (this script called via another)
if (len(sys.argv) == 3):
    smb_user = sys.argv[1]
    smb_pass = sys.argv[2]
else:
    # if credentials not provided, request them
    user_input = input("SMB username or password not set. Would you like to configure? y/n ").lower()
    if (user_input == 'y'):
        smb_user = input("Enter your SMB username: ")
        smb_pass = getpass.getpass("Enter your SMB password: ")
    else:
        print("-Skipping SMB configuration")
        exit(1)

if (not is_package_installed("cifs-utils")):
    run_command("sudo apt install -y --ignore-missing cifs-utils")

# Share configurations
smb_configs = [
    {
        "server": "vault.local",
        "share": "home",
        "mount_point": "/mnt/vault/home",
    },
    {
        "server": "vault.local",
        "share": "photography",
        "mount_point": "/mnt/vault/photography",
    }
]

for config in smb_configs:
    server = config["server"]
    share = config["server"]
    mount_point = config["mount_point"]
    
    # Mount the SMB share if not already mounted
    if not os.path.ismount(mount_point):
        run_command(f"sudo mkdir -p {mount_point}")
        run_command(f"sudo mount -t cifs -o username={smb_user},password={smb_pass} //{server}/{share} {mount_point}")
        
        # Add an entry to /etc/fstab for automatic mounting on boot
        fstab_entry = f"//{server}/{share} {mount_point} cifs username={smb_user},password={smb_pass},uid=$(id -u),gid=$(id -g),file_mode=0777,dir_mode=0777 0 0"
        run_command(f"echo '{fstab_entry}' | sudo tee -a /etc/fstab")

# Load the new mount points
run_command("sudo mount -a")

# Update user-dirs.dirs with new remote paths. Home directory is first entry in smb_configs
new_content = f'''
# This file is written by xdg-user-dirs-update
# If you want to change or add directories, just edit the line you're
# interested in. All local changes will be retained on the next run.
# Format is XDG_xxx_DIR="$HOME/yyy", where yyy is a shell-escaped
# homedir-relative path, or XDG_xxx_DIR="/yyy", where /yyy is an
# absolute path. No other format is supported.
# 
XDG_DESKTOP_DIR="$HOME/Desktop"
XDG_DOWNLOAD_DIR="$HOME/Downloads"
XDG_TEMPLATES_DIR="$HOME/Templates"
XDG_PUBLICSHARE_DIR="$HOME/Public"
XDG_DOCUMENTS_DIR="{smb_configs[0]['mount_point']}/Documents"
XDG_MUSIC_DIR="{smb_configs[0]['mount_point']}/Music"
XDG_PICTURES_DIR="{smb_configs[0]['mount_point']}/Pictures"
XDG_VIDEOS_DIR="{smb_configs[0]['mount_point']}/Videos"
'''

# Make a backup and overwrite the user-dirs.dirs file with the new content
run_command(f"cp '{USER_HOME}/.config/user-dirs.dirs' '{USER_HOME}/.config/user-dirs.dirs.bak'")
run_command(f"echo '{new_content}' > '{USER_HOME}/.config/user-dirs.dirs'")

# Rename local folders to avoid confusion, they will still show in Nautilus sidebar.
# They can also be deleted if empty and not needed.
run_command(f"mv '{USER_HOME}/Documents' '{USER_HOME}/Local Documents'")
run_command(f"mv '{USER_HOME}/Music' '{USER_HOME}/Local Music'")
run_command(f"mv '{USER_HOME}/Pictures' '{USER_HOME}/Local Pictures'")
run_command(f"mv '{USER_HOME}/Videos' '{USER_HOME}/Local Videos'")