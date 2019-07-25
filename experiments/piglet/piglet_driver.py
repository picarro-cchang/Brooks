import serial
import time
import argparse
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.common.timeutils import get_local_timestamp
from host.experiments.common.rpc_ports import rpc_ports

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
    def __init__(self, port, rpc_port, baudrate=38400, carriage_return='\r'):
        self.serial = None
        self.terminate = False
        self.port = port
        self.baudrate = baudrate
        self.carriage_return = carriage_return
        self.id_string = None
        self.rpc_port = rpc_port
        self.rpc_server = CmdFIFO.CmdFIFOServer(
            ("", self.rpc_port),
            ServerName=__class__.__name__,
            ServerDescription=f'RPC Server for {__class__.__name__}',
            ServerVersion=1.0,
            threaded=True
        )
        self.connect()
        self.register_rpc_functions()
        self.rpc_server.serve_forever()

    def connect(self):
        """
        This function will attempt to connect to the serial port
        defined when the PigletDriver is instantiated.

        :return:
        """
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
        """
        This function will send a command to the Piglet and return its response.

        Error responses:
            -1: Command not recognized
            -2: Piglet is busy

        In the event of a command not recognized, we will return -1 and move along.

        In the event of the Piglet being busy, we will sleep for 10 ms and attempt to
        read the response 10 times, for a total of 100 ms. If successful, we will return
        the response. If not successful, we will return -2

        :param command:
        :return:
        """
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
        if __debug__:
            print(f'Command sent: {command}\nResponse received: {response}')
        return response.replace('\n', '')

    def close(self):
        """
        This function will close the serial connection if it is open.

        :return:
        """
        if self.serial is not None:
            self.serial.close()

    def get_id_string(self):
        """
        This function will get a comma delimited identification
        string from the Piglet.

        Identification String Example:
            Picarro,Boxer,SN65000,1.0.2

        Element IDs:
            0: Manufacturer Name
            1: Model Number
            2: Serial Number
            3: Firmware Revision

        :return:
        """
        self.id_string = self.send('*idn?')
        return self.id_string

    def get_manufacturer(self):
        """
        This function will return the first element from the
        id_string as the manufacturer.

        :return:
        """
        if self.id_string is None:
            self.get_id_string()
        manufacturer = self.id_string.split(',')[0]
        return manufacturer

    def get_model_number(self):
        """
        This function will return the second element from the
        id_string as the model number.

        :return:
        """
        if self.id_string is None:
            self.get_id_string()
        model_number = self.id_string.split(',')[1]
        return model_number

    def get_serial_number(self):
        """
        This function will return the third element from the
        id_string as the serial number.

        :return:
        """
        if self.id_string is None:
            self.get_id_string()
        serial_number = self.id_string.split(',')[2]
        return serial_number

    def get_firmware_revision(self):
        """
        This function will return the fourth element from the
        id_string as the firmware version.

        :return:
        """
        if self.id_string is None:
            self.get_id_string()
        firmware_version = self.id_string.split(',')[3]
        return firmware_version

    def reset_piglet(self):
        """
        This function will initiate a system reset.

        :return:
        """
        self.send('*rst')
        return '0'

    @staticmethod
    def _is_int16(number):
        """
        This is a static method to check whether a number is
        and unsigned 16 bit integer. It is a helper function
        for the set_serial_number function.

        :param number:
        :return:
        """
        try:
            return not(int(number) >> 16)
        except ValueError:
            return False

    def set_serial_number(self, new_sn):
        """
        This function will accept an unsigned 16 bit int. If it is not
        a 16 bit int, the function will return -1. Otherwise, it will set
        the Piglet Serial Number and return 0.

        :param new_sn:
        :return:
        """
        try:
            new_sn = int(new_sn)
            if self._is_int16(new_sn):
                set_new_sn = self.send(f'sernum {new_sn}')
                # Reset self.id_string so when we query it,
                # we get the new serial number.
                self.id_string = None
                return set_new_sn
            else:
                return -1
        except ValueError:
            return -1

    def get_slot_id(self):
        """
        This function will query and return the Slot ID of the Piglet

        :return:
        """
        slot_id = self.send('slotid?')
        return slot_id

    def set_slot_id(self, new_slot_id):
        """
        This function will accept the integers 0-9. It will then
        set the Slot ID of the Piglet. If unsuccessful--or an invalid value is passed
        it will return -1.

        :param new_slot_id:
        :return:
        """
        try:
            new_slot_id = int(new_slot_id)
            new_slot_id = self.send(f'slotid {new_slot_id}')
            return new_slot_id
        except ValueError:
            return -1

    def get_operating_state(self):
        """
        This function will return the current state of the
        Piglet.

        :return:
        """
        current_state = self.send('opstate?')
        return current_state

    def set_operating_state(self, new_state):
        """
        This function is reserved for future use. It should
        return a -1 for now.

        :param new_state:
        :return:
        """
        new_state = self.send(f'opstate {new_state}')
        return new_state

    def get_channel_status(self, channel):
        """
        This function will get the status of provided channel.
        It accepts integers 1-8. If it is active, it will return True.
        If it is not active, it will return False. If an invalid channel
        is provided it will return -1.

        :param channel:
        :return:
        """
        channel_status = self.send(f'chanena? {channel}')
        if channel_status == '1':
            return True
        elif channel_status == '0':
            return False
        else:
            return channel_status

    def enable_channel(self, channel_to_enable):
        """
        This function will enable the provided channel. It accepts integers 1-8.
        If successful, it will return a 0. If an invalid channel is provided
        it will return -1.

        :param channel_to_enable:
        :return:
        """
        channel_to_enable = self.send(f'chanena {channel_to_enable}')
        return channel_to_enable

    def disable_channel(self, channel_to_disable):
        """
        This function will disable the provided channel. It accepts integers 1-8.
        If successful, it will return a 0. If an invalid channel is provided it
        will return -1.

        :param channel_to_disable:
        :return:
        """
        channel_to_disable = self.send(f'chanoff {channel_to_disable}')
        return channel_to_disable

    def set_channel_registers(self, channels):
        """
        This function will accept integers 0-255, representing the bits
        of the channels you would like to enable. If successful, it will
        return 0. If in invalid setting is provided it will return -1.

        :param channels:
        :return:
        """
        channels = self.send(f'chanset {channels}')
        return channels

    def get_channel_registers(self):
        """
        This function will return 0-255 indicating what channels
        are enabled.

        :return:
        """
        channel_registers = self.send('chanset?')
        return channel_registers

    @staticmethod
    def get_timestamp():
        """
        This function will return a local timestamp in ISO 8601 format.

        :return:
        """
        timestamp = get_local_timestamp()
        return timestamp

    def register_rpc_functions(self):
        self.rpc_server.register_function(self.send)
        self.rpc_server.register_function(self.connect)
        self.rpc_server.register_function(self.close)
        self.rpc_server.register_function(self.get_id_string)
        self.rpc_server.register_function(self.get_manufacturer)
        self.rpc_server.register_function(self.get_model_number)
        self.rpc_server.register_function(self.get_serial_number)
        self.rpc_server.register_function(self.get_firmware_revision)
        self.rpc_server.register_function(self.reset_piglet)
        self.rpc_server.register_function(self.set_serial_number)
        self.rpc_server.register_function(self.get_slot_id)
        self.rpc_server.register_function(self.set_slot_id)
        self.rpc_server.register_function(self.get_operating_state)
        self.rpc_server.register_function(self.set_operating_state)
        self.rpc_server.register_function(self.get_channel_status)
        self.rpc_server.register_function(self.enable_channel)
        self.rpc_server.register_function(self.disable_channel)
        self.rpc_server.register_function(self.set_channel_registers)
        self.rpc_server.register_function(self.get_channel_registers)
        self.rpc_server.register_function(self.get_timestamp)


def get_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--piglet-port', help='Piglet port')
    parser.add_argument('-b', '--baudrate', help='Piglet baudrate')
    parser.add_argument('-r', '--rpc-port', help='Piglet RPC Port')
    args = parser.parse_args()
    return args


def main():
    cli_args = get_cli_args()
    # Get the Piglet Port from the CLI
    if cli_args.piglet_port:
        port = cli_args.piglet_port
    else:
        port = '/dev/ttyACM0'
    if __debug__:
        print(f'Piglet Port: {port}')
    # Get the Piglet baudrate from the CLI
    if cli_args.baudrate:
        baudrate = cli_args.baudrate
    else:
        baudrate = 38400
    if __debug__:
        print(f'Piglet baudrate: {baudrate}')
    if cli_args.rpc_port:
        rpc_port = cli_args.rpc_port
    else:
        rpc_port = rpc_ports.get('piglet_drivers')
    if __debug__:
        print(f'Piglet RPC Port: {rpc_port}')
    # Instantiate the object and serve the RPC Port forever
    PigletDriver(port=port, baudrate=baudrate, rpc_port=int(rpc_port))
    if __debug__:
        print('PigletDriver stopped.')


if __name__ == '__main__':
    import sys
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
