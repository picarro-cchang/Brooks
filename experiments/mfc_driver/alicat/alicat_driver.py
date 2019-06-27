import serial
import time
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.common.timeutils import get_local_timestamp


class AlicatDriver(object):
    """
    Alicat Quickstart Guide:
        https://documents.alicat.com/Alicat-Serial-Primer.pdf
    """
    def __init__(self, mfc_id, port, baudrate, carriage_return):
        self.serial = None
        self.terminate = False
        self.data_dict = None
        self.id = mfc_id
        self.port = port
        self.baudrate = baudrate
        self.carriage_return = carriage_return
        self.connect()

    def connect(self):
        """
        :return:
        """
        try:
            self.serial = SerialInterface()
            self.serial.config(port=self.port, baudrate=self.baudrate)
        except serial.SerialException:
            raise

    def send(self, command):
        """
        :param command:
        :return:
        """
        self.serial.write(command + self.carriage_return)
        time.sleep(0.1)
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
        data = self.send(self.id)
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
        self.data_dict = dict(zip(data_keys, data_values))
        return self.data_dict

    def get_id(self):
        alicat_id = self.data_dict.get('id', None)
        return alicat_id

    def get_pressure(self):
        pressure = self.data_dict.get('pressure', None)
        return pressure

    def get_temperature(self):
        temperature = self.data_dict.get('temperature', None)
        return temperature

    def get_volumetric_flow(self):
        v_flow = self.data_dict.get('v_flow', None)
        return v_flow

    def get_mass_flow(self):
        mass_flow = self.data_dict.get('m_flow', None)
        return mass_flow

    def get_set_point(self):
        set_point = self.data_dict.get('set_point', None)
        return set_point

    def get_gas_id(self):
        gas_id = self.data_dict.get('gas_id', None)
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
        self.send(self.id + "S" + str(set_point))


if __name__ == "__main__":
    obj = AlicatDriver(mfc_id='A', port='/dev/ttyUSB0', baudrate=19200, carriage_return='\r')
    sp = 5
    print('Setting setpoint to: {}'.format(sp))
    obj.set_set_point(sp)
    count = 0
    while True:
        obj.get_data_dict()
        print('Time: {}'.format(get_local_timestamp()))
        print('Mass Flow Setpoint: {}'.format(obj.get_set_point()))
        print('Mass Flow: {}'.format(obj.get_mass_flow()))
        print('Delta Flow: {}'.format(obj.get_flow_delta()))
        print('Gas ID: {}'.format(obj.get_gas_id()))
        print('Pressure: {}'.format(obj.get_pressure()))
        print('Temperature: {}'.format(obj.get_temperature()))
        print('Count: {}\n'.format(count))
        count += 1
