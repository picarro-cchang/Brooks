import os
import sys
import subprocess

access_str = os.environ.get('PIGSS_CLIENT_ACCESS')

def timesync_chrony_setup(ip_list):
  cmd = 'chmod 777 /etc/chrony/chrony.conf'
  os.system('echo %s|sudo -S %s' % (access_str, cmd))

  #append ips that are not stored in chrony.conf
  with open('/etc/chrony/chrony.conf', 'r+') as f:
    current_chrony = f.read()
    for ip in ip_list:
      if ('allow ' + ip) not in current_chrony:
          f.write('allow ' + ip + ' \n')

  #return permissions to original state
  permission_cmd2 = 'chmod 644 /etc/chrony/chrony.conf'
  os.system('echo %s|sudo -S %s' % (access_str, permission_cmd2))

  #restart chrony
  chrony_cmd = 'systemctl restart chrony'
  os.system('echo %s|sudo -S %s' % (access_str, chrony_cmd))

