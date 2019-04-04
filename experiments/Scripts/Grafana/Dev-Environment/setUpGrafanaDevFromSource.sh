#!/bin/bash -i

# Quick script to replace grafana backend routing to allow
# custom configuration menu items.

# Picarro Git paths
gitDir="${HOME}/git"
configDir="${gitDir}/host/experiments/Configuration"

# Grafana Git paths
# We are assuming you have set GOPATH to /home/picarro/go
grafanaSourceDir="${GOPATH}/src/github.com/grafana/grafana"

# Install dependencies
sudo apt install -y git build-essential
sudo snap install node --channel=10/stable --classic
sudo npm install -g node-gyp
sudo npm install -g yarn

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

# Make sure our configDir exists
if [ ! -d ${configDir} ]; then
    echo "${configDir} does not exist!"
    echo "Clone I2000-Host into /home/$USER/git/ rename I2000-Host folder to host"
    exit
fi

# Make sure we have the Grafana source
if [ ! -d ${grafanaSourceDir} ]; then
    echo "Grafana source not found!"
    echo ""
    echo "Downloading source..."
    mkdir -p ${HOME}/go
    cd ${GOPATH}
    go get github.com/grafana/grafana
fi

# Brute force copy/replace index.go file to add Picarro configuration
# items to config menu in grafana
cp -rv $configDir/index.go /home/gerald/go/src/github.com/grafana/grafana/pkg/api/
cp -rv $configDir/routes.ts /home/gerald/go/src/github.com/grafana/grafana/public/app/routes/

# symlink Picarro config ui items into features folder
featuresDir="${HOME}/go/src/github.com/grafana/grafana/public/app/features/"
ln -s ${HOME}/git/host/experiments/Configuration/modbus-settings ${featuresDir}
ln -s ${HOME}/git/host/experiments/Configuration/network-settings ${featuresDir}

# symlink Picarro plugins
ln -s ${HOME}/git/host/experiments/networking/grafana/picarro-networking-plugin-tsx ${HOME}/go/src/github.com/grafana/grafana/data/plugins/picarro-networking-plugin-tsx
ln -s ${HOME}/git/host/experiments/ModbusSettings/picarro-modbus-settings ${HOME}/go/src/github.com/grafana/grafana/data/plugins/picarro-modbus-settings
ln -s ${HOME}/git/host/learn/examples/grafana/plugins/picarro-valve-panel ${HOME}/go/src/github.com/grafana/grafana/data/plugins/picarro-valve-panel
echo ""
echo "Ready to build front and back-end!"
echo ""
echo "Don't forget to build your plug-ins!"
echo ""
