#!/bin/bash
#!/usr/bin/python3

#This installation script is for setting up a new Pop!_OS installation according to my needs.

git_name="Steven Gutierrez"
git_email="steven.s.gutier@gmail.com"


# -------------------------- Startup -------------------------- 

echo "-------------------------- SETUP SCRIPT --------------------------"

if [[ $EUID -eq 0 ]]; then
   echo "This script must be run as a normal user, not root." 
   exit 1
else
    echo "Please enter root password to make system changes"
    sudo -v #prompt for sudo password
fi

#Change device name
read -p "Enter name for device: " device_name
sudo hostnamectl set-hostname --static $device_name

read -p "Generate SSH key? y/n " generate_ssh

echo "Do you want to configure SMB directories?"
read -p "WARNING: Symlink will FORCE OVERWRITE user home folders. (y/n): " configure_directories
if [[ "$configure_directories" == "y" || "$configure_directories" == "Y" ]]; then
    read -p "Enter your SMB username: " smb_username
    read -s -p "Enter your SMB password: " smb_password
    echo  # Add a newline after password input for readability
fi

echo "--------------------------"
start=$SECONDS

error_messages=""
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y && flatpak update -y


# -------------------------- Configure Home Directories from NAS --------------------------

if [[ "$configure_directories" == "y" || "$configure_directories" == "Y" ]]; then
    ./configure_directories.sh "$smb_username" "$smb_password"
else
    echo "Configuring directories to SMB shares setup skipped."
    error_messages+="WARNING: Configuring directories to SMB shares setup skipped.\n"
fi


# -------------------------- Icon/Folder Theme --------------------------
echo "-------------------------- Install PPAs --------------------------"
# Install papirus PPA, configure folders and icons

ppa_name="ppa:papirus/papirus"
if (! ls /etc/apt/sources.list.d | grep -q "papirus"); then
    # Try to add the Papirus PPA
    if sudo add-apt-repository -y "$ppa_name"; then
        echo "Added PPA $ppa_name"

        # Install Papirus icon theme and folders
        sudo apt update
        sudo apt install -y papirus-icon-theme papirus-folders

        # Configure Papirus icon theme settings
        gsettings set org.gnome.desktop.interface icon-theme 'Papirus'
        papirus-folders -C paleorange
    else
        echo "ERROR: adding PPA $ppa_name"
        error_messages+="ERROR adding PPA $ppa_name\n"
        # You can choose to exit the script or handle the error in some other way
        # exit 1
    fi
else
    printf "$ppa_name already installed.\n"

    # Configure Papirus icon theme settings
    gsettings set org.gnome.desktop.interface icon-theme 'Papirus'
    papirus-folders -C paleorange
fi

# -------------------------- Install Software --------------------------
echo "-------------------------- Install Software --------------------------"
sudo apt install -y --ignore-missing \
steam \
lutris \
flameshot \
papirus-icon-theme \
papirus-folders \
ffmpeg \
neofetch \
ibus-mozc \
code \
lm-sensors

flatpak install flathub -y \
com.discordapp.Discord \
com.spotify.Client \
org.kde.kdenlive \
org.kde.krita \
org.gnome.Boxes \
com.slack.Slack \
io.mpv.Mpv \
com.obsproject.Studio \
com.mojang.Minecraft \
org.darktable.Darktable \
com.rawtherapee.RawTherapee \
org.gnome.Cheese \
com.github.tchx84.Flatseal \
org.pulseaudio.pavucontrol \
org.chromium.Chromium \
io.github.aandrew_me.ytdn \
org.gnome.gitlab.YaLTeR.Identity \
io.missioncenter.MissionCenter


# -------------------------- Run Program Configurations --------------------------
./configure_flameshot.sh && echo "Flameshot configuration succesful." || error_messages+="ERROR: Flameshot configuration failed.\n"
./configure_vscode.sh && echo "VSCode configuration succesful." || error_messages+="ERROR: VSCode configuration failed.\n"
./configure_firefox.sh && echo "Firefox configuration succesful." || error_messages+="ERROR: Firefox configuration failed.\n"
echo "-----------------------------------------------"
echo "Program configurations complete."

