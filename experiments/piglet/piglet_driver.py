import serial
import time
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.common.timeutils import get_local_timestamp

# TODO
#   Remove local import for CmdFIFO
#   Remove hardcoded host
#   Remove hardcoded port
import CmdFIFO


class PigletDriver(object):
    """
    This class currently covers the Boxer firmware for the
    Piglet OFF (Arduino).
        https://github.com/picarro/I2000-Host/tree/develop-boxer/experiments/firmware/pigss/boxer
    """
    def __init__(self, port, baudrate=38400, carriage_return='\r'):
        self.serial = None
        self.terminate = False
        self.port = port
        self.baudrate = baudrate
        self.carriage_return = carriage_return
        self.rpc_server = CmdFIFO.CmdFIFOServer(
            ("", 6669),
            ServerName=__class__.__name__,
            ServerDescription=f'RPC Server for {__class__.__name__}',
            ServerVersion=1.0,
            threaded=True
        )
        self.connect()
        self.register_rpc_functions()
        # self.rpc_server.serve_forever()

    def connect(self):
        try:
            self.serial = SerialInterface()
            self.serial.config(port=self.port, baudrate=self.baudrate)
            if __debug__:
                print(f'\nConnecting to Piglet on {self.port}\n')
            # The Piglet boot loader takes a little less to load. Every time
            # the DTR is toggled, the Piglet will re-set. The DTR is toggled
            # upon enumeration from the Linux Kernel as well as every time
            # we connect to the device. We'll sleep for a few seconds to
            # allow the device to reset. At this time, we cannot disable
            # the re-set functionality as we'll rely on this for flashing
            # firmware to the device.
            time.sleep(2)
        except serial.SerialException:
            raise

    def send(self, command):
        self.serial.write(command + self.carriage_return)
        time.sleep(0.2)
        response = self.serial.read()
        if '-1' in response:
            # Piglet doesn't recognize the command
            if __debug__:
                print(f'Command not recognized: {command}')
        elif '-2' in response:
            # Piglet is busy and cannot respond
            if __debug__:
                print('Piglet is busy...')
            for attempt in range(1, 11):
                time.sleep(0.01)
                if __debug__:
                    print(f'Attempt {attempt} to wait on Piglet...')
                response = self.serial.read()
                if '-2' not in response:
                    break
        return response

    def close(self):
        if self.serial is not None:
            self.serial.close()

    def register_rpc_functions(self):
        self.rpc_server.register_function(self.send)
        self.rpc_server.register_function(self.connect)
        self.rpc_server.register_function(self.close)


if __name__ == '__main__':
    obj = PigletDriver(port='/dev/ttyACM0')
    obj.rpc_server.serve_forever()
    # print(obj.send('*rst'))
    # print(obj.send('*idn?'))
    obj.close()
