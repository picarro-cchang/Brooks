#!/bin/bash

# Set-up the dev environment for PIGSS
# Assumes a bare Ubuntu-Mate 18.04.2 iso has been used


# Picarro Git paths
gitDir="${HOME}/git"
grafanaDir="${gitDir}/host/experiments/grafana/src/github.com/grafana/grafana"

# Do a full update/upgrade
sudo apt update
sudo apt upgrade -y

# Install git and build tools
sudo apt install -y git build-essential

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

# Put our files in the ~/Downloads folder
cd ${HOME}/Downloads

# Get Miniconda install script and install
if [ ! -d /home/$USER/miniconda3 ]; then
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
	chmod +x Miniconda3-latest-Linux-x86_64.sh
	./Miniconda3-latest-Linux-x86_64.sh
fi

# Install apt packages we need
sudo apt install -y openssh-server chromium-browser

# Install influxdb from site -- apt version is too old
wget https://dl.influxdata.com/influxdb/releases/influxdb_1.7.5_amd64.deb
sudo dpkg -i influxdb_1.7.5_amd64.deb
# Enable and start influxdb services
sudo systemctl daemon-reload && sudo systemctl enable influxdb.service && sudo systemctl start influxd.service && sudo systemctl start influxdb.service

# Make sure golang is installed
if [ ! -d /usr/local/go ]; then
    echo "Go not found!"
    echo ""
    echo "Downloading Go..."
    echo ""
    cd $HOME/Downloads
    wget https://dl.google.com/go/go1.12.1.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go*.tar.gz
    # Add environmental variables to .bashrc
    echo "export GOPATH=$HOME/go" >> ${HOME}/.bashrc
    echo "export PATH=/usr/local/go/bin:$PATH" >> ${HOME}/.bashrc
    echo "export PYTHONPATH="${gitDir}$PYTHONPATH"" >> ${HOME}/.bashrc
    source ${HOME}/.bashrc
fi

# Build Grafana back-end
export GOPATH=$HOME/go
export PATH=/usr/local/go/bin
export PYTHONPATH=${gitDir}
cd $grafanaDir
go run build.go setup
go run build.go build

# Build Grafana front-end
yarn install --pure-lockfile
yarn build

# Start Grafana
bin/linux-amd64/grafana-server

# echo ""
# echo "Please run the setUpGrafanaDevFromSource.sh"
# echo ""


