#!/bin/sh
#!/usr/bin/python3

#This installation script is for setting up a new Pop!_OS installation according to my needs.

cd
clear
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y && flatpak update -y

# ################## install software ################## 
# sudo apt install -y lutris steam flameshot

# # "sudo -u $SUDO_USER" is needed to run the commands outside of sudo (normal user), required for flatpak installation
# flatpak install flathub com.discordapp.Discord -y
# flatpak install flathub com.spotify.Client -y
# flatpak install flathub com.visualstudio.code -y
# flatpak install flathub org.deluge_torrent.deluge -y
# flatpak install flathub org.kde.kdenlive -y
# flatpak install flathub org.kde.krita -y
# flatpak install flathub org.gnome.Boxes -y
# flatpak install flathub us.zoom.Zoom -y
# flatpak install flathub org.videolan.VLC -y
# flatpak install flathub com.obsproject.Studio -y
# flatpak install flathub com.mojang.Minecraft -y
# flatpak install flathub org.darktable.Darktable -y
# flatpak install flathub com.rawtherapee.RawTherapee -y


# #add pip modules
# sudo apt install python3-pip -y
# pip_packages='discord.py[voice] youtube-dl'
# sudo python3 -m pip install -U $pip_packages


################## customizations ################## 
# WARNING: this will overwrite any existing .bash_aliases file!
echo "alias upup='sudo apt update && sudo apt upgrade -y && flatpak update -y'" | sudo tee ~/.bash_aliases
echo "alias minecraft='clear && cd ~/Minecraft\ Server/ && ./start.sh'" | sudo tee -a ~/.bash_aliases
echo "alias botbot='clear && cd ~/Gits/BotBot/ && python3 bot.py'" | sudo tee -a ~/.bash_aliases
echo "alias yt-video=\"youtube-dl --ignore-errors --verbose -f 'bestvideo+bestaudio' --output '%(title)s.%(ext)s'\"" | sudo tee -a ~/.bash_aliases
echo "alias yt-audio=\"youtube-dl --ignore-errors --verbose --extract-audio --audio-format mp3 --audio-quality 0 --output '%(title)s.%(ext)s'\"" | sudo tee -a ~/.bash_aliases

source .bash_aliases #load aliases file to be used immediately

#Change device name
device_name="box"
sudo hostnamectl set-hostname --static $device_name
# echo $device_name > /etc/hostname
# sudo sed "s/pop-os/$device_name/" /etc/hosts

gsettings set org.gnome.desktop.session idle-delay 720 #set screen off time to 12 minutes
gsettings set org.gnome.desktop.interface clock-show-weekday true
gsettings set org.gnome.desktop.interface clock-show-seconds true
gsettings set org.gnome.desktop.calendar show-weekdate true
# ACTION="flameshot gui"
# KEY="PrintSc"
# gsettings set org.gnome.desktop.wm.keybindings $KEY $ACTION
# gsettings set org.gnome.mutter.keybindings $KEY $ACTION
# gsettings set org.gnome.settings-daemon.plugins.media-keys $KEY $ACTION

git config --global user.name "Steven Gutierrez"
git config --global user.email "steven.s.gutier@gmail.com"

#Notes:
#input is taken with "read foo"

#Todo:
#change mount points of attached drives to identify by label
#create symlinks for folders on Koi drive to home
#set refresh rates of monitors to highest
#enable Japanese keyboard
#add custom keyboard shortcuts (printscrn for "flameshot gui")
#change sleep time of device