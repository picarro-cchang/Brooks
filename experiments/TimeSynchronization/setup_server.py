# This is based on https://vitux.com/how-to-install-ntp-server-and-client-on-ubuntu/

# Please run: conda install -c conda-forge netifaces

import shlex
import subprocess

from netifaces import AF_INET, ifaddresses, interfaces

subprocess.run(shlex.split("sudo apt-get update"))
subprocess.run(shlex.split("sudo apt-get install -y ntp"))
subprocess.run(shlex.split("sntp --version"))

with open("/etc/ntp.conf", "r") as fp:
    contents = fp.read()
    contents = contents.replace("ubuntu.pool.ntp.org", "us.pool.ntp.org")

with open("./temp.tmp", "w") as fp:
    fp.write(contents)

subprocess.run(shlex.split("sudo cp ./test.tmp /etc/ntp.conf"))
subprocess.run(shlex.split("rm ./temp.tmp"))

subprocess.run(shlex.split("sudo service ntp restart"))
subprocess.run(shlex.split("sudo ufw allow from any to any port 123 proto udp"))
subprocess.run(shlex.split("sudo service ntp status"))

ip_addresses = [(ifname, ifaddresses(ifname)[AF_INET][0]['addr']) for ifname in interfaces()]
print("Specify the time server address on the LAN when setting up clients. This host has the following IPv4 interfaces:")
print(ip_addresses)
