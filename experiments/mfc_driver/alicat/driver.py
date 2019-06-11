from host.experiments.mfc_driver.i_mfc_driver import IMFCDriver
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.mfc_driver.conf import port, baudrate, carriage_return
import serial
import time


# lets say our class is implementing IMFCDriver interface
@IMFCDriver.register
class AlicatDriver:
    """
    Alicat Quickstart Guide:
        https://documents.alicat.com/Alicat-Serial-Primer.pdf
    """
    def __init__(self):
        self.serial = None
        self.terminate = False
        self.connect()

    def connect(self):
        """
        :return:
        """
        try:
            self.serial = SerialInterface()
            self.serial.config(port=port, baudrate=baudrate)
        except serial.SerialException as e:
            msg = "Unable to connect to Alicat MFC. EXCEPTION: %s" % e
            print(msg)
            raise e

    def send(self, command):
        """
        :param command:
        :return:
        """
        self.serial.write(command + carriage_return)
        time.sleep(0.2)
        response = self.serial.read()
        if response == '?':
            # Alicat doesn't recognize the command
            response = None
        return response

    def close(self):
        """
        :return:
        """
        if self.serial is not None:
            self.serial.close()

    def get_data(self):
        """
        :return:
        """
        data = self.send("A")
        return data

    def get_data_dict(self):
        """
        Data string from Alicat example:
            A +014.44 +026.92 +000.00 +000.00 000.00     Air
        Element IDs:
            0: Device ID
            1: Absolute Pressure
            2: Temperature
            3: Volumetric Flow Rate
            4: Mass Flow Rate
            5: Setpoint
            6: Gas Select
        :return:
        """
        data = self.get_data()
        data_keys = ['id', 'pressure', 'temperature', 'v_flow', 'm_flow', 'set_point', 'gas_id']
        data_values = ''.join(data).split()
        data_dict = dict(zip(data_keys, data_values))
        return data_dict

    def get_id(self):
        alicat_id = self.get_data_dict().get('id', None)
        return alicat_id

    def get_pressure(self):
        pressure = self.get_data_dict().get('pressure', None)
        return pressure

    def get_temperature(self):
        temperature = self.get_data_dict().get('temperature', None)
        return temperature

    def get_volumetric_flow(self):
        v_flow = self.get_data_dict().get('v_flow', None)
        return v_flow

    def get_mass_flow(self):
        mass_flow = self.get_data_dict().get('m_flow', None)
        return mass_flow

    def get_set_point(self):
        set_point = self.get_data_dict().get('set_point', None)
        return set_point

    def get_gas_id(self):
        gas_id = self.get_data_dict().get('gas_id', None)
        return gas_id

    def get_flow_delta(self):
        try:
            set_point = float(self.get_set_point())
            flow_rate = float(self.get_mass_flow())
            delta = abs(set_point - flow_rate)
        except TypeError:
            delta = None
        return delta

    def set_set_point(self, set_point):
        self.send("AS" + set_point)


if __name__ == "__main__":
    from pprint import pprint
    obj = AlicatDriver()
    obj.set_set_point('5')
    print(obj.get_set_point())
    print(obj.get_mass_flow())
    print(obj.get_flow_delta())
    # pprint(obj.get_data_dict())
