# Set up network namespaces on a virtual machine to allow multiple IP addresses to exist within a single host
#  and for these to be associated with different processes, thus allowing a multiplicity of simulators to run with
#  the same network port assignments but on different IP addresses

import asyncio
import ipaddress
import json
import os
import subprocess
import attr

from netifaces import AF_INET, gateways, ifaddresses, interfaces

from run_in_shell import ShellRunner


@attr.s
class Analyzer:
    chassis = attr.ib(type=str)
    analyzer = attr.ib(type=str)
    analyzer_num = attr.ib(type=str)
    species = attr.ib()
    source = attr.ib(type=str)
    mode = attr.ib(type=str)
    interval = attr.ib(type=float)


analyzers = [
    Analyzer('4123', 'AMADS', '3001', ['NH3', 'HF'], 'analyze_AMADS_LCT', 'AMADS_LCT_mode', 1.1),
    Analyzer('4357', 'SBDS', '3002', ['HCl'], 'analyze_SADS', 'HCl_mode', 1.2),
    Analyzer('4532', 'BFADS', '3003', ['H2S'], 'analyze_BFADS', 'BFADS_mode', 1.3)
]


async def setup_sim(name, analyzer):
    client = ShellRunner("/bin/bash")
    await client.sendline(f"sudo ip netns exec {name} bash")
    await client.sendline(f"su picarro")
    await client.sendline(f'eval "$(~/miniconda3/condabin/conda shell.bash hook)"')
    await client.sendline(f'export PYTHONPATH=/home/picarro/git:/home/picarro/git/host')
    await client.sendline(f"conda activate pigss")
    await client.sendline(f"python mysim.py {name} '{json.dumps(attr.asdict(analyzer))}' &")
    await client.expect("Done")


async def create_netns(name):
    async with ShellRunner("/bin/bash") as client:
        print(f"Creating namespace for interface {name}")
        await client.sendline(f"sudo ip netns add {name}")
        await client.sendline(f"sudo ip link set {name} netns {name}")
        await client.sendline(f"sudo ip netns exec {name} ip link set {name} up")
        await client.sendline(f"sudo ip netns exec {name} dhclient {name}")
        await client.sendline(f"sudo ip netns exec {name} ifconfig lo 127.0.0.1 netmask 255.0.0.0 up")
        await client.sendline(f"echo Done")
        await client.expect("Done\n")


async def remove_netns(name):
    async with ShellRunner("/bin/bash") as client:
        await client.sendline(f"sudo ip netns pids {name}")
        await client.sendline(f"echo Done")
        await client.expect("Done\n")
        pid = [line.strip() for line in client.before.splitlines() if line][0]
        print(f"Killing {pid}")
        await client.sendline(f"sudo kill {pid}")
        await client.sendline(f"sudo ip netns del {name}")


async def list_netns():
    async with ShellRunner("/bin/bash") as client:
        await client.sendline(f"sudo ip netns list")
        await client.sendline(f"echo Done")
        await client.expect("Done\n")
        return [line.split()[0] for line in client.before.splitlines() if line]


def is_host_interface(name):
    # Determine if one of the IP addresses associated with interface "name" lies
    #  within the IP range for host interfaces
    ip_low = ipaddress.IPv4Address('192.168.10.101')
    ip_high = ipaddress.IPv4Address('192.168.10.254')

    # Find interface names belonging to the host-only network
    for x in ifaddresses(name)[AF_INET]:
        ip = ipaddress.IPv4Address(x['addr'])
        if ip_low <= ip <= ip_high:
            return True
    return False


async def main():
    os.system("sudo echo OK")
    for name in interfaces():
        print(f"Processing {name}")
        if is_host_interface(name):
            await create_netns(name)
            print(f"Created namespace {name}")

    # for name in await list_netns():
    #     await remove_netns(name)
    #     print(f"Removed namespace {name}")

    for i, name in enumerate(await list_netns()):
        print(f"Running simulator on {name}")
        await setup_sim(name, analyzers[i])

    while True:
        await asyncio.sleep(1.0)


# os.system("sudo ip netns list")
# print(interfaces())

# ip_low = ipaddress.IPv4Address('192.168.56.101')
# ip_high = ipaddress.IPv4Address('192.168.56.254')

# # Find interface names belonging to the host-only network
# names = set()
# for ifname in interfaces():
#     for x in ifaddresses(ifname)[AF_INET]:
#         ip = ipaddress.IPv4Address(x['addr'])
#         if ip_low <= ip <= ip_high:
#             names.add(ifname)

# # Use these names as namespaces for the network
# for name in names:
#     print(f"Processing interface {name}")
#     os.system(f"sudo ip netns add {name}")
#     os.system(f"sudo ip link set {name} netns {name}")
#     os.system(f"sudo ip netns exec {name} ip link set {name} up")
#     os.system(f"sudo ip netns exec {name} dhclient {name}")
#     os.system(f"sudo ip netns exec {name} ifconfig lo 127.0.0.1 netmask 255.0.0.0 up")

# os.system("sudo ip netns list")

asyncio.run(main())
