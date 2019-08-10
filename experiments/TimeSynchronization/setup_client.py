# This is based on information at https://vitux.com/how-to-install-ntp-server-and-client-on-ubuntu/
# Also see https://stackoverflow.com/questions/20499074/run-local-python-script-on-remote-server

# This script is run on the rack server which has been set up as an ntp time server (using setup_server.py)
#  in order to configure the Picarro analyzers on the network to use it as their time standard.
# Note that the rack server should be given a static IP address since this is written to configuration files
#  on the clients

# Usage:
#     setup_client deploy ip-address-of-client
#
# The script copies itself to the client via sftp and runs itself there (without the deploy argument) to perform
#  the installation. It installs ntp and ntpdate from .deb packages which it copies to the client. These
#  files are appropriate for UBUNTU 16.04 LTS (xenial). This script will need to be modified for use with a
#  different version of the OS on the client.

import os
import shlex
import subprocess
import sys
import time

my_path = os.path.dirname(os.path.abspath(__file__))
pkg_list = ["libopts25_5.18.7-3_amd64.deb", "ntp_4.2.8p4+dfsg-3ubuntu5.9_amd64.deb", "ntpdate_4.2.8p4+dfsg-3ubuntu5.9_amd64.deb"]
access_str = "310595054"


def sudo_run(cmd):
    p = subprocess.Popen(shlex.split("sudo -S %s" % cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate(access_str + "\n")


def run(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()


def install():
    # This is executed on the client to install the software
    for fname in pkg_list:
        print("== Starting to install %s ==" % fname)
        print(sudo_run("apt install -y %s" % (os.path.join("/tmp", fname)))[0])
    print("== After installing packages ==")
    print(sudo_run("timedatectl set-ntp off")[0])
    print(sudo_run("cp /tmp/ntp.conf /etc/ntp.conf")[0])
    print(sudo_run("service ntp restart")[0])
    print("== After restarting ntp service ==")
    time.sleep(5.0)
    print("== Running ntpq ==")
    print(run("ntpq -np")[0])


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
            with open("/tmp/ntp.conf", "w") as fp:
                fp.write("server %s prefer iburst\n" % server_address)

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(client_address, username="picarro", password=access_str)

            # Check the operating system version on the client
            print("== Requesting client OS version ==")
            stdout = client.exec_command("lsb_release -a")[1]
            for line in stdout:
                line = line.rstrip()
                print(line)
                if line.startswith("Release"):
                    _, rel = line.split()
            if rel.strip() != "16.04":
                print("Operating system version is incorrect (should be 16.04)")
                sys.exit(-1)

            sftp = client.open_sftp()
            # Use secure FTP to copy this script to the client
            sftp.put(__file__, "/tmp/myscript.py")

            # Copy the generated ntp.conf file to the client
            sftp.put("/tmp/ntp.conf", "/tmp/ntp.conf")

            # Copy the required .deb packages to the client
            for fname in pkg_list:
                sftp.put(os.path.join(my_path, fname), os.path.join("/tmp", fname))
            sftp.close()

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

    print("""Usage:

    python setup_client.py deploy ip-addr

    This is run on the rack server to set up NTP time-synchronization software on the analyzer client 
    at ip-addr.
    
    Note: The analyzer client should be running Ubuntu 16.04 LTS software.
    """)
