import json
import os

my_path = os.path.dirname(os.path.abspath(__file__))


class SimSerialMapper:
    def get_usb_serial_devices(self):
        with open(os.path.join(my_path, "sim_serial_map.json"), "r") as fp:
            mapper_dict = json.load(fp)
            return {"Serial_Devices": mapper_dict["Devices"]["Serial_Devices"]}