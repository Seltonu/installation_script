#!/bin/bash
#!/usr/bin/python3

#This installation script is for setting up a new Pop!_OS installation according to my needs.

cd
clear
echo "Enter name for device"
read device_name
echo "Setup unattended? y/n"
read unattended
start=$SECONDS

sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y && flatpak update -y

# ################## install software ################## 

#add PPAs for software I use, first checking if PPA already installed
if (! ls /etc/apt/sources.list.d | grep -q papirus)
then
    sudo add-apt-repository -y ppa:papirus/papirus
else
    printf "Papirus PPA already installed.\n"
fi
# if (! ls /etc/apt/sources.list.d | grep -q sysmontask)
# then
#     sudo add-apt-repository -y ppa:camel-neeraj/sysmontask
# else
#     printf "Sysmontask PPA already installed.\n"
# fi
# No longer want howdy currently.
# if (! ls /etc/apt/sources.list.d | grep -q howdy)
# then
#     sudo add-apt-repository -y ppa:boltgolt/howdy
# else
#     printf "Howdy PPA already installed.\n"
# fi


sudo apt install -y --ignore-missing \
steam \
lutris \
flameshot \
papirus-icon-theme \
papirus-folders \
# sysmontask \
ffmpeg \
neofetch \
# xclip \
ibus-mozc \
code


# # "sudo -u $SUDO_USER" is needed to run the commands outside of sudo (normal user), required for flatpak installation
flatpak install flathub -y \
com.discordapp.Discord \
com.spotify.Client \
# com.visualstudio.code \ # No longer want flatpak, use official deb.
# org.deluge_torrent.deluge \
org.kde.kdenlive \
org.kde.krita \
org.gnome.Boxes \
# us.zoom.Zoom \ # No longer used.
com.slack.Slack \
# org.videolan.VLC \ # Use mpv instead
io.mpv.Mpv \
com.obsproject.Studio \
com.mojang.Minecraft \
org.darktable.Darktable \
com.rawtherapee.RawTherapee \
org.gnome.Cheese \
com.github.tchx84.Flatseal \
org.pulseaudio.pavucontrol

firefox "lutris:league-of-legends-standard-launch-help" & disown
firefox https://addons.mozilla.org/firefox/downloads/file/3807401/bitwarden_free_password_manager-1.51.1-an+fx.xpi & disown

#add pip modules
# development on discord bot has currently ceased, libraries not needed.
# sudo apt install python3-pip -y
# pip_packages='discord.py[voice] youtube-dl'
# sudo python3 -m pip install -U $pip_packages


################## customizations ################## 
# WARNING: this will overwrite any existing .bash_aliases file!
echo "alias upup='sudo apt update && sudo apt upgrade -y && flatpak update -y'" | sudo tee ~/.bash_aliases
# echo "alias minecraft='clear && cd ~/Minecraft\ Server/ && ./start.sh'" | sudo tee -a ~/.bash_aliases # No longer hosted on this machine.
# echo "alias botbot='clear && cd ~/Gits/BotBot/ && python3 bot.py'" | sudo tee -a ~/.bash_aliases # No longer hosted on this machine.
# echo "alias yt-video=\"youtube-dl --ignore-errors --verbose -f 'bestvideo+bestaudio' --output '%(title)s.%(ext)s'\"" | sudo tee -a ~/.bash_aliases
# echo "alias yt-audio=\"youtube-dl --ignore-errors --verbose --extract-audio --audio-format mp3 --audio-quality 0 --output '%(title)s.%(ext)s'\"" | sudo tee -a ~/.bash_aliases

source .bash_aliases #load aliases file to be used immediately

#Change device name
# device_name="box"
sudo hostnamectl set-hostname --static $device_name

gsettings set org.gnome.desktop.session idle-delay 900 #set screen off time to 15 minutes
gsettings set org.gnome.desktop.interface clock-show-weekday true
gsettings set org.gnome.desktop.interface clock-show-seconds true
gsettings set org.gnome.desktop.calendar show-weekdate true
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('ibus', 'mozc-jp')]" #add Japanese keyboard
gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close'
gsettings set org.gnome.desktop.interface icon-theme 'Papirus'


git config --global user.name "Steven Gutierrez"
git config --global user.email "steven.s.gutier@gmail.com"

papirus-folders -C paleorange
flameshot config --autostart true --trayicon false --maincolor \#4287f5
#~/.config/flameshot/flameshot.ini
#config file still needs modification to avoid notification popup. No CLI config available.

#### Favorite Apps
gsettings set org.gnome.shell favorite-apps "['pop-cosmic-launcher.desktop', 'org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop', 'firefox.desktop', \
'com.discordapp.Discord.desktop', 'com.spotify.Client.desktop', 'steam.desktop', 'code.desktop', 'com.slack.Slack.desktop', 'pop-cosmic-applications.desktop']"



printf "\nSettings updated.\n"

############## SSH KEY SETUP ##############
if [[ $unattended != y* ]]
then
    echo "Generate SSH key? y/n"
    read generate_ssh_bool
fi

if [[ $generate_ssh_bool = y* || $unattended = y* ]]
then
    printf "\n Generating SSH key...\n"
    ssh-keygen -t ed25519 -N "" -f ~/.ssh/github_key -C "steven.s.gutier@gmail.com"
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/github_key
    # No longer installing xclip
    # xclip -selection clipboard < ~/.ssh/github_key.pub 
    # printf "\nSSH Pub Key copied to clipboard.\n"
else
    printf "Skipping SSH key.\n"
fi

duration=( $SECONDS - start )
printf "Setup complete. Runtime $duration seconds\n"



#Notes:
#input is taken with "read foo"

#Todo:
#change mount points of attached drives to identify by label
#create symlinks for folders on Koi drive to home
#set refresh rates of monitors to highest
#add custom keyboard shortcuts (printscrn for "flameshot gui")
#add try catch for adding PPAs (prevents breakage on OS version update)