#!/bin/bash -i

# Set-up the dev and production environment for PiGSS
# Assumes a bare/minimal Ubuntu 18.04.x iso has been used

# TODO - Set keybidings
# TODO - Fix Alt+Print Scrot Keybinding
# TODO - Change GTK Theme
# TODO - Maybe implement plymouth picarro splash screen

# Paths used in this script
gitDir="${HOME}/git"
scriptDir=$PWD

# Force a time sync -- useful for when using an old VM snapshot
# apt will reject authentication if the date/time is too far off
sudo systemctl restart systemd-timesyncd

# Add user to dialout group
groups | grep dialout || sudo usermod -a -G dialout ${USER}

# Disable auto package updates and unattended upgrades
if [ -f /etc/apt/apt.conf.d/20auto-upgrades ]; then
    sudo sed -i 's/"1"/"0"/g' /etc/apt/apt.conf.d/20auto-upgrades
else
    sudo sh -c \
    "printf 'APT::Periodic::Update-Package-Lists "0";\nAPT::Periodic::Unattended-Upgrade "0";' \
    > /etc/apt/apt.conf.d/20auto-upgrades"
fi

# Remove gnome/ubuntu software GUIs and update-notifier
kill $(pidof gnome-software)
kill $(pidof ubuntu-software)
kill $(pidof update-notifier)
sudo apt remove -y ubuntu-software gnome-software update-notifier

# Remove CUPS (printer service)
sudo systemctl disable cups.service
sudo systemctl disable cups-browsed.service
sudo apt remove -y cups

# Disable auto screen lock
gsettings set org.gnome.desktop.session idle-delay 0

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

# Set wallpaper
sudo cp -r $scriptDir/picarro_logo.png /usr/share/backgrounds/
gsettings set org.gnome.desktop.background primary-color '#ffffff'
gsettings set org.gnome.desktop.background secondary-color '#ffffff'
gsettings set org.gnome.desktop.background picture-options 'scaled'
gsettings set org.gnome.desktop.background picture-uri 'file:///usr/share/backgrounds/picarro_logo.png'

# Set the display resolution to 1080p
xrandr --output `xrandr | grep " connected"|cut -f1 -d" "` --mode 1920x1080

# Add environmental variables to .bashrc
echo $GOPATH | grep go || echo "export GOPATH=$HOME/go" >> ${HOME}/.bashrc
echo $PATH | grep miniconda || echo "export PATH=$HOME/miniconda3/bin:$HOME/miniconda3/condabin:/usr/local/go/bin:$PATH" \
>> ${HOME}/.bashrc
echo $PYTHONPATH | grep git || echo "export PYTHONPATH="${gitDir}:${gitDir}/host$PYTHONPATH"" >> ${HOME}/.bashrc

# Get Miniconda install script and install
if [ ! -d /home/$USER/miniconda3 ]; then
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
	chmod +x Miniconda3-latest-Linux-x86_64.sh
	./Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
fi

# Update this shell to use the new environment vars
source ${HOME}/.bashrc
# We have to re-define all variables after sourcing a
# .bashrc file when the script is run in interactive mode
gitDir="${HOME}/git"
scriptDir=$PWD

# Set up miniconda environment(s)
conda env update -f $scriptDir/pigss_conda_env.yaml
conda init bash
conda activate base

# Configure the Node.js Repo
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -

# Do a full update/upgrade
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

# Build and install pigss-meta package
printf '\n\nBuilding pigss-meta package\n\n\n'
$scriptDir/../Build/pigss_meta/build_pigss_meta
printf '\n\nInstalling pigss-meta package\n\n\n'
sudo apt install -y /tmp/pigss-meta*.deb
printf '\n\nRemoving pigss-meta package from /tmp'
rm -rf /tmp/pigss-meta*.deb

# Set chromium as default browser
xdg-settings set default-web-browser chromium-browser.desktop

# Set custom keybindings for scrot
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_full_screenshot/', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_focused_screenshot/']"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_full_screenshot/ name "Scrot Fullscreen"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_full_screenshot/ command "scrot ${HOME}/Pictures/$HOSTNAME-$(date +%Y%m%d_%H%M%S).png"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_full_screenshot/ binding "Print"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_focused_screenshot/ name "Scrot Focused"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_focused_screenshot/ command "scrot -u ${HOME}/Pictures/$HOSTNAME-$(date +%Y%m%d_%H%M%S).png"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom_focused_screenshot/ binding "<Alt>Print"

# Configure git
printf "\nEnter your Picarro GitHub Username: "
read githubUserName
printf "\nEnter your Picarro GitHub Email: "
read githubEmail
git config --global user.name "${githubUserName}"
git config --global user.email "${githubEmail}"

# Install global Node.js dependencies
sudo npm list -g | grep node-gyp || sudo npm install -g node-gyp
sudo npm list -g | grep yarn || sudo npm install -g yarn

# Install fpm (required to build native grafana production packages)
gem list fpm | grep fpm || sudo gem install fpm

# Put our files in the ~/Downloads folder
cd ${HOME}/Downloads

# Install bat (like cat but with syntax highlighting)
if ! which bat 2> /dev/null; then
    wget https://github.com/sharkdp/bat/releases/download/v0.11.0/bat_0.11.0_amd64.deb
    sudo dpkg -i bat_0.11.0_amd64.deb
    rm -rf bat_0.11.0_amd64.deb
fi

# Install influxdb from site -- apt version is too old
if ! which influx 2> /dev/null; then
    wget https://dl.influxdata.com/influxdb/releases/influxdb_1.7.7_amd64.deb
    sudo dpkg -i influxdb_1.7.7_amd64.deb
    rm -rf influxdb_1.7.7_amd64.deb
    # Enable and start influxdb services
    sudo systemctl daemon-reload && sudo systemctl enable influxdb.service \
    && sudo systemctl start influxd.service && sudo systemctl start influxdb.service
fi

# Make sure golang is installed
if [ ! -d /usr/local/go ]; then
    printf '\nGo not found!\n'
    printf 'Downloading Go...\n\n'
    cd $HOME/Downloads
    wget https://dl.google.com/go/go1.12.1.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go*.tar.gz
    rm -rf go*.tar.gz
fi

# Disable ubuntu splash at boot
sudo sed -i 's/"quiet splash"/"quiet"/g' /etc/default/grub
sudo update-grub

sudo cp -r $scriptDir/../Build/buildMenu.sh /usr/bin/picarro-build-menu
printf "\nReady to build! Enter picarro-build-menu in new terminal to launch...\n\n"; sleep 1s
