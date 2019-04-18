#!/bin/bash

# Set-up the dev environment for PIGSS
# Assumes a bare Ubuntu-Mate 18.04 iso has been used

# Put our files in the ~/Downloads folder
cd ${HOME}/Downloads

# Install curl
sudo apt update
sudo apt install -y curl

# Get Miniconda install script and install
if [ ! -d /home/$USER/miniconda3 ]; then
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
	chmod +x Miniconda3-latest-Linux-x86_64.sh
	./Miniconda3-latest-Linux-x86_64.sh
fi

# Install apt packages we need
sudo apt update
sudo apt install -y influxdb-client openssh-server chromium-browser

# Install influxdb from site -- apt version is too old
wget https://dl.influxdata.com/influxdb/releases/influxdb_1.7.5_amd64.deb
sudo dpkg -i influxdb_1.7.5_amd64.deb

echo ""
echo "Please run the setUpGrafanaDevFromSource.sh"
echo ""


