"""A module to control a Numato Lab’s 4 Channel USB Powered Relay Module."""
import time

import serial


GPIO_MODES = ["D_IN", "D_OUT", "A_IN"]


class UsbRelay:
    """A class to control a USB relay module."""

    def __init__(self, port_name, relay_count=4, gpio_count=4, debug=False):
        """Init function."""
        self.portName = port_name
        self.debug = debug
        self.relayCount = relay_count
        self.gpioCount = gpio_count
        self.gpioModes = []
        self.gpioOutputStatus = []
        self.serPort = serial.Serial(
            port=self.portName,
            baudrate=19200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            write_timeout=0,
            inter_byte_timeout=0)

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

    def __send(self, command, answer_needed=False):
        self.serPort.write(str.encode("{}\r".format(command)))
        if self.debug:
            print("SENDING COMMAND [{}]".format(command))
        self.__wait_for_echo(command)

        if answer_needed:
            answer_line = self.serPort.readline().decode().strip()
            if self.debug:
                print("                                       ANSWER [{}]".format(answer_line))
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


def test():
    """Test."""
    # create object
    ub = UsbRelay("/dev/ttyACM2", debug=True)

    # set device ID
    #ub.set_id("11223344")

    # get device ID
    print("{}".format(ub.get_id()))

    # set device ID
    ub.set_id("55667788")

    # get device ID
    print("{}".format(ub.get_id()))

    # relay flip test
    for i in range(4):
        print("relay {} is {}".format(i, ub.get_relay_status(i)))
        ub.set_relay(i, False)
        print("relay {} is {}".format(i, ub.get_relay_status(i)))
        time.sleep(0.5)

    time.sleep(1)

    for t in range(9):
        for i in range(4):
            print("relay {} is {}".format(i, ub.get_relay_status(i)))
            ub.flip_relay(i)
            print("relay {} is {}".format(i, ub.get_relay_status(i)))
            time.sleep(0.1 / (t + 1))

    # do disco
    ub.do_disco()


if __name__ == "__main__":
    #test()
    ub = UsbRelay("/dev/ttyACM2", debug=True)
    ub.init()

    for i in range(4):
        print(ub.get_gpio_status(i))

    time.sleep(1)

    for i in range(4):
        print(ub.set_gpio_status(i, True))

    time.sleep(1)

    for i in range(4):
        print(ub.get_gpio_status(i))
    
