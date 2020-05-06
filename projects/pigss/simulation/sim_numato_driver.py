#!/usr/bin/env python3
"""
    A module to control a Numato Lab’s 4 Channel USB Powered Relay Module.
    python numato_driver_proto.py "/dev/ttyACM1" 6668
"""
import time
from threading import Thread

from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel, QVBoxLayout)

import common.CmdFIFO as CmdFIFO
from back_end.lologger.lologger_client import LOLoggerClient
from common.rpc_ports import rpc_ports

GPIO_MODES = ["D_IN", "D_OUT", "A_IN"]


class UsbRelay:
    """A class to control a Numato USB relay module."""

    def __init__(self, port_name, relay_count=4, gpio_count=4, debug=False, logger=None):
        """Init function."""
        self.port_name = port_name
        self.debug = debug
        self.relay_count = relay_count
        self.gpio_count = gpio_count
        self.gpio_modes = []
        self.gpio_output_status = []
        self.serial_port = None  # Simulator has no serial port
        self.relay_states = relay_count * [False]
        self.board_id = "00000000"
        self.gpio_states = gpio_count * [False]
        self.init()  # Initialize gpio_modes and gpio_output_status

        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(client_name=f"{self.port_name}_NUMATO")

    def init(self):
        """
            Start by calling this method, it sets relays off and GPIO to Digital Out LOW.
        """
        # set all relays off
        for i in range(self.relay_count):
            self.set_relay(i, False)
        # set all gpio off
        for i in range(self.gpio_count):
            self.gpio_modes.append("D_OUT")
            self.gpio_output_status.append(False)
            self.set_gpio_status(i, False)

    def get_relay_status(self, relay_num):
        """
            Returns relay status as boolean.
            relay_num (int)
        """
        if relay_num >= self.relay_count:
            raise ValueError("relay_num is bigger than relay_count")
        return self.relay_states[relay_num]

    def set_relay(self, relay_num, status):
        """
            Sets relay on or off.
            relay_num (int)
            status (bool)
        """
        if relay_num >= self.relay_count:
            raise ValueError("relay_num is bigger than relay_count")
        self.relay_states[relay_num] = status

    def flip_relay(self, relay_num):
        """
            Flips relay to an opposite state from current
            relay_num (int)
        """
        self.set_relay(relay_num, not self.get_relay_status(relay_num))

    def set_id(self, new_id):
        """
            Sets device ID.
            new_id (string)
        """
        if len(new_id) != 8:
            raise ValueError("new id must be exactly 8 chars")
        self.board_id = new_id

    def get_id(self):
        """
            Returns device ID.
        """
        return self.board_id

    def do_disco(self, relay_num=0, times=8, delay=0.05):
        """
            Disco
        """
        for i in range(times):
            self.flip_relay(relay_num)
            time.sleep(delay)

    def do_full_disco(self, cycles):
        for k in range(cycles):
            self.logger.info(f"Cycle {k} in progress, {100*((k+1.)/cycles)}% done")
            for i in range(self.relay_count):
                self.do_disco(i)

    def __gpio_check(self, gpio_num, required_mode=None):
        """
            Checks if GPIO requested GPIO exists and is in the right state.
            gpio_num (int)
            required_mode [GPIO_MODES]
        """
        if gpio_num >= self.gpio_count:
            raise ValueError("gpio_num is bigger than gpio_count")
        if required_mode is not None:
            if self.gpio_modes[gpio_num] != required_mode:
                raise ValueError(f"current gpio mode is wrong, should be {required_mode}")

    def get_gpio_mode(self, gpio_num):
        """
            Returns current mode of the requested GPIO.
            gpio_num (int)
        """
        self.__gpio_check(gpio_num)
        return self.gpio_modes[gpio_num]

    def set_gpio_mode(self, gpio_num, mode):
        """
            Sets requested GPIO to a requested mocde.
            gpio_num (int)
            mode [GPIO_MODES]
        """
        self.__gpio_check(gpio_num)
        if mode not in GPIO_MODES:
            raise ValueError("mode not supported")
        if mode in ["D_IN", "A_IN"]:
            self.gpio_output_status[gpio_num] = False
        self.gpio_modes[gpio_num] = mode

    def set_gpio_status(self, gpio_num, status):
        """
            If GPIO is in D_OUT mode - sets it to HIGH or LOW.
            gpio_num (int)
            status (bool)
        """
        self.__gpio_check(gpio_num, required_mode="D_OUT")
        if not isinstance(status, bool):
            raise ValueError("status should be boolean")
        self.gpio_states[gpio_num] = status

    def get_gpio_status(self, gpio_num):
        """
            If GPIO is in D_OUT mode - returns it's status as bool, which has been previously set.
            gpio_num (int)
        """
        return self.gpio_states[gpio_num]

    def get_gpio_reading(self, gpio_num):
        """
            If GPIO is in D_IN mode - returns it's reading.
            gpio_num (int)
        """
        return self.gpio_states[gpio_num]

    def get_gpio_analog_reading(self, gpio_num):
        """
            If GPIO is in A_IN mode - returns it's reading.
            gpio_num (int)
        """
        return 0


