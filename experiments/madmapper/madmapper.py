import os
import json
from host.experiments.madmapper.network.networkmapper import NetworkMapper
from host.experiments.madmapper.usb.serialmapper import SerialMapper


class MadMapper(object):
    def __init__(self):
        self.device_dict = {'Name': f'{__class__.__name__}', 'Devices': {}}
        self.networkmapper = NetworkMapper()
        self.serialmapper = SerialMapper()
        self.path = f'{os.getenv("HOME")}/.config/picarro'
        self.file_name = 'madmapper.json'

    def map_devices(self):
        network_devices = self.networkmapper.get_all_picarro_hosts()
        serial_devices = self.serialmapper.get_usb_serial_devices()
        self.device_dict['Devices'].update(network_devices)
        self.device_dict['Devices'].update(serial_devices)
        if __debug__:
            print(json.dumps(self.device_dict, indent=2))
        return self.device_dict

    def write_json(self, obj):
        try:
            if not os.path.isdir(self.path):
                if __debug__:
                    print(f'Making directory: {self.path}')
                os.mkdir(self.path, mode=0o755)
            with open(f'{self.path}/{self.file_name}', "w") as f:
                f.write(f'{json.dumps(obj, indent=2)}\n')
        except Exception as e:
            if __debug__:
                print(f'Exception: e')
            raise


if __name__ == '__main__':
    from host.experiments.common.function_timer import FunctionTimer
    with FunctionTimer():
        test = MadMapper()
        devices = test.map_devices()
        test.write_json(devices)
