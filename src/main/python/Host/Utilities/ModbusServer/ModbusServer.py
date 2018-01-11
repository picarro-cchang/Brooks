"""
This is the Modbus server program running on analyzers.
It serves for 2 purposes:
1) Report measurement results and analyzer status through modbus.
2) Allow remote control of analyzer through modbus

"""

# FYI, if this code is started in shell with a different directory
# some code and ini files won't load if their location is defined
# with a relative path.

# FYI the original code was written with everything in 
# Host/Utilities/Modbus and only worked if the code was started
# with a shell in this directory.  It wouldn't work if started by
# the Supervisor because relative paths would break as this code's
# working directory would be than expected.  To make the code work
# I made the following changes:
#
# *Add module pathnames in the import statements.
# *Prepend relative paths with sys.path[0].  sys.path[0] is the full
#  path of this code.
# *Move ModbusServer.ini to AppConfig/Config/Utilities
#
# 11NOV2017 RSF

import os
import sys
import time
import getopt
import math
import random
from struct import pack, unpack
import threading
from Host.Utilities.ModbusServer.ErrorHandler import Errors, ErrorHandler
from Queue import Queue
from pymodbus.server.sync import ModbusSerialServer
from pymodbus.server.sync import ModbusTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.transaction import ModbusSocketFramer

from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO, SharedTypes, Listener, StringPickler
from Host.Utilities.ModbusServer.ModbusDataBlock import ThreadSafeDataBlock, CallbackDataBlock
from Host.Utilities.ModbusServer.ModbusUtils import get_variable_type, ModbusScriptEnv
from Host.Common import AppStatus
from Host.Common import InstMgrInc

import socket

