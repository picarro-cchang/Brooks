"""This script is copied to the client to carry out time synchronization with the host server.
    It should be located on the server at /usr/local/share/picarro/setup_client.py
"""
import os
import shlex
import subprocess
import time

access_str = os.environ.get('PIGSS_CLIENT_ACCESS')


def sudo_run(cmd):
    p = subprocess.Popen(shlex.split("sudo -S %s" % cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate(access_str + "\n")


def run(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()


if __name__ == "__main__":
    print(sudo_run("cp /tmp/timesyncd.conf /etc/systemd/timesyncd.conf")[0])
    print(sudo_run("timedatectl set-ntp true")[0])
    print(sudo_run("systemctl restart systemd-timesyncd")[0])
    print("== After restarting timesyncd service ==")
    time.sleep(3.0)
    print(sudo_run("systemctl status systemd-timesyncd")[0])
    current_cron = sudo_run("crontab -l")[0]
    if "systemctl restart systemd-timesyncd" not in current_cron:
        with open("tmp_cron.txt", "w+") as f:
            f.write(current_cron)
            f.write("* * * * * systemctl restart systemd-timesyncd\n")
        print(sudo_run("crontab tmp_cron.txt")[0])
        print(sudo_run("rm -rf tmp_cron,txt")[0])
