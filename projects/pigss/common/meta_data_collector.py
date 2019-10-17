"""
    A module to collect a metadata from the system
"""
import os
import shutil
import psutil
import subprocess
import requests

REST_API_PORT = 8000  # this port is being hardcoded since there is no proper way to import it at this moment
SUPERVISOR_ADDRESS = f"http://localhost:{REST_API_PORT}"
DEVICE_MAP_PATH = f"{SUPERVISOR_ADDRESS}/supervisor/device_map"


def get_metadata_ready_for_db(pkg_meta=None):
    """ Prepare metadata for database. """
    metadata = collect_metadata(pkg_meta)
    metadata_tpl = [(k, metadata[k]) for k in metadata]
    return metadata_tpl


def collect_metadata(pkg_meta=None):
    """
        Method to collect metadata:
        - package versions specified in pkg_meta argument
        - os metadata
        - pigss device map
        - disk usage
        - system time related stuff
    """
    meta_dict = {}

    # package versions
    if pkg_meta is not None:
        for pkg in pkg_meta:
            meta_dict[f"pkg_{pkg}"] = get_pkg_verions(pkg)

    # system meta
    sysname, nodename, release, version, machine = os.uname()
    meta_dict["system_sysname"] = sysname
    meta_dict["system_nodename"] = nodename
    meta_dict["system_release"] = release
    meta_dict["system_version"] = version
    meta_dict["system_machine"] = machine

    # rest api request to device_map
    try:
        responce = requests.get(DEVICE_MAP_PATH)
        if responce.status_code == 200:
            meta_dict["device_map"] = responce.text
    except requests.exceptions.ConnectionError:
        # server is not responding, don't add "device_map" key to dictionary
        pass

    # disk usage
    for partition in psutil.disk_partitions():
        total, used, free = shutil.disk_usage(partition.mountpoint)
        meta_dict[f"partitions_{partition.mountpoint}"] = f"total_{total}_used_{used}_free_{free}"

    # uptime
    meta_dict["boot_time"] = psutil.boot_time()

    # timezone
    meta_dict["time_zone"] = get_time_zone()

    # last reboot
    meta_dict["last_reboot"] = get_last_reboot_time()
    return meta_dict


def get_time_zone():
    line = _run_command(command=["timedatectl"], line_trigger="Time zone: ")
    if line is not None:
        return line[line.find(":") + 2:]
    return None


def get_last_reboot_time():
    return _run_command(command=["last", "reboot"], line_trigger="still running")


def get_pkg_verions(pkg):
    line_trigger = "Version: "
    line = _run_command(command=["dpkg", "-s", pkg], line_trigger=line_trigger)
    if line is not None:
        return line.replace(line_trigger, "")
    return None


def _run_command(command, line_trigger):
    """
        A method to run a command as subprocess and return
        line from stdout that contains line_trigger
    """
    try:
        output = subprocess.check_output(command, universal_newlines=True)
    except subprocess.CalledProcessError:
        return None
    # search for trigger in the line
    for line in output.splitlines():
        if line_trigger in line:
            return line
    return None
