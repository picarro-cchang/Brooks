from host.experiments.mfc_driver.i_mfc_driver import IMFCDriver
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.mfc_driver.conf import port, baudrate, carriage_return
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
        self.serial.write(command + carriage_return)
        time.sleep(0.2)
        return self.serial.read()

    def close(self):
        if self.serial is not None:
            self.serial.close()


if __name__ == "__main__":
    obj = AlicatDriver()
    for x in range(10):
        print(obj.send("A"))
