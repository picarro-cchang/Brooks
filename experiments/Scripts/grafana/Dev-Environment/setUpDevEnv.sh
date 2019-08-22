#!/bin/bash

# Set-up the dev and production environment for PiGSS
# Assumes a bare/minimal Ubuntu 18.04.x iso has been used

# TODO - Get Picarro wallpaper and set background using gsettings
# TODO - Set keybidings
# TODO - Setup scrot add to keybidings

# Picarro Git paths
gitDir="${HOME}/git"
scriptDir=$PWD

# Disable auto package updates and unattended upgrades
if [ -f /etc/apt/apt.conf.d/20auto-upgrades ]; then
    sudo sed -i 's/"1"/"0"/g' /etc/apt/apt.conf.d/20auto-upgrades
else
    sudo sh -c \
    "printf 'APT::Periodic::Update-Package-Lists "0";\nAPT::Periodic::Unattended-Upgrade "0";' \
    > /etc/apt/apt.conf.d/20auto-upgrades"
fi

# Disable auto screen lock
gsettings set org.gnome.desktop.session idle-delay 0

# Remove gnome/ubuntu software GUIs and update-notifier
sudo apt remove -y ubuntu-software gnome-software update-notifier

# Disable desktop icons
gsettings set org.gnome.desktop.background show-desktop-icons false

# Prevent gnome from opening file manager when external media is plugged in
gsettings set org.gnome.desktop.media-handling automount-open false

# Prevent the user from locking the screen
gsettings set org.gnome.desktop.lockdown disable-lock-screen true

# Prevent the user from logging out
gsettings set org.gnome.desktop.lockdown disable-log-out true

# Disable gnome user administration
gsettings set org.gnome.desktop.lockdown user-administration-disabled true

# Prevent the user from switching users in an active session
gsettings set org.gnome.desktop.lockdown disable-user-switching true

# Prevent the user from opening print dialogs
gsettings set org.gnome.desktop.lockdown disable-printing true
gsettings set org.gnome.desktop.lockdown disable-print-setup true

# Disable banner notifications
gsettings set org.gnome.desktop.notifications show-banners false
gsettings set org.gnome.desktop.notifications show-in-lock-screen false

# Disable screensaver
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
gsettings set org.gnome.desktop.screensaver lock-enabled false

# Set default file browser view to list-view
gsettings set org.gnome.nautilus.preferences default-folder-viewer list-view

# Enable on-screen keyboard
gsettings set org.gnome.desktop.a11y.applications screen-keyboard-enabled true

# Disable geolocation
gsettings set org.gnome.system.location enabled false

# Do a full update/upgrade
sudo apt update
sudo apt upgrade -y

# Install git and build tools
sudo apt install -y git ruby ruby-dev rubygems build-essential

# Configure git
echo "Enter your Picarro GitHub Username: "
read githubUserName
echo "Enter your Picarro GitHub Email: "
read githubEmail
git config --global user.name "${githubUserName}"
git config --global user.email "${githubEmail}"

# Install curl
sudo apt install -y curl

# Configure the Node.js Repo
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -

# Install Node.js
sudo apt install -y nodejs

# Install Node Package Manager
sudo apt install -y npm

# Install global Node.js dependencies
sudo npm install -g node-gyp
sudo npm install -g yarn

# Install fpm (required to build native grafana production packages)
sudo gem install fpm

# Put our files in the ~/Downloads folder
cd ${HOME}/Downloads

# Get Miniconda install script and install
if [ ! -d /home/$USER/miniconda3 ]; then
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
	chmod +x Miniconda3-latest-Linux-x86_64.sh
	./Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
fi

# Add environmental variables to .bashrc
echo "export GOPATH=$HOME/go" >> ${HOME}/.bashrc
echo "export PATH=$HOME/miniconda3/bin:$HOME/miniconda3/condabin:/usr/local/go/bin:$PATH" \
>> ${HOME}/.bashrc
echo "export PYTHONPATH="${gitDir}$PYTHONPATH"" >> ${HOME}/.bashrc
source ${HOME}/.bashrc

# Install openssh-server
sudo apt install -y openssh-server

# Install chromium
sudo apt install -y chromium-browser

# Install gnome-terminal
sudo apt install -y gnome-terminal

# Install gnome tweaks
sudo apt install -y gnome-tweaks

# Install dconf-editor
sudo apt install -y dconf-editor

# Install influxdb from site -- apt version is too old
if ! which influx 2> /dev/null; then
    wget https://dl.influxdata.com/influxdb/releases/influxdb_1.7.5_amd64.deb
    sudo dpkg -i influxdb_1.7.5_amd64.deb
    # Enable and start influxdb services
    sudo systemctl daemon-reload && sudo systemctl enable influxdb.service \
    && sudo systemctl start influxd.service && sudo systemctl start influxdb.service
fi

# Make sure golang is installed
if [ ! -d /usr/local/go ]; then
    echo "Go not found!"
    echo ""
    echo "Downloading Go..."
    echo ""
    cd $HOME/Downloads
    wget https://dl.google.com/go/go1.12.1.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go*.tar.gz
fi

echo "Ready to build! Launching menu..."; sleep 1s

# Launch the build menu
gnome-terminal -- $scriptDir/../Build/buildMenu.sh
