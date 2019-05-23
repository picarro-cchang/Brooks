from host.experiments.MFC_Driver.IMFCDriver import IMFCDriver
from host.experiments.Common.SerialInterface import SerialInterface
from host.experiments.MFC_Driver.conf import port, baudrate, carriage_return


# lets say our class is implementing IMFCDriver interface
@IMFCDriver.register
class AlicateDriver:
    def __init__(self):
        self.serial = None
        self.connect()

    def connect(self):
        self.serial = SerialInterface()
        self.serial.config(port=port, baudrate=baudrate)

    def send(self, command):
        self.serial.write(command)
        return self.serial.read()


if __name__ == "__main__":
    obj = AlicateDriver()
    print(obj.send("A"+carriage_return))
