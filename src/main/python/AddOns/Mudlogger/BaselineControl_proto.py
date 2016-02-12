APP_NAME = "ValveControl_GCC_CRDS"

import serial, time

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_VALVE_SEQUENCER

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, APP_NAME)


class BaselineControl(object):
    '''Includes both Control of the Baseline GC and the valves used
    for sample handling'''
    def __init__(self):
        # time delay after a Run has started before the sample gas 
        # from GC is allowed to go to the Combustion Furnace and to
        # the CRDS for analysis. and the flag is used to signal that
        # when the run is finished, the valve is switch to divert flow
        self.open_sample_valve_delay = 10.0 #seconds, will be overwritten by setup parameters
        self.open_sample_valve_duration = 10.0 #seconds, will be overwritten by setup parametes
        self.close_sample_valve_on_finish_flag = True
        self.number_of_valves = 6
        self.furnace_delay = 120.0 #seconds, will be overwritten by setup parameters
     
        self.three_way_valve_mask = 32 
        self.two_way_valve_position = 2 #Needs to be changed to match final hardware configuration.
        
        self.index_shift = 1
        self.base = 2
        
        # self.delay is seconds to wait before clearing the gc trigger
        # the 0th bit is used trigger the DIO of the gc
        # if the DIO sigal isn't reset to 00000 then the
        # next 'communication' will not be acknowledged.
        self.delay = 1
        self.trigger_flag = False
        self.valve_flag = False
        
        self.monitor_flag = False
        self.warning_flag = False
        self.filter_done = False
        
        self.connection = self.initialize_usb_communication_with_monitor()
        
        # reset all DIO signals
        self.clear_gc_trigger()

    def reset_filter_done(self):
        self.filter_done = False
        
    def get_warning_flag(self):
        return self.warning_flag
    
    def set_warning_flag(self, boolean):
        self.warning_flag = boolean
    
    def get_monitor_flag(self):
        return self.monitor_flag
        
    def set_monitor_flag(self):
        self.monitor_flag = True
    
    def get_device_port(self):
        if self.connection != None:
            return self.connection.portstr
        else: 
            return None
        
    def get_current_sequence(self):
        return CRDS_Driver.getValveMask()
        
    def get_current_valve_mask(self):
        return CRDS_Driver.getValveMask()
        
    def trigger_gc_sequence(self,mask):
        self.trigger_flag = True
        self.set_valve_mask(mask)
        
    def clear_gc_trigger(self):
        self.trigger_flag = False
        self.set_valve_mask(0)
        
    def activate_three_way_value(self):
        if not self.filter_done:
            self.valve_flag = True
            self.set_valve_mask(self.three_way_valve_mask)
        
    def deactivate_three_way_valve(self):
        if not self.filter_done:
            self.valve_flag = False
            self.filter_done = True
            self.set_valve_mask(0)
     
    
    def set_valve_mask(self,mask):
        CRDS_Driver.closeValves((~mask) & (self.base**self.number_of_valves-self.index_shift))
        CRDS_Driver.openValves(mask & (self.base**self.number_of_valves-self.index_shift))
        
        
    def stop_all(self):
        ## don't have the hardward capacity to use this function yet.
        stop_all = 63 # 5 bits all on
        self.set_valve_mask(stop_all)
        time.sleep(1.0)
        self.set_valve_mask(0)
        
    ## VALVE FUNCTIONS NO LONGER WORK PROPERLY AFTER USING THE 1-5 RELAYS FOR THE CONTACT
    ## CLOSURES... NEED TO MODIFY THESE IF IT TURNS OUT THAT WE NEED TO USE A VALVE CONTROL
    def open_sample_valve(self):
        mask = self.base**(self.three_way_valve_position - self.index_shift)
        mask += self.is_two_way_valve_open()*self.base**(self.two_way_valve_position - self.index_shift)
        self.set_valve_mask(mask)
        
    def close_sample_valve(self):
        mask = self.is_two_way_valve_open()*self.base**(self.two_way_valve_position - self.index_shift)
        self.set_valve_mask(mask)
        
    def is_two_way_valve_open(self):
        b_list = self.convert(self.get_current_valve_mask())
        try:
            return b_list[-self.two_way_valve_position] == 1
        except IndexError:
            return False
        
        
    def convert(self,mask,b_list = []):
        if mask > 1:
            self.convert(mask//2,b_list)
        b_list.append(mask%2)
        return b_list
        
    def initialize_usb_communication_with_monitor(self):
        serial_connection = self.search_for_GCC_CRDS()
        if serial_connection != None:
            return serial_connection
        return None
      
        
    def search_for_GCC_CRDS(self):
        
            # firmware_command yeilds 'MLPvXX',
            # where the XX is the firmware version.
            firmware_command = 'y'
            expected_string = 'MLPv'
            min_search_value = 2
            max_search_value = 100
            for port in range(min_search_value,max_search_value):
                try:
                    serial_connection = self.setup_serial(port)
                except:
                    pass
            
                try:
                    if serial_connection != None:
                        self.delay_for_arduino()
                        self.write(serial_connection, firmware_command)
                        if expected_string in self.read_line(serial_connection):
                            return serial_connection
                except:
                    pass
            return None
                
             
    def setup_serial(self, port, baudrate = 9600, timeout = 1.0):
        try:
            return serial.Serial(port, baudrate=baudrate, timeout=timeout)
        except:
            return None

    def close_serial(self, serial_connection):
        serial_connection.close()

    def flush_buffers(self, serial_connection):
        serial_connection.flushInput()
        serial_connection.flushOutput()

    def write(self, serial_connection, message,flag=False):
        self.flush_buffers(serial_connection)
        bytes_written = serial_connection.write(message)
        if flag:
            print bytes_written

    def read_line(self, serial_connection):
        return serial_connection.readline()

    def is_connected(self, serial_connection):
        return serial_connection != None

    def delay_for_arduino(self):
        time.sleep(2.0)
        
    def get_DIO_data(self):
        data_stream = None
        if self.connection != None:
            self.write(self.connection,'GD')
            data_stream = self.read_line(self.connection)
        return data_stream
        
    def has_warnings(self):
        if self.get_monitor_flag():
            try:
                #if sum([float(value) for value in self.get_DIO_data().split('\t')]) != 0:
                if False:
                    self.set_warning_flag(True)
                else:
                    self.set_warning_flag(False)
            except:
                return None
        return self.get_warning_flag()