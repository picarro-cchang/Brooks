"""
This is based on information at https://help.ubuntu.com/lts/serverguide/NTP.html

 It is used to configure the Picarro analyzers on the network to use the rack server as their time
 standard. It sends the file setup_client.py to the client and runs it there as root.

 NOTE: The rack server must first be set up as an chrony time server (e.g., by using setup_server.py)
  before this will work. It should have a static IP address on the local network since this is
  written to a configuration file on the client.
"""
import ipaddress
import os
import sys

import subprocess
import json

access_str = os.environ.get('PIGSS_CLIENT_ACCESS')

analyzers_list = []
with open('../../../../.config/picarro/madmapper.json') as json_file:
  data = json.load(json_file)
  for analyzers in data["Devices"]["Network_Devices"]:
    analyzers_list.append(analyzers)

command = "cat /etc/chrony/chrony.conf"
command = command.split()
string = "allow " + ip

cmd1 = subprocess.Popen(['echo',access_str], stdout=subprocess.PIPE)
cmd2 = subprocess.Popen(['sudo','-S'] + command, stdin=cmd1.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(cmd2.stdout.read())

# current_chrony = os.system('echo %s|sudo -S %s' % (access_str, command))[0]
# print(current_chrony)