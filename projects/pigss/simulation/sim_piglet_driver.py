#!/usr/bin/env python3
"""
Replaces PigletDriver class when the system is run in simulation mode.
"""
import argparse
from threading import Thread

from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QApplication, QDialog, QGridLayout, QLabel

from common import CmdFIFO
from common.async_helper import SyncWrapper
from common.rpc_ports import rpc_ports
from common.timeutils import get_local_timestamp
from simulation.piglet_simulator import PigletSimulator


class SimPigletDriver(object):
    """
    This class currently is based on the Boxer firmware for the piglets described in
        https://github.com/picarro/I2000-Host/tree/develop-boxer/experiments/firmware/pigss/boxer
    """

    def __init__(self, port, rpc_port, baudrate=38400, carriage_return='\r', bank=1, random_ids=False, enable_ui=True):
        self.serial = None
        self.terminate = False
        self.port = port
        self.baudrate = baudrate
        self.carriage_return = carriage_return
        self.id_string = None
        self.rpc_port = rpc_port
        self.rpc_server = CmdFIFO.CmdFIFOServer(("", self.rpc_port),
                                                ServerName=__class__.__name__,
                                                ServerDescription=f'RPC Server for {__class__.__name__}',
                                                ServerVersion=1.0,
                                                threaded=True)
        self.piglet_simulator = SyncWrapper(PigletSimulator, bank=bank, random_ids=random_ids).wrap(['cli'])
        self.piglet_simulator.random_ids = random_ids
        self.connect()
        self.register_rpc_functions()
        if enable_ui:
            Thread(target=self.serve_forever, daemon=True).start()
            self.simple_ui()
        else:
            self.rpc_server.serve_forever()

    def serve_forever(self):
        """
            Call serve_forever method of rpc_server. It is called automatically by __init__
            NOTE: This should not be renamed to rpc_serve_forever since that name is reserved
                for a method that the user has to call, if the driver is written in such a
                way that the RPC server loop has to be run manually after calling __init__
        """
        self.rpc_server.serve_forever()
        self.ui_root.close()

    def simple_ui(self):
        """
            Generates a simple user interface showing the state of the simulated hardware
        """
        piglet = self.piglet_simulator.raw_access()
        app = QApplication([])
        self.ui_root = QDialog()
        self.ui_root.setWindowTitle(f"Piglet")
        self.ui_root.setStyleSheet("QLabel {font: 10pt Helvetica}")
        layout = QGridLayout()
        layout.addWidget(QLabel("Port:", self.ui_root), 0, 0)
        layout.addWidget(QLabel(f"{self.rpc_port}", self.ui_root), 0, 1)
        layout.addWidget(QLabel("Bank:", self.ui_root), 1, 0)
        layout.addWidget(QLabel(f"{piglet.bank}", self.ui_root), 1, 1)
        layout.addWidget(QLabel("Opstate:", self.ui_root), 2, 0)
        self.opstate_label = QLabel(f"{piglet.opstate}", self.ui_root)
        layout.addWidget(self.opstate_label, 2, 1)
        layout.addWidget(QLabel("MFC value:", self.ui_root), 3, 0)
        self.mfc_value_label = QLabel(f"{piglet.mfc_value:.2f}", self.ui_root)
        layout.addWidget(self.mfc_value_label, 3, 1)
        layout.addWidget(QLabel("Clean:", self.ui_root), 4, 0)
        self.clean_solenoid_state_label = QLabel(f"{piglet.clean_solenoid_state}", self.ui_root)
        layout.addWidget(self.clean_solenoid_state_label, 4, 1)
        layout.addWidget(QLabel("Solenoids:", self.ui_root), 5, 0)
        self.solenoid_state_label = QLabel(f"{piglet.solenoid_state}", self.ui_root)
        layout.addWidget(self.solenoid_state_label, 5, 1)
        self.ui_root.setLayout(layout)
        self.ui_root.setFixedSize(self.ui_root.sizeHint())
        self.ui_root.show()
        timer = QTimer(self.ui_root)
        timer.setSingleShot(False)
        timer.timeout.connect(self.update_ui)
        timer.start(200)
        app.exec_()
        self.rpc_server.stop_server()

    def update_ui(self):
        piglet = self.piglet_simulator.raw_access()
        self.opstate_label.setText(f"{piglet.opstate}")
        self.mfc_value_label.setText(f"{piglet.mfc_value:.2f}")
        self.clean_solenoid_state_label.setText(f"{piglet.clean_solenoid_state}")
        self.solenoid_state_label.setText(f"{piglet.solenoid_state}")

    def connect(self):
        """
        This function will attempt to connect to the serial port
        defined when the PigletDriver is instantiated.

        :return:
        """
        pass

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
        return self.piglet_simulator.cli(command + self.carriage_return)

    def close(self):
        """
        This function will close the serial connection if it is open.

        :return:
        """
        pass

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
            return not (int(number) >> 16)
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
        This function will set the operating state

        :param new_state:
        :return:
        """
        new_state = self.send(f'opstate {new_state}')
        return new_state

    def get_channel_status(self, channel):
        """
        This function will get the status of provided channel.
        It accepts integers 1-8. If it is active, it will return True.
        If it is not active, it will return False. On error it will
        return the code sent back by the piglet

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
        It returns the status code returned by the piglet.

        :param channel_to_enable:
        :return:
        """
        channel_to_enable = self.send(f'chanena {channel_to_enable}')
        return channel_to_enable

    def disable_channel(self, channel_to_disable):
        """
        This function will disable the provided channel. It accepts integers 1-8.
        It returns the status code returned by the piglet.

        :param channel_to_disable:
        :return:
        """
        channel_to_disable = self.send(f'chanoff {channel_to_disable}')
        return channel_to_disable

    def set_channel_registers(self, channels):
        """
        This function will accept integers 0-255, representing the bits
        of the channels you would like to enable.
        It returns the status code returned by the piglet.

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
    parser.add_argument('-p', '--piglet_port', help='Piglet port', default='/dev/ttyACM0')
    parser.add_argument('-b', '--baudrate', help='Piglet baudrate', default=38400)
    parser.add_argument('-r', '--rpc_port', help='Piglet RPC Port', default=rpc_ports.get('piglet_drivers'))
    args = parser.parse_args()
    return args


def main():
    cli_args = get_cli_args()
    port = cli_args.piglet_port
    baudrate = cli_args.baudrate
    rpc_port = cli_args.rpc_port
    # Instantiate the object and serve the RPC Port forever
    SimPigletDriver(port=port, baudrate=baudrate, rpc_port=int(rpc_port))


if __name__ == '__main__':
    import sys
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
