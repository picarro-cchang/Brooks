import os
import json
from host.experiments.madmapper.network.networkmapper import NetworkMapper
from host.experiments.madmapper.usb.serialmapper import SerialMapper
from host.experiments.common.rpc_ports import rpc_ports
from host.experiments.testing.cmd_fifo import CmdFIFO
from host.experiments.LOLogger.LOLoggerClient import LOLoggerClient


class MadMapper(object):
    """
    TODO - Docstring
    """
    def __init__(self):
        self.device_dict = {'Name': f'{__class__.__name__}', 'Devices': {}}
        self.networkmapper = NetworkMapper()
        self.serialmapper = SerialMapper()
        self.path = os.path.join(os.getenv('HOME'), '.config/picarro')
        self.file_name = 'madmapper.json'
        self.rpc_port = rpc_ports.get('madmapper')
        self.rpc_server = CmdFIFO.CmdFIFOServer(
            ("", self.rpc_port),
            ServerName=__class__.__name__,
            ServerDescription=f'RPC Server for {__class__.__name__}',
            ServerVersion=1.0,
            threaded=True
        )
        self.logger = LOLoggerClient(client_name=__class__.__name__)
        self.logger.debug(f'Started')
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
        self.logger.debug(f'Devices found: \n{json.dumps(self.device_dict, indent=2)}')
        if should_write is True:
            self._write_json(self.device_dict)
        return self.device_dict

    def _write_json(self, obj=None):
        """
        TODO - Docstring
        """
        try:
            if not os.path.isdir(self.path):
                self.logger.debug(f'Making directory: {self.path}')
                os.mkdir(self.path, mode=0o755)
            with open(os.path.join(self.path, self.file_name), 'w') as f:
                self.logger.debug(f'Writing to '
                                  f'{os.path.join(self.path, self.file_name)}:\n'
                                  f'{json.dumps(obj, indent=2)}')
                f.write(f'{json.dumps(obj, indent=2)}\n')
        except Exception as e:
            self.logger.critical(f'Unhandled Exception: {e}')
            raise

    def read_json(self):
        """
        TODO - Docstring
        """
        json_path = os.path.join(self.path, self.file_name)
        try:
            with open(json_path, 'r') as f:
                json_contents = json.load(f)
                self.logger.debug(f'Reading from {json_path}: \n{json.dumps(json_contents, indent=2)}')
                return json_contents
        except FileNotFoundError:
            self.logger.warning(f'File does not exist: {json_path}')
        except Exception as e:
            self.logger.critical(f'Unhandled Exception: {e}')
            raise


    def register_rpc_functions(self):
        self.logger.debug(f'Registering RPC Functions')
        self.rpc_server.register_function(self.map_devices)
        self.rpc_server.register_function(self.read_json)


def main():
    if __debug__:
        print(f'Starting MadMapper on port {rpc_ports.get("madmapper")}')
    MadMapper()

if __name__ == '__main__':
    import sys
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