def get_ip_address():
    '''
    Method use to get eth0 ip address and run modbus server using ip address for Modbus over TCPIP
    :return:
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception, e:
        print "Error in reading IpAddress in ModbusServer: %s " % e
        return '127.0.0.1'

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
APP_NAME = "ModbusServer"

COIL = 1
DISCRETE_INPUT = 2
HOLDING_REGISTER = 3
INPUT_REGISTER = 4

def StartServer(rtu = True, context=None, framer=None, identity=None, **kwargs):
    ''' 
    This is a bug in pyModbus 1.2.0 that only allows framer=ModbusAsciiFramer
    The bug is fixed in pymodbus 1.3.0. The solution here will work for both versions.
    '''
    if rtu:
        server = ModbusSerialServer(context, framer, identity, **kwargs)
    else:
        server = ModbusTcpServer(context, framer, identity, **kwargs)
    server.serve_forever() 

class ModbusServer(object):
    def __init__(self, configFile, simulation, debug):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            raise Exception("Configuration file not found: %s" % configFile) 
        if debug:
            import logging
            logging.basicConfig()
            log = logging.getLogger()
            log.setLevel(logging.DEBUG)
        self.slaveid = self.config.getint("SerialPortSetup", "SlaveId", 1)
        self.rtu = self.config.getboolean("Main", "rtu", False)
        self.debug = debug
        self.get_register_info()
        self.errorhandler = ErrorHandler(self, 'Errors')
        self.data_queue = Queue()
        self.command_queue = Queue()
        sync_bits = {}
        r = self.register_variables
        for v in r[COIL-1]['variables']:
            if self.variable_params[v]['sync'] and ("function" in self.variable_params[v]):
                sync_bits[self.variable_params[v]['address']] = self.variable_params[v]['function']
        store = ModbusSlaveContext(
            # PyModbus add one buffer index for each register address so adding 1 for each register size
            # if we dont add 1 more space we will get address error when reading last register value
            # read-only status and alarm bits
            di = ThreadSafeDataBlock(ModbusSequentialDataBlock(0x00, [0]*(1+r[DISCRETE_INPUT-1]['size']))),
            # remote control bits
            co = ThreadSafeDataBlock(CallbackDataBlock(self.command_queue, sync_bits, 0x00, [0]*(1+r[COIL-1]['size']))),
            # remote control parameters
            hr = ThreadSafeDataBlock(ModbusSequentialDataBlock(0x00, [0]*(1+r[HOLDING_REGISTER-1]['size']))),
            # read-only output variables
            ir = ThreadSafeDataBlock(ModbusSequentialDataBlock(0x00, [0]*(1+r[INPUT_REGISTER-1]['size'])))
        )
        self.context = ModbusServerContext(slaves={self.slaveid:store}, single=False)

        identity = ModbusDeviceIdentification()
        identity.VendorName  = 'Picarro'
        identity.ProductCode = 'SI2000'
        identity.VendorUrl   = 'http://www.picarro.com'
        identity.ProductName = 'Picarro Modbus Server'
        identity.ModelName   = 'Picarro Modbus Server'
        identity.MajorMinorRevision = '1.0'
        if self.rtu:
            framer = ModbusRtuFramer
        else:
            framer = ModbusSocketFramer
        self.serverConfig = {
            "rtu": self.rtu,
            "context": self.context, 
            "framer": framer,
            "identity": identity,
            "address" : (get_ip_address(), self.config.getint("Main", "TCPPort", 50500)),
            "port": self.config.get("SerialPortSetup", "Port").strip(),
            "baudrate": self.config.getint("SerialPortSetup", "BaudRate", 19200),
            "timeout": self.config.getfloat("SerialPortSetup", "TimeOut", 1.0),
            "bytesize": self.config.getint("SerialPortSetup", "ByteSize", 8),
            "parity": self.config.get("SerialPortSetup", "Parity", "N"),
            "stopbits": self.config.getint("SerialPortSetup", "StopBits", 1),
            "ignore_missing_slaves": True}
        if simulation:
            self.get_simulation_params()
            self.data_thread = threading.Thread(target=self.simulate_data)
            self.data_thread.daemon = True
            self.data_thread.start()
        else:
            self.source = self.config.get("Main", "Source")
            self.data_thread = Listener.Listener(self.data_queue,
                                        SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                        StringPickler.ArbitraryObject,
                                        self._streamFilter,
                                        retry = True,
                                        name = APP_NAME)
            self.InstMgrStatusListener = Listener.Listener(None,
                                                  SharedTypes.STATUS_PORT_INST_MANAGER,
                                                  AppStatus.STREAM_Status,
                                                  self._InstMgrStatusFilter,
                                                  retry = True,
                                                  name = APP_NAME)
        # writer thread gets data from queue and write to memory
        self.writer_thread = threading.Thread(target=self.data_writer)
        self.writer_thread.daemon = True
        # control thread gets command from queue and execute
        self.control_thread = threading.Thread(target=self.controller)
        self.control_thread.daemon = True
    
    def get_register_info(self):
        self.register_variables = [{}, {}, {}, {}]
        self.variable_params = {}
        self.endian = ">" if self.config.get("Main", "Endian", "Big").lower() == "big" else "<"
        script_name = self.config.get("Main", "Script", "")
        script_path = sys.path[0] + "/" + script_name
        scriptEnv = ModbusScriptEnv(self).create_script_env()
        if os.path.exists(script_path):
            script = file(script_path, 'r')
            scriptObj = compile(script.read().replace("\r\n","\n"), script_path, 'exec')
            exec scriptObj in scriptEnv
        for s in self.config:
            name = ""
            d = {}
            if s.startswith("Variable_"):
                name = s[9:]
                d["bit"] = self.config.getint(s, "Byte") * 8
                d["size"] = d["bit"] / 16
                d["type"] = self.config.get(s, "Type")
                d["format"] = self.endian + "".join( [get_variable_type(d["bit"], d["type"])])
                if self.config.getboolean(s, "ReadOnly"):
                    d["register"] = INPUT_REGISTER
                else:
                    d["register"] = HOLDING_REGISTER
            elif s.startswith("Bit_"):
                name = s[4:]                
                if self.config.getboolean(s, "ReadOnly"):
                    d["register"] = DISCRETE_INPUT
                else:
                    d["register"] = COIL
                    d["sync"] = self.config.getboolean(s, "Sync", False)
            if name:
                d["name"] = name
                d["address"] = self.config.getint(s, "Address")
                if "Value" in self.config[s]:
                    d["Value"] = self.config[s]["Value"]
                if "Function" in self.config[s]:
                    func = self.config[s]["Function"]
                    if func in scriptEnv:
                        d["function"] = scriptEnv[func]
                    else:
                        raise Exception("Function not found: %s (in section %s)" % (func, s))
                if "Input" in self.config[s]:
                    d["input"] = self.config[s]["Input"].split(",")
                self.variable_params[name] = d
        for register in range(4):
            # sort list based on address of variables
            li = [self.variable_params[v] for v in self.variable_params if self.variable_params[v]["register"] == (register + 1)]
            sorted_list = sorted(li, key=lambda k: k["address"])
            self.register_variables[register]["variables"] = [v["name"] for v in sorted_list]
            if register >= 2:   # variables
                self.register_variables[register]["size"] = self.check_variable_address(sorted_list)
                self.register_variables[register]["format"] = self.endian + \
                    "".join( [get_variable_type(v["bit"], v["type"]) for v in sorted_list] )
            else:       # bits
                self.register_variables[register]["size"] = self.check_bit_address(sorted_list)
        self.readonly_variables = self.register_variables[DISCRETE_INPUT-1]["variables"] \
                + self.register_variables[INPUT_REGISTER-1]["variables"]
    
    def check_variable_address(self, variable_list):
        addr, var_size = 0, 0
        address_dict={}
        for v in variable_list:
            addr = v["address"]
            if addr in address_dict:
                raise Exception("Variable address of %s is wrong, Address is already used by other variable!" % (v["name"]))
            var_size = v["bit"] / 16
            for i in range(0,var_size):
                address_dict[addr+i] = True
        return addr + var_size
        
    def check_bit_address(self, bit_list):
        addr = 0
        address_dict = {}
        for b in bit_list:
            addr = b["address"]
            if addr in address_dict:
                raise Exception("Variable address of %s is wrong. Address is already used by other variable!" % (b["name"]))
            address_dict[addr] = True
        return addr+1

    def get_simulation_params(self):
        self.simulation_dict = {}
        for s in self.config:
            if s.startswith("Variable_") and self.config.getboolean(s, "ReadOnly") and self.config.has_option("Simulation", s):
                self.simulation_dict[s[9:]] = self.config.get("Simulation", s)
        self.simulation_env = {func: getattr(math, func) for func in dir(math) if not func.startswith("__")}
        self.simulation_env.update({'random':  random.random, 'time': time, 'x': 0})
        self.simulation_max_index = self.config.getint('Simulation', 'Max_Index', 100)

    # Method use to write read only register values
    # if pass with more than one register it will write sequential one by one
    def write_readonly_registers(self, value_dict):
        try:
            for v in self.register_variables[INPUT_REGISTER - 1]["variables"]:
                if v in value_dict:
                    variableParam = self.variable_params[v]
                    # write ir variables
                    values = [value_dict[v]]
                    if len(values) > 0:
                        str = pack(variableParam['format'], *values)
                        value_to_write = list( unpack('%s%dH' % (self.endian, variableParam['size']), str) )
                        self.context[self.slaveid].setValues(INPUT_REGISTER, variableParam['address'], value_to_write)
            # write di bits
            for v in self.register_variables[DISCRETE_INPUT - 1]["variables"]:
                if v in value_dict:
                    variableParam = self.variable_params[v]
                    values = [value_dict[v]]
                    if len(values) > 0:
                        self.context[self.slaveid].setValues(DISCRETE_INPUT, variableParam['address'], values)
        except KeyError:
            pass

    # Method is use to write all data in one lock
    # Main idea is to write all data which are dependent in one write and while writing client can
    # not able to read. Still it can go in to race condition as if client read some of the
    # values and before client read remaining value server overwrite all data
    # in that case client will have fist read values as old data and remaining read
    # will have new data (Means race condition)
    def write_readonly_all_data_with_one_lock(self, value_dict):
        try:
            addressValues_dict={}
            for v in self.register_variables[INPUT_REGISTER - 1]["variables"]:
                if v in value_dict:
                    variableParam = self.variable_params[v]
                    # write ir variables
                    values = [value_dict[v]]
                    if len(values) > 0:
                        str = pack(variableParam['format'], *values)
                        value_to_write = list( unpack('%s%dH' % (self.endian, variableParam['size']), str) )
                        addressValues_dict[variableParam['address']]=value_to_write
            self.context[self.slaveid].setValues(INPUT_REGISTER, 0 ,addressValues_dict)
            addressValues_dict = {}
            # write di bits
            for v in self.register_variables[DISCRETE_INPUT - 1]["variables"]:
                if v in value_dict:
                    variableParam = self.variable_params[v]
                    values = [value_dict[v]]
                    if len(values) > 0:
                        addressValues_dict[variableParam['address']] = values
            self.context[self.slaveid].setValues(DISCRETE_INPUT, 0 ,addressValues_dict)
        except KeyError:
            pass

    # Method is use to write all data at once which is depend on time stamp
    # For that we forcing use that all data has to go in sequential memory
    # so we can write all data in one write and client can read all data in one read
    def write_readonly_all_data_in_one_write(self, value_dict):
        try:
            # write ir variables
            values = []
            format = self.endian
            datasize=0
            startaddress=0
            for v in self.register_variables[INPUT_REGISTER - 1]["variables"]:
                if v in value_dict:
                    variableParam = self.variable_params[v]
                    if datasize == 0:
                        startaddress = variableParam['address']
                    values.extend([value_dict[v]])
                    format += variableParam['format'][1:]
                    datasize += variableParam['size']
            if len(values) > 0:
                str = pack(format, *values)
                value_to_write = list(unpack('%s%dH' % (self.endian, datasize), str))
                self.context[self.slaveid].setValues(INPUT_REGISTER, startaddress, value_to_write)
            # write di bits
            values = []
            format = self.endian
            datasize = 0
            for v in self.register_variables[DISCRETE_INPUT - 1]["variables"]:
                if v in value_dict:
                    variableParam = self.variable_params[v]
                    if datasize == 0:
                        startaddress = variableParam['address']
                    datasize += 1
                    values.extend([value_dict[v]])
            if len(values) > 0:
               self.context[self.slaveid].setValues(DISCRETE_INPUT, startaddress, values)
        except KeyError:
            pass

    def write_readonly_constant_data(self):
        '''
        Method use to write all constant register values
        :return:
        '''
        # set default as no error
        self.errorhandler.set_error(Errors.NO_ERROR)
        instr_cal_file_path = self.config.get("Main", "InstrumentCalFilePath", "")
        user_cal_file_path = self.config.get("Main", "UserCalFilePath", "")
        instr_cal_file_path = sys.path[0] + "/" + instr_cal_file_path
        user_cal_file_path = sys.path[0] + "/" + user_cal_file_path
        self.Write_Instrument_Cal_File_Data(instr_cal_file_path)
        self.Write_User_Cal_Data(user_cal_file_path)
        self.Write_All_Const_Values()

    def Write_Instrument_Cal_File_Data(self, file_path):
        """
        Method will read instrument cal file and write gas offset and slope
        in modbus memory register which are included in register map
        :param file_path:
        """

        # open files and read content of file. if file is missing throw exception
        if os.path.exists(file_path):
            instrument_cal_config = CustomConfigObj(file_path)
        else:
            raise Exception("Configuration file not found: %s" % file_path)
        data_dict = {}
        # now go over each variable and check if variable is available in instrument
        # calibration file. If it is present lets get value of variable so we can
        # write to modbus memory
        for v in self.register_variables[INPUT_REGISTER - 1]["variables"]:
            if 'Value' not in self.variable_params[v] and instrument_cal_config.has_option('Data', v):
                data_dict[v] = instrument_cal_config.getfloat('Data', v)

        # let make sure that there is data to write
        if len (data_dict) > 0:
            self.write_readonly_registers(data_dict)



    def Write_User_Cal_Data(self, file_path):
        '''
        Method will read user cal file and write gas offset and slope
        in modbus memory register which are included in register map
        :param file_path:
        :return:
        '''

        # open files and read content of file. if file is missing throw exception
        if os.path.exists(file_path):
            user_cal_config = CustomConfigObj(file_path)
        else:
            raise Exception("Configuration file not found: %s" % file_path)
        data_dict = {}
        # lets go through all available variable and check if variable are slope or offset related
        for v in self.register_variables[INPUT_REGISTER - 1]["variables"]:
            if (v.endswith('_slope') or v.endswith('_offset')) and 'Value' not in self.variable_params[v]:
                words = v.rsplit('_',1)
                if len(words) == 2:
                    section = words[0]
                    option = words[1]
                    # lets make sure that variable is present in file
                    # variable is present in file lets save to dictionary so we can
                    # write to modbus register
                    if user_cal_config.has_section(section):
                        data_dict[v] = user_cal_config.getfloat(section, option)
        # let make sure that there is data to write
        if len(data_dict) > 0:
            self.write_readonly_registers(data_dict)

    def Write_All_Const_Values(self):
        '''
        Method use to write all constant value in modbus register
        :return:
        '''
        data_dict = {}
        # Go through each variable and get constant value of it
        for v in self.register_variables[INPUT_REGISTER - 1]["variables"]:
            variableParam = self.variable_params[v]
            if 'Value' in variableParam:
                data_dict[v] = float(variableParam['Value'])
        # let make sure that there is data to write
        if len(data_dict) > 0:
            self.write_readonly_registers(data_dict)
        
    def _streamFilter(self, streamOut):
        try:
            if streamOut["source"] == self.source:
                data = streamOut["data"]
                result = self.process_data(data)
                if self.debug:
                    print "Processed data: ", result
                return result
        except Exception, err:
            print "Error: %s" % err
            
    def process_data(self, data_dict):
        result = {}
        for v in self.readonly_variables:
            if "function" in self.variable_params[v]:
                if "input" in self.variable_params[v]:
                    try:
                        input = [data_dict[n] for n in self.variable_params[v]["input"]]
                    except:
                        continue
                else:
                    input = []
                result[v] = self.variable_params[v]["function"](*input)
            else:
                if v in data_dict:
                    result[v] = data_dict[v]
        return result
        
    def simulate_data(self):
        data = {}
        while True:
            time.sleep(1)
            for k in self.simulation_dict:
                data[k] = self.run_simulation_expression(self.simulation_dict[k])
            result = self.process_data(data)
            self.write_readonly_all_data_with_one_lock(result)
            if self.simulation_env['x'] == self.simulation_max_index:
                self.simulation_env['x'] = 0
            else:
                self.simulation_env['x'] += 1
                
    def run_simulation_expression(self, expression):
        if len(expression) > 0:
            exec "simulation_result=" + expression in self.simulation_env
            return self.simulation_env["simulation_result"]
        else:
            return 0.0
            
    def controller(self):
        addr_func_map = {}
        for v in self.register_variables[COIL-1]['variables']:
            if "function" in self.variable_params[v]:
                addr_func_map[self.variable_params[v]['address']] = self.variable_params[v]['function']
        while True:
            time.sleep(1)
            while not self.command_queue.empty():
                addr = self.command_queue.get(False)
                ret = addr_func_map[addr]()
                
    def data_writer(self):
        time.sleep(1)
        self.write_readonly_constant_data()
        while True:
            time.sleep(0.1)
            while not self.data_queue.empty():
                data = self.data_queue.get(False)
                self.write_readonly_all_data_with_one_lock(data)
        
    def run(self):
        self.control_thread.start()
        self.writer_thread.start()
        StartServer(**self.serverConfig)

    def _InstMgrStatusFilter(self, obj):
        """Updates the local (latest) copy of the instrument manager status bits."""
        LedState = self.get_Instrument_Status(obj.status)
        data_dict = {}
        data_dict["Measurement_Status"] = LedState
        # let make sure that there is data to write
        if len(data_dict) > 0:
            self.write_readonly_registers(data_dict)

    def get_Instrument_Status(self, currentInstMgrStatus):

        pressureLocked = currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_PRESSURE_LOCKED
        cavityTempLocked = currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_CAVITY_TEMP_LOCKED
        warmboxTempLocked = currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
        measActive = currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_MEAS_ACTIVE
        warmingUp = currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_WARMING_UP
        systemError = currentInstMgrStatus & InstMgrInc.INSTMGR_STATUS_SYSTEM_ERROR

        # ANOTHER TERRIBLE KLUDGE HERE...
        # RSF 04NOV2017
        #
        # The analyzer GUI and front panel have a real and simulated red/yellow/green LED
        # indicating the analyzer measuring state.  The logic to set the LED color in the
        # GUI and front panel light is (originally) set in SysAlarmGui.py.  That is the
        # color logic is in the GUI code at the point the color needs to be determined.
        # Not my choice to put it there!
        #
        # Well now, with the addition of Modbus, we need to report this status in a Modbus
        # register.  Unfortunately the LED status in SysAlarmGui.py can't be shared with
        # any other code so we have to repeat the LED color selection logic here and put
        # the state in the reportDict.  And, unfortunately again, SysAlarmGui.py can't
        # read this data stream without a significant redesign so the LED color logic
        # remains there too.
        #
        # ledState = 0 # red, system error, gas conc. measurements invalid
        # ledState = 1 # solid yellow, need service, gas conc. measurements might be ok
        # ledState = 2 # blinking yellow, not in reporting mode by system ok, like during warmup
        # ledState = 3 # green, system ok, gas conc. measurements accurate
        #
        # Note that at this time there is no test that sets ledState = 1. Checks to do this
        # is TBD.
        #
        ledState = 0
        makeLedBlink = False
        if pressureLocked and cavityTempLocked and warmboxTempLocked and measActive and \
                (not warmingUp) and (not systemError) and (not makeLedBlink):
            ledState = 3  # green
        if ledState != 3:
            descr = "System Status:"
            if warmingUp or makeLedBlink:
                descr += "\n* Warming Up"
                ledState = 2  # blinking yellow
            if systemError:
                descr += "\n* System Error"
            if not pressureLocked:
                descr += "\n* Pressure Unlocked"
            if not cavityTempLocked:
                descr += "\n* Cavity Temp Unlocked"
            if not warmboxTempLocked:
                descr += "\n* Warm Box Temp Unlocked"
            if not measActive:
                descr += "\n* Measurement Not Active"
                ledState = 2

        return ledState


HELP_STRING = """ModbusServer.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./ModbusServer.ini"
-s                   simulation mode
--debug              debug mode
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:s'
    longOpts = ["help", "debug"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = "./ModbusServer.ini"
    simulation = False
    debug = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options:
        simulation = True
    if "--debug" in options:
        debug = True
    return (configFile, simulation, debug)

if __name__ == "__main__":
    server = ModbusServer(*handleCommandSwitches())
    server.run()
