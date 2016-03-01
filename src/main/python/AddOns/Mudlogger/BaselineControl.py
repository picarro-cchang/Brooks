import serial, time

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_VALVE_SEQUENCER

APP_NAME = "ValveControl_GCC_CRDS"
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, APP_NAME)


class BaselineControl(object):
    '''Control of the Baseline GC'''
    def __init__(self, sidebar):
        self.sidebar = sidebar
        self.furnace_delay = 120.0 #seconds, will be overwritten by setup parameters
        self.connection = None
        self.connection = self.search_for_GCC_CRDS()
        self.monitor_flag = False
        self.warning_flag = False
        
    def set_monitor_flag(self):
        self.monitor_flag = True

    def search_for_GCC_CRDS(self):
        # firmware_command yeilds 'MLPvXX',
        # where the XX is the firmware version.
        firmware_command = 'y'
        expected_string = 'MLPv'
        min_search_value = 2
        max_search_value = 100
        for port in range(min_search_value, max_search_value):
            try:
                serial_connection = self.setup_serial(port)
            except:
                pass
        
            try:
                if serial_connection != None:
                    time.sleep(2.0)
                    self.write(serial_connection, firmware_command)
                    if expected_string in self.read_line(serial_connection):
                        return serial_connection
            except:
                pass
        return None

    def setup_serial(self, port, baudrate=9600, timeout=1.0):
        try:
            return serial.Serial(port, baudrate=baudrate, timeout=timeout)
        except:
            return None

    def write(self, serial_connection, message, flag=False):
        self.flush_buffers(serial_connection)
        try:
            bytes_written = serial_connection.write(message)
        except:
            if self.connection is None:
                raise
            else:
                self.sidebar.write_alert_to_log('Error: Cannot write to GC.\n')
        if flag:
            print bytes_written

    def stop_all(self, flag=False):
        message = 'gk' # stop all from baseline
        if self.connection != None:
            self.write(self.connection, message, flag)

    def trigger_gc_sequence(self, seq):
        #firmware switch cases...
        command_dictionary = {1:'go1', 2:'go2', 3:'gs3'}
        if self.connection != None:
            self.write(self.connection, command_dictionary[seq], False)

    def flush_buffers(self, serial_connection):
        serial_connection.flushInput()
        serial_connection.flushOutput()

    def read_line(self, serial_connection):
        return serial_connection.readline()
        
    def get_device_port(self):
        if self.connection != None:
            return self.connection.portstr
        else:
            return None

    def has_warnings(self):
        if self.monitor_flag:
            try:            
                if float(self.get_warnings()) != 0:
                    self.set_warning_flag(True)
                else:
                    self.set_warning_flag(False)
            except:
                return None
        return self.warning_flag

    def set_warning_flag(self, boolean):
        self.warning_flag = boolean
        
    def get_warnings(self):
        data_stream = None
        if self.connection != None:
            try:
                self.write(self.connection, 'gc', False)
                data_stream = self.read_line(self.connection)
            except:
                pass
        return data_stream
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        