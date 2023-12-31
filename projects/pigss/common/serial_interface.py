import serial


class SerialInterface(object):
    def __init__(self):
        """ Initializes Serial Interface """
        self.serial = None

    def config(self,
               port=None,
               baudrate=9600,
               bytesize=serial.EIGHTBITS,
               parity=serial.PARITY_NONE,
               stopbits=serial.STOPBITS_ONE,
               timeout=0.2,
               xonxoff=0,
               rtscts=0):
        """
        :param port: number of device, numbering starts at zero. if everything fails, the user can specify a
                    device string, note that this isn't portable anymore if no port is specified an unconfigured an
                    closed serial port object is created
        :param baudrate: baudrate
        :param bytesize: number of databits
        :param parity: enable parity checking
        :param stopbits: number of stopbits
        :param timeout: set a timeout value, None for waiting forever
        :param xonxoff: enable software flow control
        :param rtscts: enable RTS/CTS flow control
        :return:
        """
        self.serial = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout, xonxoff, rtscts)

    def open(self):
        """ Opens port """
        if self.serial is not None:
            if not self.serial.isOpen():
                self.serial.open()

    def close(self):
        """ Closes port """
        if self.serial is not None:
            if self.serial.isOpen():
                self.serial.close()

    def read(self, terminator=b"\n"):
        if not isinstance(terminator, bytes):
            raise AssertionError("Terminator in serial_interface.read must be a byte string")
        return self.serial.read_until(terminator).decode()

    def write(self, msg):
        self.serial.write(msg.encode())


if __name__ == "__main__":
    import time
    s = SerialInterface()
    s.config(port='/dev/ttyUSB0', baudrate=19200)
    try:
        s.open()
        s.write("A\r")
        time.sleep(0.2)
        print(s.read())
    except Exception:
        raise
    finally:
        s.close()
