#!/usr/bin/env python3
#
# FILE:
#   sim_serial_mapper.py
#
# DESCRIPTION:
#   Replaces SerialMapper class for madmapper when the system is run in simulation mode.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze Initial check in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
import json
import os

my_path = os.path.dirname(os.path.abspath(__file__))


class SimSerialMapper:
    """This currently just returns the data from the file sim_serial_map.json"""
    def get_usb_serial_devices(self):
        with open(os.path.join(my_path, "sim_serial_map.json"), "r") as fp:
            mapper_dict = json.load(fp)
            return {"Serial_Devices": mapper_dict["Devices"]["Serial_Devices"]}
