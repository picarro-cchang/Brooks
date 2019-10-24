"""
This is based on information at https://help.ubuntu.com/lts/serverguide/NTP.html
Also see https://stackoverflow.com/questions/20499074/run-local-python-script-on-remote-server
 It is used to configure the Picarro analyzers on the network to use the rack server as their time
 standard.
 NOTE: The rack server must first be set up as an chrony time server (e.g., by using setup_server.py)
  before this will work. It should have a static IP address on the local network since this is
  written to a configuration file.
"""
import asyncio

from back_end.lologger.lologger_client import LOLoggerClient

log = LOLoggerClient(client_name="SetupTimeSyncClient", verbose=True)
TMP_FILENAME = "/tmp/setup_client.py"

# The script setup_client.py is contained in the string setup_client_script, which is copied
#  to /tmp/setup_client.py when this script is imported. The co-routine time_sync_analyzers
#  runs the following in a subprocess for each client in analyzer_ips
#
#    python /tmp/setup_client.py deploy ip-address-of-client
#
# This causes paramiko to rewrite /etc/timesyncd.conf on the client with the server
#  address and to restart the systemd-timesyncd service on the client

# Note: Care is needed to escape backslashes in setup_client_script so that it is correctly
#  written out to disk
setup_client_script = """
import os
import shlex
import subprocess
import sys
import time

my_path = os.path.dirname(os.path.abspath(__file__))
access_str = os.environ.get('PIGSS_CLIENT_ACCESS', "310595054")


def sudo_run(cmd):
    p = subprocess.Popen(shlex.split("sudo -S %s" % cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate(access_str + "\\n")


def run(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()


def install():
    # This is executed on the client to install the software
    print(sudo_run("cp /tmp/timesyncd.conf /etc/timesyncd.conf")[0])
    print(sudo_run("timedatectl set-ntp true")[0])
    print(sudo_run("systemctl restart systemd-timesyncd")[0])
    print("== After restarting timesyncd service ==")
    time.sleep(3.0)
    print(sudo_run("systemctl status systemd-timesyncd")[0])


if __name__ == "__main__":
    try:
        if sys.argv[1] == 'deploy':
            # The following is executed on the server
            import ipaddress
            import paramiko
            from netifaces import AF_INET, ifaddresses, interfaces

            netmask = 24
            client_address = sys.argv[2]
            client = int.from_bytes(ipaddress.IPv4Address(client_address).packed, 'big')

            ip_addresses = [(ifname, ifaddresses(ifname)[AF_INET][0]['addr']) for ifname in interfaces()]
            # Find the IP address of the time server by iterating through the IP addresses on its
            #  network interfaces and finding one which is on the same subnet as the client
            for ifname, ifaddr in ip_addresses:
                server = int.from_bytes(ipaddress.IPv4Address(ifaddr).packed, 'big')
                if (client ^ server) < (1 << (32 - netmask)):
                    server_address = ifaddr
                    break
            else:
                raise ValueError("Cannot find server for %s within network with netmask %d" % (client_address, netmask))

            # Set up the configuration file for ntp on the client
            with open("/tmp/timesyncd.conf", "w") as fp:
                fp.write("[Time]\\n")
                fp.write("NTP=%s\\n" % server_address)

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(client_address, username="picarro", password=access_str)

            sftp = client.open_sftp()
            # Use secure FTP to copy this script to the client
            sftp.put(__file__, "/tmp/myscript.py")

            # Copy the generated ntp.conf file to the client
            sftp.put("/tmp/timesyncd.conf", "/tmp/timesyncd.conf")

            print("\\n\\nCopying script to client and starting execution...")
            # Execute the script on the client and record the results
            stdout = client.exec_command("python /tmp/myscript.py install")[1]
            for line in stdout:
                print(line.rstrip())
            client.close()
            sys.exit(0)
        elif sys.argv[1] == 'install':
            install()
            sys.exit(0)
    except IndexError:
        pass
"""
with open(TMP_FILENAME, "w") as fp:
    fp.write(setup_client_script)


async def time_sync_analyzers(analyzer_ips):
    for ip in analyzer_ips:
        proc = await asyncio.create_subprocess_shell(f"python {TMP_FILENAME} deploy {ip}",
                                                     stdin=asyncio.subprocess.PIPE,
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        log.info(f"TimeSyncClient {ip} returns {proc.returncode} stdout: {stdout.decode()}")
        log.info(f"TimeSyncClient {ip} returns {proc.returncode} stderr: {stderr.decode()}")
        await proc.wait()
