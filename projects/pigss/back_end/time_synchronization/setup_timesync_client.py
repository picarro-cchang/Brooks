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

import paramiko
from netifaces import AF_INET, ifaddresses, interfaces

from back_end.lologger.lologger_client import LOLoggerClient
from back_end.time_synchronization import setup_client # noqa - for packaging purposes

log = LOLoggerClient(client_name="SetupTimeSyncClient", verbose=True)
my_path = os.path.dirname(os.path.abspath(__file__))


async def time_sync_analyzers(analyzer_ips):
    netmask = 24  # This defines what it means for the analyzer and rack server to be on the same network
    access_str = os.environ.get('PIGSS_CLIENT_ACCESS')
    for ip in analyzer_ips:
        client_address = ip
        client = int.from_bytes(ipaddress.IPv4Address(client_address).packed, 'big')
        ip_addresses = []
        # Find the IP address of the time server by iterating through the IP addresses on its
        #  network interfaces and finding one which is on the same subnet as the client
        for ifname in interfaces():
            addresses = ifaddresses(ifname)
            if AF_INET in addresses:
                ip_addresses.append((ifname, addresses[AF_INET][0]['addr']))
        for ifname, ifaddr in ip_addresses:
            server = int.from_bytes(ipaddress.IPv4Address(ifaddr).packed, 'big')
            if (client ^ server) < (1 << (32 - netmask)):
                server_address = ifaddr
                break
        else:
            raise ValueError("Cannot find server for %s within network with netmask %d" % (client_address, netmask))

        # Set up the configuration file for ntp on the client
        tmp_config_path = os.path.join("/tmp", "timesyncd.conf")
        with open(tmp_config_path, "w") as fp:
            fp.write("[Time]\n")
            fp.write("NTP=%s\n" % server_address)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(client_address, username="picarro", password=access_str)
        sftp = client.open_sftp()
        # Use secure FTP to copy the setup script to the client
        script_filename = "setup_client.py"
        script_path = os.path.join("/usr", "local", "share", "picarro", script_filename)
        tmp_script_path = os.path.join("/tmp", script_filename)
        if not os.path.exists(script_path):
            script_path = os.path.join(my_path, script_filename)
        sftp.put(script_path, tmp_script_path)
        # Copy the generated timesyncd.conf file to the client
        sftp.put(tmp_config_path, tmp_config_path)

        print("\n\nCopying script to client and starting execution...")
        # Execute the script on the client and record the results
        stdout = client.exec_command(f"export PIGSS_CLIENT_ACCESS={access_str} && python {tmp_script_path}")[1]
        result = "\n".join([line.rstrip() for line in stdout])
        log.info(f"TimeSyncClient {ip} stdout: {result}")
        client.close()
