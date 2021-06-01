#!/bin/sh
#!/usr/bin/python3

#This installation script is for setting up a new Pop!_OS installation according to my needs.
cd
clear

sudo apt update && sudo apt upgrade -y && flatpak update -y

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



#input is taken with "read foo"