# -------------------------- Bash Aliases --------------------------

# WARNING: this will overwrite any existing .bash_aliases file!
echo "alias upup='sudo apt update && sudo apt upgrade -y && sudo apt autoremove && flatpak update -y'" | sudo tee ~/.bash_aliases
source ~/.bash_aliases #load aliases file to be used immediately
echo "Bash aliases updated."


# -------------------------- Configure Gnome settings --------------------------
echo "-------------------------- Configure Gnome --------------------------"

# Set Favorites in Dock
gsettings set org.gnome.shell favorite-apps "['pop-cosmic-launcher.desktop', 'org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop', 'firefox.desktop', \
'com.discordapp.Discord.desktop', 'com.spotify.Client.desktop', 'steam.desktop', 'code.desktop', 'com.slack.Slack.desktop', 'pop-cosmic-applications.desktop']"
# Gnome DE settings
gsettings set org.gnome.desktop.session idle-delay 900 #set screen off time to 15 minutes
gsettings set org.gnome.desktop.interface clock-show-weekday true
gsettings set org.gnome.desktop.interface clock-show-seconds true
gsettings set org.gnome.desktop.calendar show-weekdate true
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('ibus', 'mozc-jp')]" #add Japanese keyboard
gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close'
# Nautilus settings
gsettings set org.gnome.nautilus.preferences show-image-thumbnails 'always'
gsettings set org.gnome.nautilus.preferences recursive-search 'always'
gsettings set org.gnome.nautilus.preferences default-folder-viewer 'icon-view'
gsettings set org.gnome.nautilus.preferences open-folder-on-dnd-hover false
gsettings set org.gnome.nautilus.preferences show-directory-item-counts 'always'

echo "Gnome Settings updated."


# -------------------------- Configure Displays --------------------------
echo "-------------------------- Configure Displays --------------------------"

# Set the maximum refresh rate for all connected displays
xrandr --listmonitors | awk '{print $4}' | while read -r display; do
    mode="$(xrandr | grep "$display" -A 1 | grep -oP '\d{3,}x\d{3,}')"
    xrandr --output "$display" --mode "$mode"
done

# Enable wayland by commenting out the force disable
if grep -q '^WaylandEnable=false' /etc/gdm3/custom.conf; then
    # Comment out the line using sed and create a backup
    sudo sed -i.bak 's/^WaylandEnable=false/#WaylandEnable=false/' /etc/gdm3/custom.conf
    echo "Wayland unlocked, please select from gear icon on login screen."
else
    echo "ERROR: Could not find WaylandEnable setting in /etc/gdm3/custom.conf."
    error_messages+="ERROR: Could not find WaylandEnable setting in /etc/gdm3/custom.conf."
fi


# -------------------------- SSH KEY SETUP --------------------------
echo "-------------------------- SSH KEY SETUP --------------------------"

git config --global user.name "$gitname"
git config --global user.email "$git_email"
git config --global init.defaultBranch main

if [[ $generate_ssh = "y"* ]]
then
    echo "Generating SSH key..."
    # -N for empty passphrase, -C for comment
    generation_date=`date +%b ``date +%Y`
    ssh-keygen -t ed25519 -N "" -f ~/.ssh/"${device_name}_${generation_date}" -C "$git_email"
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/"${device_name}_${generation_date}"
    cat ~/.ssh/"${device_name}_${generation_date}.pub"
else
    echo "Skipping SSH key."
fi


# -------------------------- End --------------------------

duration=( $SECONDS - start )
echo "-----------------------------------------------"
echo "Setup complete. Runtime $duration seconds"

# Print all accumulated error messages at the end
if [ -n "$error_messages" ]; then
    printf "Errors occurred:\n$error_messages"
else
    echo "No errors."
fi


#(Require Testing):
#set refresh rates of monitors to highest via xrandr
