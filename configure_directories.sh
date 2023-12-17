#!/bin/bash

echo "-------------------------- SMB Directory Configuration --------------------------"

# The purpose of this script is to mount the NAS folders for the user directories,
# and point my default folders to use those instead. This keeps most files off my main machine.

# Check if username and password are provided as command-line arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <username> <password>"
    exit 1
fi

# Define the SMB server and share
smb_server="vault.local"
smb_share="home"
smb_mount_point="/mnt/vault"

# Extract username and password from command-line arguments
username="$1"
password="$2"

sudo apt install -y --ignore-missing cifs-utils

# Mount the SMB share if not already mounted
if ! mountpoint -q "$smb_mount_point"; then
    sudo mkdir -p "$smb_mount_point"
    sudo mount -t cifs -o username="$username",password="$password" "//$smb_server/$smb_share" "$smb_mount_point"
    # Add an entry to /etc/fstab for automatic mounting on boot
    echo "//$smb_server/$smb_share $smb_mount_point cifs username=$username,password=$password,uid=$(id -u),gid=$(id -g),file_mode=0777,dir_mode=0777 0 0" | sudo tee -a /etc/fstab
fi

# Note: Some folders like desktop and downloads are kept local to serve as rapid access "scratch" areas
read -r -d '' new_content <<EOF
# This file is written by xdg-user-dirs-update
# If you want to change or add directories, just edit the line you're
# interested in. All local changes will be retained on the next run.
# Format is XDG_xxx_DIR="\$HOME/yyy", where yyy is a shell-escaped
# homedir-relative path, or XDG_xxx_DIR="/yyy", where /yyy is an
# absolute path. No other format is supported.
# 
XDG_DESKTOP_DIR="$HOME/Desktop"
XDG_DOWNLOAD_DIR="$HOME/Downloads"
XDG_TEMPLATES_DIR="$HOME/Templates"
XDG_PUBLICSHARE_DIR="$HOME/Public"
XDG_DOCUMENTS_DIR="$smb_mount_point/Documents"
XDG_MUSIC_DIR="$smb_mount_point/Music"
XDG_PICTURES_DIR="$smb_mount_point/Pictures"
XDG_VIDEOS_DIR="$smb_mount_point/Videos"
EOF

# Make a backup and overwrite the user-dirs.dirs file with the new content
cp "$HOME/.config/user-dirs.dirs" "$HOME/.config/user-dirs.dirs.bak"
echo "$new_content" > "$HOME/.config/user-dirs.dirs"

# Rename local folders to avoid confusion, they will still show in Nautilus sidebar.
# They can also be deleted if empty and not needed.
mv "$HOME/Documents" "$HOME/Local Documents"
mv "$HOME/Music" "$HOME/Local Music"
mv "$HOME/Pictures" "$HOME/Local Pictures"
mv "$HOME/Videos" "$HOME/Local Videos"

echo "User folders set to remote locations. SMB Setup complete."
