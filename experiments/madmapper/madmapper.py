import os
import json
from host.experiments.madmapper.network.networkmapper import NetworkMapper
from host.experiments.madmapper.usb.serialmapper import SerialMapper
from host.experiments.common.rpc_ports import rpc_ports
from host.experiments.madmapper.network import CmdFIFO


class MadMapper(object):
    """
    TODO - Docstring
    """
    def __init__(self):
        self.device_dict = {'Name': f'{__class__.__name__}', 'Devices': {}}
        self.networkmapper = NetworkMapper()
        self.serialmapper = SerialMapper()
        self.path = f'{os.getenv("HOME")}/.config/picarro'
        self.file_name = 'madmapper.json'
        self.rpc_port = rpc_ports.get('madmapper')
        self.rpc_server = CmdFIFO.CmdFIFOServer(
            ("", self.rpc_port),
            ServerName=__class__.__name__,
            ServerDescription=f'RPC Server for {__class__.__name__}',
            ServerVersion=1.0,
            threaded=True
        )
        self.register_rpc_functions()
        self.rpc_server.serve_forever()

    def map_devices(self, should_write=True):
        """
        TODO - Docstring
        """
        network_devices = self.networkmapper.get_all_picarro_hosts()
        serial_devices = self.serialmapper.get_usb_serial_devices()
        self.device_dict['Devices'].update(network_devices)
        self.device_dict['Devices'].update(serial_devices)
        if __debug__:
            print(json.dumps(self.device_dict, indent=2))
        if should_write is True:
            self._write_json(self.device_dict)
        return self.device_dict

    def _write_json(self, obj=None):
        """
        TODO - Docstring
        """
        try:
            if not os.path.isdir(self.path):
                if __debug__:
                    print(f'Making directory: {self.path}')
                os.mkdir(self.path, mode=0o755)
            with open(f'{self.path}/{self.file_name}', 'w') as f:
                f.write(f'{json.dumps(obj, indent=2)}\n')
        except Exception as e:
            if __debug__:
                print(f'Exception: {e}')
            raise

    def read_json(self):
        """
        TODO - Docstring
        """
        json_path = f'{self.path}/{self.file_name}'
        try:
            with open(json_path, 'r') as f:
                json_contents = json.load(f)
                if __debug__:
                    print(json.dumps(json_contents, indent=2))
                return json_contents
        except Exception as e:
            print(f'Exception: {e}')
            raise


    def register_rpc_functions(self):
        self.rpc_server.register_function(self.map_devices)
        self.rpc_server.register_function(self.read_json)


def main():
    if __debug__:
        print(f'Starting MadMapper on port: {rpc_ports.get("madmapper")}')
    MadMapper()

if __name__ == '__main__':
    import sys
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
