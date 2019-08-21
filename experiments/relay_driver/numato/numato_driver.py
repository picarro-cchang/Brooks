"""
    A module to control a Numato Lab’s 4 Channel USB Powered Relay Module.
    python numato_driver_proto.py "/dev/ttyACM1" 6668
"""
import time

import serial

from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from experiments.testing.cmd_fifo import CmdFIFO

GPIO_MODES = ["D_IN", "D_OUT", "A_IN"]


class UsbRelay:
    """A class to control a Numato USB relay module."""

    def __init__(self, port_name, relay_count=4, gpio_count=4, debug=False, logger=None):
        """Init function."""
        self.portName = port_name
        self.debug = debug
        self.relayCount = relay_count
        self.gpioCount = gpio_count
        self.gpioModes = []
        self.gpioOutputStatus = []
        self.serPort = serial.Serial(port=self.portName,
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
        for i in range(self.relayCount):
            self.set_relay(i, False)
        # set all gpio off
        for i in range(self.gpioCount):
            self.gpioModes.append("D_OUT")
            self.gpioOutputStatus.append(False)
            self.set_gpio_status(i, False)

    def __wait_for_echo(self, command):
        while self.serPort.readline().decode().strip().replace(">", "") != command:
            time.sleep(0.001)

    def __send(self, command, answer_needed=False, wait_after=0.01):
        self.serPort.write(str.encode("{}\r".format(command)))
        # if self.debug:
        #     print("SENDING COMMAND [{}]".format(command))
        self.__wait_for_echo(command)
        time.sleep(wait_after)

        if answer_needed:
            answer_line = self.serPort.readline().decode().strip()
            time.sleep(wait_after)
            # if self.debug:
            #     print("                                       ANSWER [{}]".format(answer_line))
            return answer_line

    def get_relay_status(self, relayNum):
        """
            Returns relay status as boolean.
            relayNum (int)
        """
        if relayNum >= self.relayCount:
            raise ValueError("relayNum is bigger than relayCount")
        responce = self.__send("relay read {}".format(relayNum), True)
        return responce == "on"

    def set_relay(self, relayNum, status):
        """
            Sets relay on or off.
            relayNum (int)
            status (bool)
        """
        if relayNum >= self.relayCount:
            raise ValueError("relayNum is bigger than relayCount")
        key = "on" if status else "off"
        self.__send("relay {} {}".format(key, relayNum))

    def flip_relay(self, relayNum):
        """
            Flips relay to an opposite state from current
            relayNum (int)
        """
        self.set_relay(relayNum, not self.get_relay_status(relayNum))

    def set_id(self, newId):
        """
            Sets device ID.
            newID (string)
        """
        if len(newId) != 8:
            raise ValueError("new id must be exactly 8 chars")
        self.__send("id set {}".format(newId))

    def get_id(self):
        """
            Returns device ID.
        """
        return self.__send("id get", True)

    def do_disco(self, relayNum=0, times=8, delay=0.05):
        """
            Disco
        """
        for i in range(times):
            self.flip_relay(relayNum)
            time.sleep(delay)

    def do_full_disco(self, cycles):
        for k in range(cycles):
            self.logger.info(f"Cycle {k} in progress, {100*((k+1.)/cycles)}% done")
            for i in range(self.relayCount):
                self.do_disco(i)

    def __gpio_check(self, gpioNum, required_mode=None):
        """
            Checks if GPIO requested GPIO exists and is in the right state.
            gpioNum (int)
            required_mode [GPIO_MODES]
        """
        if gpioNum >= self.gpioCount:
            raise ValueError("gpioNum is bigger than gpioCount")
        if required_mode is not None:
            if self.gpioModes[gpioNum] != required_mode:
                raise ValueError("current gpio mode is wrong, should be {}".format(required_mode))

    def get_gpio_mode(self, gpioNum):
        """
            Returns current mode of the requested GPIO.
            gpioNum (int)
        """
        self.__gpio_check(gpioNum)
        return self.gpioModes[gpioNum]

    def set_gpio_mode(self, gpioNum, mode):
        """
            Sets requested GPIO to a requested mocde.
            gpioNum (int)
            mode [GPIO_MODES]
        """
        self.__gpio_check(gpioNum)
        if mode not in GPIO_MODES:
            raise ValueError("mode not supported")
        if mode in ["D_IN", "A_IN"]:
            self.gpioOutputStatus[gpioNum] = False
        self.gpioModes[gpioNum] = mode

    def set_gpio_status(self, gpioNum, status):
        """
            If GPIO is in D_OUT mode - sets it to HIGH or LOW.
            gpioNum (int)
            status (bool)
        """
        self.__gpio_check(gpioNum, required_mode="D_OUT")
        if not isinstance(status, bool):
            raise ValueError("status should be boolean")
        key = "set" if status else "clear"
        self.__send("gpio {} {}".format(key, gpioNum))
        self.gpioOutputStatus[gpioNum] = status

    def get_gpio_status(self, gpioNum):
        """
            If GPIO is in D_OUT mode - returns it's status as bool, which has been previously set.
            gpioNum (int)
        """
        self.__gpio_check(gpioNum, required_mode="D_OUT")
        return self.gpioOutputStatus[gpioNum]

    def get_gpio_reading(self, gpioNum):
        """
            If GPIO is in D_IN mode - returns it's reading.
            gpioNum (int)
        """
        self.__gpio_check(gpioNum, required_mode="D_IN")
        responce = self.__send("gpio read {}".format(gpioNum), True)
        return responce == "on"

    def get_gpio_analog_reading(self, gpioNum):
        """
            If GPIO is in A_IN mode - returns it's reading.
            gpioNum (int)
        """
        self.__gpio_check(gpioNum, required_mode="A_IN")
        return self.__send("adc read {}".format(gpioNum), True)


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
    parser.add_argument("serial_port_name", help="serial port name of the Numato relay board", default="/dev/ttyACM1")
    parser.add_argument("rpc_server_port", type=int, help="port for an rpc server to accept client", default=6668)
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
        rpc_server_name = "NUMATO_{}".format(args.serial_port_name)

    logger = LOLoggerClient(client_name=f"RPC_NUMATO_{args.serial_port_name}", verbose=True)

    numato_driver = NumatoDriver(device_port_name=args.serial_port_name,
                                 rpc_server_port=args.rpc_server_port,
                                 rpc_server_name=args.name,
                                 rpc_server_description="Driver for Numato RelayBoard",
                                 relay_count=args.relay_count,
                                 gpio_count=args.gpio_count,
                                 logger=logger)
    logger.info(f"Numato Relay Board Driver for {args.serial_port_name} created.")
    logger.info(f"RPC server will be available at {args.rpc_server_port} in a sec.")

    try:
        numato_driver.rpc_serve_forever()
    except KeyboardInterrupt:
        logger.info("RPC server has ended it's lifecycle after brutal KeyboardInterrupt, good job.")

    logger.info("RPC server has ended")


if __name__ == "__main__":
    main()

# def test():
#     """Test."""
#     serial_port_name = "/dev/ttyACM1"
#     numato_driver = NumatoDriver(serial_port_name, 6668)
#     numato_driver.server.serve_forever()

# create object
# ub = UsbRelay("/dev/ttyACM1", debug=True)

# set device ID
#ub.set_id("11223344")

# get device ID
# print("{}".format(ub.get_id()))

# # set device ID
# ub.set_id("55667788")

# # get device ID
# print("{}".format(ub.get_id()))

# # relay flip test
# for i in range(4):
#     print("relay {} is {}".format(i, ub.get_relay_status(i)))
#     ub.set_relay(i, False)
#     print("relay {} is {}".format(i, ub.get_relay_status(i)))
#     time.sleep(0.5)

# time.sleep(1)

# for t in range(9):
#     for i in range(4):
#         print("relay {} is {}".format(i, ub.get_relay_status(i)))
#         ub.flip_relay(i)
#         print("relay {} is {}".format(i, ub.get_relay_status(i)))
#         time.sleep(0.1 / (t + 1))

# do disco
# for i in range(10):
#     for i in range(3):
#         ub.do_disco(relayNum=i)

# ub.set_relay(0, False)
# ub.set_relay(1, False)
# ub.set_relay(2, False)
# ub.set_relay(3, False)
# for i in range(100):
#     time.sleep(0.01)
#     print(ub.get_relay_status(3))

# if __name__ == "__main__":
#     test()
# ub = UsbRelay("/dev/ttyACM2", debug=True)
# ub.init()

# ub.set_relay()

# for i in range(4):
#     print(ub.get_gpio_status(i))

# time.sleep(1)

# for i in range(4):
#     print(ub.set_gpio_status(i, True))

# time.sleep(1)

# for i in range(4):
#     print(ub.get_gpio_status(i))