class SimNumatoDriver(object):
    """
        This is an RPC wrapper for Numato Relay Driver
    """

    def __init__(self,
                 device_port_name,
                 rpc_server_port,
                 rpc_server_name="NumatoDriver",
                 rpc_server_description="Driver for Numato RelayBoard",
                 relay_count=4,
                 gpio_count=4,
                 debug=False,
                 logger=None,
                 enable_ui=True):

        self.device_port_name = device_port_name
        self.rpc_server_port = rpc_server_port
        self.rpc_server_name = rpc_server_name
        self.rpc_server_description = rpc_server_description
        self.relay_count = relay_count
        self.gpio_count = gpio_count

        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(client_name=f"RPC_NUMATO_{self.device_port_name}")

        self.ur = UsbRelay(port_name=self.device_port_name,
                           relay_count=self.relay_count,
                           gpio_count=self.gpio_count,
                           debug=debug,
                           logger=self.logger)

        self.server = CmdFIFO.CmdFIFOServer(("", self.rpc_server_port),
                                            ServerName=self.rpc_server_name,
                                            ServerDescription=self.rpc_server_description,
                                            threaded=True)

        self.register_numato_driver_rpc_functions()
        if enable_ui:
            Thread(target=self.serve_forever, daemon=True).start()
            self.simple_ui()
        else:
            self.server.serve_forever()

    def register_numato_driver_rpc_functions(self):
        """Register all public methods to the rpc server."""
        # disco functions, delete in production
        self.server.register_function(self.ur.do_full_disco, name="NUMATO_full_disco")
        self.server.register_function(self.ur.do_disco, name="NUMATO_do_disco")

        # relay functions
        self.server.register_function(self.ur.get_relay_status, name="NUMATO_get_relay_status")
        self.server.register_function(self.ur.set_relay, name="NUMATO_set_relay")
        self.server.register_function(self.ur.flip_relay, name="NUMATO_flip_relay")

        # board ID functions
        self.server.register_function(self.ur.set_id, name="NUMATO_set_id")
        self.server.register_function(self.ur.get_id, name="NUMATO_get_id")

        # gpio functions
        self.server.register_function(self.ur.get_gpio_mode, name="NUMATO_get_gpio_mode")
        self.server.register_function(self.ur.set_gpio_mode, name="NUMATO_set_gpio_mode")
        self.server.register_function(self.ur.set_gpio_status, name="NUMATO_set_gpio_status")
        self.server.register_function(self.ur.get_gpio_status, name="NUMATO_get_gpio_status")
        self.server.register_function(self.ur.get_gpio_reading, name="NUMATO_get_gpio_reading")
        self.server.register_function(self.ur.get_gpio_analog_reading, name="NUMATO_get_gpio_analog_reading")

    def serve_forever(self):
        """
            Call serve_forever method of rpc_server. It is called automatically by __init__
            NOTE: This should not be renamed to rpc_serve_forever since that name is reserved
                for a method that the user has to call, if the driver is written in such a
                way that the RPC server loop has to be run manually after calling __init__
        """
        self.server.serve_forever()
        self.ui_root.close()

    def simple_ui(self):
        """
            Generates a simple user interface showing the state of the simulated hardware
        """
        app = QApplication([])
        self.ui_root = QDialog()
        self.ui_root.setWindowTitle(f"Numato Board")
        self.ui_root.setStyleSheet("QLabel {font: 10pt Helvetica}")
        column = QVBoxLayout()
        label = QLabel(f"Port: {self.rpc_server_port}", self.ui_root)
        column.addWidget(label)
        row = QHBoxLayout()
        self.relay_box = []
        for i in range(self.relay_count):
            label = QLabel(f"{i}", self.ui_root)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(30, 20)
            color = "#00ff00" if self.ur.relay_states[i] else "#ff0000"
            label.setStyleSheet(f"background-color:{color};")
            self.relay_box.append(label)
            row.addWidget(label)
        column.addLayout(row)
        self.ui_root.setLayout(column)
        self.ui_root.setFixedSize(self.ui_root.sizeHint())
        self.ui_root.show()
        timer = QTimer(self.ui_root)
        timer.setSingleShot(False)
        timer.timeout.connect(self.update_ui)
        timer.start(200)
        app.exec_()

    def update_ui(self):
        for i in range(self.relay_count):
            color = "#00ff00" if self.ur.relay_states[i] else "#ff0000"
            self.relay_box[i].setStyleSheet(f"background-color:{color};")


def parse_arguments():
    """
        parse command line arguments
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial_port_name", help="serial port name of the Numato relay board", default="/dev/ttyACM0")
    parser.add_argument("-r",
                        "--rpc_server_port",
                        type=int,
                        help="port for an rpc server to accept client",
                        default=rpc_ports["relay_drivers"])
    parser.add_argument("-n", "--name", help="name for an rpc server", default="NumatoDriver")
    parser.add_argument("-rc", "--relay_count", help="how many relays in this board", default=4)
    parser.add_argument("-gc", "--gpio_count", help="how many gpios in this board", default=4)

    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()

    if args.name:
        rpc_server_name = args.name
    else:
        rpc_server_name = f"NUMATO_{args.serial_port_name}"

    logger = LOLoggerClient(client_name=f"RPC_NUMATO_{args.serial_port_name}", verbose=True)

    SimNumatoDriver(device_port_name=args.serial_port_name,
                    rpc_server_port=args.rpc_server_port,
                    rpc_server_name=rpc_server_name,
                    rpc_server_description="Driver for Numato RelayBoard",
                    relay_count=args.relay_count,
                    gpio_count=args.gpio_count,
                    logger=logger)


if __name__ == "__main__":
    main()
