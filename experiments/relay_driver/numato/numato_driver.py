import serial
import time
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.common.timeutils import get_local_timestamp

# TODO
#   Remove local import for CmdFIFO
#   Remove hardcoded host
#   Remove hardcoded port
import CmdFIFO

class NumatoDriver(object):
    """
    This class is for the Numato 4 Channel USB Relay Module
        https://numato.com/product/4-channel-usb-relay-module
    """
    def __init__(self,
                 port,
                 baudrate=192000,
                 relay_count=4,
                 gpio_count=4,
                 carriage_return='\r'):
        self.serial = None
        self.terminate = False
        self.port = port
        self.baudrate = baudrate
        self.carriage_return = carriage_return
        self.relay_count = relay_count
        self.gpio_count = gpio_count
        self.gpio_modes = []
        self.gpio_output_status = []
        self.rpc_server = CmdFIFO.CmdFIFOServer(
            ("", 6668),
            ServerName=__class__.__name__,
            ServerDescription=f"RPC Server for {__class__.__name__}",
            ServerVersion=1.0,
            threaded=True
        )
        self.connect()
        self.register_rpc_functions()
        self.rpc_server.serve_forever()

    def connect(self):
        """
        This function opens the serial port defined when the
        class is instantiated.

        :return:
        """
        try:
            self.serial = SerialInterface()
            self.serial.config(port=self.port, baudrate=self.baudrate)
        except serial.SerialException:
            raise

    def send(self, command):
        self.serial.write(command + self.carriage_return)
        #self._wait_for_echo(command)
        time.sleep(0.2)
        response = self.serial.read()
        print(response)
        return response

    def _wait_for_echo(self, command):
        while self.serial.read().strip().replace('>', '') != command:
            print('sleeping')
            time.sleep(0.001)

    def close(self):
        if self.serial is not None:
            self.serial.close()

    def get_current_time(self):
        current_time = get_local_timestamp()
        return current_time

    def register_rpc_functions(self):
        self.rpc_server.register_function(self.send)
        self.rpc_server.register_function(self.get_current_time)


if __name__ == '__main__':
    obj = NumatoDriver(port='/dev/ttyACM1')
    """
    obj.send('ver')
    print()
    obj.send('id get')
    print()
    obj.send('relay on 0')
    print()
    obj.send('relay off 0')
    print()
    obj.send('relay read 0')
    print()
    obj.send('gpio read 0')
    print()
    obj.send('gpio clear 0')
    print()
    obj.send('gpio set 0')
    print()
    obj.send('adc read 0')
    print()
    """
