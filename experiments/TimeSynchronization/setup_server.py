# This is based on https://help.ubuntu.com/lts/serverguide/NTP.html

# Please run first: conda install -c conda-forge netifaces

# This sets up the rack computer to be an NTP server which can be used as the
#  time reference for the other analyzer computers.

import shlex
import subprocess

from netifaces import AF_INET, ifaddresses, interfaces

# Install chrony if it is not already installed
result = subprocess.run(shlex.split("dpkg -l chrony"))
if result.returncode:
    subprocess.run(shlex.split("sudo apt-get update"))
    subprocess.run(shlex.split("sudo apt-get install -y chrony"))

# Restart the chrony service on the server
subprocess.run(shlex.split("sudo systemctl restart chrony.service"))

# Enable the next line if firewall is used to allow connections from clients on the into port 123
# subprocess.run(shlex.split("sudo ufw allow from any to any port 123 proto udp"))

ip_addresses = [(ifname, ifaddresses(ifname)[AF_INET][0]['addr']) for ifname in interfaces()]
print("Set up each client using setup_client. This host has the following IPv4 interfaces:")
print(ip_addresses)
