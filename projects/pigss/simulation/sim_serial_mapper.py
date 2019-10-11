#!/usr/bin/env python3
"""
Replaces SerialMapper class for madmapper when the system is run in simulation mode.
"""
import json
import os

config_path = [
    os.getenv("PIGSS_CONFIG"),
    os.path.join(os.getenv("HOME"), ".config", "pigss"),
    os.path.dirname(os.path.abspath(__file__))
]
config_path = [p for p in config_path if p is not None and os.path.exists(p) and os.path.isdir(p)]


class SimSerialMapper:
    """This currently just returns the data from the file sim_serial_map.json"""
    def get_usb_serial_devices(self):
        found = False
        for p in config_path:
            filename = os.path.normpath(os.path.join(p, "sim_serial_map.json"))
            if os.path.exists(filename):
                found = True
                break
        if found:
            with open(filename, "r") as fp:
                mapper_dict = json.load(fp)
                return {"Serial_Devices": mapper_dict["Devices"]["Serial_Devices"]}
        else:
            raise FileNotFoundError("Cannot find configuration file sim_serial_map.json")
