#!/bin/bash

# Set-up the dev environment for PIGSS
# Assumes a bare/minimal Ubuntu 18.04.x iso has been used

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

# Install apt packages we need
sudo apt install -y openssh-server chromium-browser

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
