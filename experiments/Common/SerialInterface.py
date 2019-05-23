"""
File Name: SerialInterface.py
Purpose: Handles serial/rs232 interface communication.

Copyright (c) 2019 Picarro, Inc. All rights reserved
"""
import serial


class SerialInterface(object):
    def __init__(self):
        """ Initializes Serial Interface """
        self.terminate = False
        self.serial = None

    def config(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
               stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=0, rtscts=0):
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
            if not self.serial.isOpen():
                self.serial.close()

    def read(self, carriage_return=None):
        if carriage_return is not None:
            command_buffer = ""
            while True:
                data = self.serial.read().decode()
                if data[0] == carriage_return:
                    return command_buffer
                else:
                    command_buffer += data
        return self.serial.read().decode()

    def write(self, msg):
        self.serial.write(msg.encode())


if __name__ == "__main__":
    s = SerialInterface()
    s.config(port='/dev/ttyS1', timeout=1)
    s.open()
    print(s.write("Hello from PySerial\r\n"))
    print(s.read())
    s.close()
