# This is based on https://vitux.com/how-to-install-ntp-server-and-client-on-ubuntu/

# Please run first: conda install -c conda-forge netifaces

# This sets up the rack computer to be an NTP server which can be used as the
#  time reference for the other analyzer computers.

import shlex
import subprocess

from netifaces import AF_INET, ifaddresses, interfaces

# Install the ntp package
subprocess.run(shlex.split("sudo apt-get update"))
subprocess.run(shlex.split("sudo apt-get install -y ntp"))
subprocess.run(shlex.split("sntp --version"))

# Configure the server to use the US time servers as its reference
with open("/etc/ntp.conf", "r") as fp:
    contents = fp.read()
    contents = contents.replace("ubuntu.pool.ntp.org", "us.pool.ntp.org")

with open("./temp.tmp", "w") as fp:
    fp.write(contents)

subprocess.run(shlex.split("sudo cp ./temp.tmp /etc/ntp.conf"))
subprocess.run(shlex.split("rm ./temp.tmp"))

# Restart the NTP service on the server
subprocess.run(shlex.split("sudo service ntp restart"))
# Allow connections from clients on the nto port 123
subprocess.run(shlex.split("sudo ufw allow from any to any port 123 proto udp"))
# subprocess.run(shlex.split("sudo service ntp status"))

ip_addresses = [(ifname, ifaddresses(ifname)[AF_INET][0]['addr']) for ifname in interfaces()]
print("Set up each client using setup_client. This host has the following IPv4 interfaces:")
print(ip_addresses)
