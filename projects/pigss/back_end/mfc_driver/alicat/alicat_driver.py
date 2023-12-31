import argparse
import time

import serial

from common import CmdFIFO
from common.rpc_ports import rpc_ports
from common.serial_interface import SerialInterface
from common.timeutils import get_local_timestamp
from back_end.lologger.lologger_client import LOLoggerClient


class AlicatDriver(object):
    """
    Alicat Quickstart Guide:
        https://documents.alicat.com/Alicat-Serial-Primer.pdf
    """

    def __init__(self, port, rpc_port, carriage_return='\r', mfc_id='A', baudrate=19200):
        self.serial = None
        self.terminate = False
        self.data_dict = None
        self.id = mfc_id
        self.port = port
        self.baudrate = baudrate
        self.carriage_return = carriage_return
        self.rpc_port = rpc_port
        self.rpc_server = CmdFIFO.CmdFIFOServer(("", self.rpc_port),
                                                ServerName=__class__.__name__,
                                                ServerDescription=f"RPC Server for {__class__.__name__}",
                                                ServerVersion=1.0,
                                                threaded=True)
        self.logger = LOLoggerClient(client_name='MFCDriver')
        self.logger.debug(f'Started')
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
            self.serial.config(port=self.port, baudrate=self.baudrate, timeout=0.2)
            self.logger.debug(f'\nConnecting to Alicat on {self.port}\n')
        except serial.SerialException:
            raise

    def send(self, command, lines_to_receive=1):
        """
        This function will send any string to the MFC. If the MFC does not
        recognize the command, it will response with: '?'. If an unrecognized command
        is sent, we will disregard the response, otherwise we will
        return the response.

        When the Alicat receives its own id character followed by a carriage return,
         it responds with status string terminated by a carriage return, e.g.,

        Send> A\r
        Recv> A +014.44 +026.92 +000.00 +000.00 000.00     Air\r

        If we send it a set-point command, the response consists of two lines, as shown

        Send> AS 10.00\r
        Recv> 10.0000\rA +014.44 +026.92 +000.00 +000.00 010.00     Air\r

        It is necessary to specify the number of lines to receive so that we wait for
        the correct number of carriage returns.

        :param command: Command to send
        :param lines_to_receive: Number of lines to receive
        :return: if `lines_to_recive`==1, either the received string or None if the Alicat returns "?"
                 otherwise, the list of received strings
        """
        self.serial.write(command + self.carriage_return)
        time.sleep(0.01)
        """
        Alicat recommends an optimal baud rate of 19200
        We start getting garbage data from the MFC if we try
        to poll faster than 5 Hz at this baud rate.
        """
        try:
            response = [self.serial.read(terminator=b"\r").strip() for i in range(lines_to_receive)]
            if lines_to_receive == 1:
                response = response[0]
                if response == '?':
                    # Alicat doesn't recognize the command
                    self.logger.debug(f'Command not recognized: {command}')
                    response = None
        except serial.SerialException:
            response = None
        self.logger.Log(f'Command sent: {command}\nResponse received: {response}\n', level=5)
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
            self.send(self.id + "S" + str(set_point), lines_to_receive=2)
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
    parser.add_argument('-i', '--mfc_id', help='Alicat MFC ID', default='A')
    parser.add_argument('-p', '--mfc_port', help='Alicat MFC Port', default='/dev/ttyUSB0')
    parser.add_argument('-b', '--baudrate', help='Alicat MFC baudrate', default=19200)
    parser.add_argument('-r', '--rpc_port', help='Piglet RPC Port', default=rpc_ports.get('mfc_drivers'))
    args = parser.parse_args()
    return args


def main():
    cli_args = get_cli_args()
    id = cli_args.mfc_id.upper()
    port = cli_args.mfc_port
    baudrate = cli_args.baudrate
    rpc_port = cli_args.rpc_port
    if __debug__:
        print(f'\nAlicat MFC_ID: {id}'
              f'\nAlicat MFC Port: {port}'
              f'\nAlicat RCP Port: {rpc_port}'
              f'\nAlicat MFC Baudrate: {baudrate}\n')
    # Instantiate the object and serve the RPC Port forever
    AlicatDriver(mfc_id=id, port=port, baudrate=baudrate, rpc_port=int(rpc_port))
    if __debug__:
        print('AlicatDriver stopped.')


if __name__ == "__main__":
    import sys
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
