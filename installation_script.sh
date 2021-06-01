#!/bin/sh
#!/usr/bin/python3

#My first attempt at bash scripting.
#This installation script is for setting up a new Pop!_OS installation according to my needs.

cd
clear
sudo apt update && sudo apt upgrade -y && flatpak update -y

################## install software
# "sudo -u $SUDO_USER" is needed to run the commands outside of sudo (normal user), required for flatpak installation
sudo -u $SUDO_USER flatpak install flathub com.discordapp.Discord -y
sudo -u $SUDO_USER flatpak install flathub com.spotify.Client -y
sudo -u $SUDO_USER flatpak install flathub com.visualstudio.code -y
sudo -u $SUDO_USER flatpak install flathub org.deluge_torrent.deluge -y
sudo -u $SUDO_USER flatpak install flathub org.kde.kdenlive -y
sudo -u $SUDO_USER flatpak install flathub org.kde.krita -y
sudo -u $SUDO_USER flatpak install flathub org.gnome.Boxes -y
sudo -u $SUDO_USER flatpak install flathub us.zoom.Zoom -y
sudo -u $SUDO_USER flatpak install flathub org.videolan.VLC -y
sudo -u $SUDO_USER flatpak install flathub com.obsproject.Studio -y
sudo -u $SUDO_USER flatpak install flathub com.mojang.Minecraft -y
sudo -u $SUDO_USER flatpak install flathub org.darktable.Darktable -y
sudo -u $SUDO_USER flatpak install flathub com.rawtherapee.RawTherapee -y


# WARNING: this will overwrite any existing .bash_aliases file!
echo "alias upup='sudo apt update && sudo apt upgrade -y && flatpak update -y'" > .bash_aliases
echo "alias minecraft='clear && cd ~/Minecraft\ Server/ && ./start.sh'" >> .bash_aliases
echo "alias botbot='clear && cd ~/Gits/BotBot/ && python3 bot.py'" >> .bash_aliases

source .bash_aliases #load aliases file to be used immediately

#Change device name
device_name="box"
#echo $device_name > /etc/hostname
#python3 rename_files.py  #this needs to be modified to accept command line args first
#sudo sed "s/pop-os/$device_name/" /etc/hosts


#add pip modules
sudo apt install python3-pip -y
pip_packages="discord.py[voice]"
python3 -m pip install -U "$pip_packages"


#Notes:
#input is taken with "read foo"

#Todo:
#install flatpak softwares I use
#change mount points of attached drives to identify by label
#create symlinks for folders on Koi drive to home
#set refresh rates of monitors to highest
#enable Japanese keyboard
#add custom keyboard shortcuts (printscrn for "flameshot gui")
#change sleep time of device