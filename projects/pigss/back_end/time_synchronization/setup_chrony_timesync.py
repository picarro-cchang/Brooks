import os
import sys
import subprocess
import json

def timesync_chrony_setup(ip_list):
  access_str = os.environ.get('PIGSS_CLIENT_ACCESS')

  #change permissions so that the file can be modified
  permission_cmd = "chmod 777 /etc/chrony/chrony.conf"
  permission_cmd = permission_cmd.split()

  cmd = subprocess.Popen(['echo', access_str], stdout=subprocess.PIPE)
  subprocess.run(['sudo','-S'] + permission_cmd, stdin=cmd.stdout)

  #append ips that are not stored in chrony.conf
  with open("/etc/chrony/chrony.conf", "r+") as f:
    current_chrony = f.read()
    for ip in ip_list:
      if 'allow ' + ip not in current_chrony:
          f.write("allow " + ip + " \n")
  f.close()

  #return permissions to original state
  permission_cmd2 = "chmod 644 /etc/chrony/chrony.conf"
  permission_cmd2 = permission_cmd2.split()
  subprocess.run(['sudo','-S'] + permission_cmd2, stdin=cmd.stdout)
  
  #restart chrony
  chrony_cmd = "systemctl restart chrony"
  chrony_cmd = chrony_cmd.split()
  subprocess.run(['sudo','-S'] + chrony_cmd, stdin=cmd.stdout)

