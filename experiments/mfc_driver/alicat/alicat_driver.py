import serial
import time
import argparse
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.common.timeutils import get_local_timestamp

# TODO
#   Remove local import for CmdFIFO
#   Remove hardcoded host
#   Remove hardcoded port
import CmdFIFO


class AlicatDriver(object):
    """
    Alicat Quickstart Guide:
        https://documents.alicat.com/Alicat-Serial-Primer.pdf
    """
    def __init__(self, port, carriage_return='\r',
                 mfc_id='A', baudrate=19200):
        self.serial = None
        self.terminate = False
        self.data_dict = None
        self.id = mfc_id
        self.port = port
        self.baudrate = baudrate
        self.carriage_return = carriage_return
        self.rpc_server = CmdFIFO.CmdFIFOServer(
            ("", 6667),
            ServerName=__class__.__name__,
            ServerDescription=f"RPC Server for {__class__.__name__}",
            ServerVersion=1.0,
            threaded=True
        )
        self.connect()
        self.register_rpc_functions()
        self.rpc_server.serve_forever()

    def connect(self):
        """
        This function opens the serial port defined when the
        class is instantiated.

        :return:
        """
        try:
            self.serial = SerialInterface()
            self.serial.config(port=self.port, baudrate=self.baudrate)
            if __debug__:
                print(f'\nConnecting to Alicat on {self.port}\n')
        except serial.SerialException:
            raise

    def send(self, command):
        """
        This function will send any string to the MFC. If the MFC does not
        recognize the command, it will response with: '?'. If an unrecognized command
        is sent, we will disregard the response, otherwise we will
        return the response.

        :param command:
        :return:
        """
        self.serial.write(command + self.carriage_return)
        """
        Alicat recommends an optimal baud rate of 19200
        We start getting garbage data from the MFC if we try
        to poll faster than 5 Hz at this baud rate.
        """
        time.sleep(0.2)
        response = self.serial.read()
        if response == '?':
            # Alicat doesn't recognize the command
            if __debug__:
                print(f'Command not recognized: {command}')
            response = None
        if __debug__:
            print(f'Command sent: {command}\nResponse received: {response}\n')
        return response

    def close(self):
        """
        This function will close the serial port if it is open.
        :return:
        """
        if self.serial is not None:
            self.serial.close()

    def get_data(self):
        """
        This function will send a command to the MFC, the MFC will then
        reply back with a string containing all of its pertinent data.

        Example:
            A +014.44 +026.92 +000.00 +000.00 000.00     Air

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

        A current local time will be appended to the dict in ISO 8601
        format.

        Example of returned dict:
            {'id': 'A', 'pressure': '+007.55', 'temperature': '+024.79', 'v_flow': '+007.05',
            'm_flow': '+003.34', 'set_point': '003.50', 'gas_id': 'Air', 'timestamp': '2019-07-02 10:30:47'}

        This function will automatically grab a new data string from the MFC,
        parse the string, and return a timestamped dictionary.

        :return:
        """
        data = self.get_data()
        current_time = get_local_timestamp()
        data_keys = ['id', 'pressure', 'temperature', 'v_flow', 'm_flow', 'set_point', 'gas_id']
        data_values = ''.join(data).split()
        self.data_dict = dict(zip(data_keys, data_values))
        self.data_dict['timestamp'] = current_time
        return self.data_dict

    def get_id(self):
        """
        This function will get the id of the MFC provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        alicat_id = self.data_dict.get('id', None)
        return alicat_id

    def get_pressure(self):
        """
        This function will get the pressure of the MFC provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        pressure = self.data_dict.get('pressure', None)
        return pressure

    def get_temperature(self):
        """
        This function will get the temperature of the MFC provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        temperature = self.data_dict.get('temperature', None)
        return temperature

    def get_volumetric_flow(self):
        """
        This function will get the volumetric flow of the MFC provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        v_flow = self.data_dict.get('v_flow', None)
        return v_flow

    def get_mass_flow(self):
        """
        This function will get the mass flow of the MFC provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        mass_flow = self.data_dict.get('m_flow', None)
        return mass_flow

    def get_set_point(self):
        """
        This function will get the flow set point of the MFC provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        set_point = self.data_dict.get('set_point', None)
        return set_point

    def get_gas_id(self):
        """
        This function will get the gas id of the MFC provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        gas_id = self.data_dict.get('gas_id', None)
        return gas_id

    def get_flow_delta(self):
        """This function will calculate the difference in flow between
        the current mass flow rate and the current mass flow set point.
        The data used in the calculation is from the get_set_point and
        the get_mass_flow functions.

        If no data exists, is a None type, or is garbled from the MFC,
        it will either fall into a TypeError, or ValueError and the
        function will return None. The function get_data_dict will need
        to be run to gather updated data, otherwise this function will
        continue to return the last gathered data.

        :return:
        """
        try:
            set_point = float(self.get_set_point())
            flow_rate = float(self.get_mass_flow())
            delta = abs(set_point - flow_rate)
        except TypeError:
            delta = None
        except ValueError:
            delta = None
        return delta

    def get_timestamp(self):
        """
        This function will get current local timestamp provided by the
        get_data_dict function. If no data exists, it will return None.
        Otherwise, it will return the value in the dict. The function
        get_data_dict will need to be run to gather updated data, otherwise
        this function will continue to return the last gathered data.

        :return:
        """
        timestamp = self.data_dict.get('timestamp', None)
        return timestamp

    def set_set_point(self, set_point):
        """
        This function will accept any string and attempt to convert
        it into a float with a precision of 2. The MFC will reject any
        flow set point with a precision > 2. If the conversion to a float
        fails, the command will not be sent to the MFC and this function
        will return None. Otherwise, the set point will be sent to the MFC
        and we will return the set point.

        :param set_point:
        :return:
        """
        try:
            # We need to convert the string into a float, and
            # set the precision to 2, otherwise the MFC will
            # reject the setpoint.
            set_point = float(set_point)
            set_point = round(set_point, 2)
            self.send(self.id + "S" + str(set_point))
        except TypeError:
            set_point = None
        except ValueError:
            set_point = None
        return set_point

    def register_rpc_functions(self):
        self.rpc_server.register_function(self.send)
        self.rpc_server.register_function(self.connect)
        self.rpc_server.register_function(self.close)
        self.rpc_server.register_function(self.get_data)
        self.rpc_server.register_function(self.get_data_dict)
        self.rpc_server.register_function(self.get_id)
        self.rpc_server.register_function(self.get_pressure)
        self.rpc_server.register_function(self.get_temperature)
        self.rpc_server.register_function(self.get_volumetric_flow)
        self.rpc_server.register_function(self.get_mass_flow)
        self.rpc_server.register_function(self.get_set_point)
        self.rpc_server.register_function(self.get_gas_id)
        self.rpc_server.register_function(self.get_flow_delta)
        self.rpc_server.register_function(self.get_timestamp)
        self.rpc_server.register_function(self.set_set_point)


def get_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--mfc_id', help='Alicat MFC ID')
    parser.add_argument('-p', '--mfc_port', help='Alicat MFC Port')
    parser.add_argument('-b', '--baudrate', help='Alicat MFC baudrate')
    args = parser.parse_args()
    return args


def main():
    cli_args = get_cli_args()
    # Get the MFC ID from the CLI
    if cli_args.mfc_id:
        id = cli_args.mfc_id.upper()
    else:
        id = 'A'
    if __debug__:
        print(f'Alicat MFC ID: {id}')
    # Get the MFC Port from the CLI
    if cli_args.mfc_port:
        port = cli_args.mfc_port
    else:
        port = '/dev/ttyUSB0'
    if __debug__:
        print(f'Alicat MFC Port: {port}')
    # Get the MFC baudrate from the CLI
    if cli_args.baudrate:
        baudrate = cli_args.baudrate
    else:
        baudrate = 19200
    if __debug__:
        print(f'Alicat MFC baudrate: {baudrate}')
    # Instantiate the object and serve the RPC Port forever
    AlicatDriver(mfc_id=id, port=port, baudrate=baudrate)
    if __debug__:
        print('AlicatDriver stopped.')


if __name__ == "__main__":
    import sys
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
