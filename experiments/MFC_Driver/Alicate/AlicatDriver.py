from host.experiments.MFC_Driver.IMFCDriver import IMFCDriver
from host.experiments.Common.SerialInterface import SerialInterface
from host.experiments.MFC_Driver.conf import port, baudrate, carriage_return
import serial
import time


# lets say our class is implementing IMFCDriver interface
@IMFCDriver.register
class AlicatDriver:
    def __init__(self):
        self.serial = None
        self.terminate = False
        self.connect()

    def connect(self):
        try:
            self.serial = SerialInterface()
            self.serial.config(port=port, baudrate=baudrate)
        except serial.SerialException as e:
            msg = "Unable to connect to Alicat MFC. EXCEPTION: %s" % e
            print(msg)
            raise e

    def send(self, command):
        command_buffer = ""
        """ waits for a complete input line and returns command to caller """
        while not self.terminate:
            try:
                self.serial.write(command)
                s = self.serial.read()
                if s[0] == carriage_return:
                    return command_buffer
                else:
                    command_buffer += s
            except serial.SerialException as e:
                msg = "Unable to read command. EXCEPTION: %s" % e
                print(msg)
                time.sleep(0.2)
                continue
            except serial.SerialTimeoutException as e:
                msg = "Unable to read command. TIMEOUTEXCEPTION: %s" % e
                print(msg)
                time.sleep(0.2)
                continue
        return command_buffer


if __name__ == "__main__":
    obj = AlicatDriver()
    print(obj.send("A"+carriage_return))
