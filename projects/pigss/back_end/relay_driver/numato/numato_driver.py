"""
    A module to control a Numato Lab’s 4 Channel USB Powered Relay Module.
    python numato_driver_proto.py "/dev/ttyACM1" 6668
"""
import time
import serial

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
        self.gpio_modes = ["D_OUT"]*self.gpio_count
        self.gpio_output_status = [False]*self.gpio_count
        self.serial_port = serial.Serial(port=self.port_name,
                                     baudrate=19200,
                                     bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE,
                                     write_timeout=0,
                                     inter_byte_timeout=0)

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
            self.set_gpio_status(i, False)

    def __wait_for_echo(self, command):
        while self.serial_port.readline().decode().strip().replace(">", "") != command:
            time.sleep(0.001)

    def __send(self, command, answer_needed=False, wait_after=0.01):
        self.serial_port.write(str.encode(f"{command}\r"))
        self.__wait_for_echo(command)
        time.sleep(wait_after)

        if answer_needed:
            answer_line = self.serial_port.readline().decode().strip()
            time.sleep(wait_after)
            return answer_line

    def get_relay_status(self, relay_num):
        """
            Returns relay status as boolean.
            relay_num (int)
        """
        if relay_num >= self.relay_count:
            raise ValueError("relay_num is bigger than relay_count")
        responce = self.__send(f"relay read {relay_num}", True)
        return responce == "on"

    def set_relay(self, relay_num, status):
        """
            Sets relay on or off.
            relay_num (int)
            status (bool)
        """
        if relay_num >= self.relay_count:
            raise ValueError("relay_num is bigger than relay_count")
        key = "on" if status else "off"
        self.__send(f"relay {key} {relay_num}")

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
        self.__send(f"id set {new_id}")

    def get_id(self):
        """
            Returns device ID.
        """
        return self.__send("id get", True)

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
        key = "set" if status else "clear"
        self.__send(f"gpio {key} {gpio_num}")
        self.gpio_output_status[gpio_num] = status

    def get_gpio_status(self, gpio_num):
        """
            If GPIO is in D_OUT mode - returns it's status as bool, which has been previously set.
            gpio_num (int)
        """
        self.__gpio_check(gpio_num, required_mode="D_OUT")
        return self.gpio_output_status[gpio_num]

    def get_gpio_reading(self, gpio_num):
        """
            If GPIO is in D_IN mode - returns it's reading.
            gpio_num (int)
        """
        self.__gpio_check(gpio_num, required_mode="D_IN")
        responce = self.__send(f"gpio read {gpio_num}", True)
        return responce == "on"

    def get_gpio_analog_reading(self, gpio_num):
        """
            If GPIO is in A_IN mode - returns it's reading.
            gpio_num (int)
        """
        self.__gpio_check(gpio_num, required_mode="A_IN")
        return self.__send(f"adc read {gpio_num}", True)


class NumatoDriver(object):
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
                 logger=None):
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

    def rpc_serve_forever(self):
        """
            Start RPC server and serve it forever.
            this is a blocking method - call once you are done setting tags
        """
        self.server.serve_forever()


def parse_arguments():
    """
        parse command line arguments
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial_port_name", help="serial port name of the Numato relay board", default="/dev/ttyACM0")
    parser.add_argument("-r", "--rpc_server_port", type=int, help="port for an rpc server to accept client", default=rpc_ports["relay_drivers"])
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

    numato_driver = NumatoDriver(device_port_name=args.serial_port_name,
                                 rpc_server_port=args.rpc_server_port,
                                 rpc_server_name=rpc_server_name,
                                 rpc_server_description="Driver for Numato RelayBoard",
                                 relay_count=args.relay_count,
                                 gpio_count=args.gpio_count,
                                 logger=logger)
    logger.info(f"Numato Relay Board Driver for {args.serial_port_name} created.")
    logger.info(f"RPC server will be available at {args.rpc_server_port} in a sec.")

    try:
        numato_driver.rpc_serve_forever()
    except KeyboardInterrupt:
        logger.info("RPC server has ended from a Keyboard Interrupt.")

    logger.info("RPC server has ended")


if __name__ == "__main__":
    main()
