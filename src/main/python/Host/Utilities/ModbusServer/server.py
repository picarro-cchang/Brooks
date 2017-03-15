"""
This is the Modbus server program running on analyzers.
It serves for 2 purposes:
1) Report measurement results and analyzer status through modbus.
2) Allow remote control of analyzer through modbus


"""

import os
import sys
import time
import getopt
import math
import random
from struct import pack, unpack
import threading
from contextlib import contextmanager
from pymodbus.server.sync import StartSerialServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer

from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO, SharedTypes, Listener, StringPickler

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
APP_NAME = "ModbusServer"

# Uncomment these lines for debugging
# import logging
# logging.basicConfig()
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

COIL = 1
DISCRETE_INPUT = 2
HOLDING_REGISTER = 3
INPUT_REGISTER = 4

struct_type_map = {
    "int_32"  :  "i",
    "float_32":  "f",
    "float_64":  "d"
}
def get_variable_type(bit, type):
    if type == "string":
        return "%ds" % (bit/8)
    else:
        return struct_type_map["%s_%s" % (type.strip().lower(), bit)]
        

class ReadWriteLock(object):
    ''' This is a write-preferring RW lock from pymodbus document:
    https://pymodbus.readthedocs.io/en/latest/examples/thread-safe-datastore.html
    '''

    def __init__(self):
        ''' Initializes a new instance of the ReadWriteLock
        '''
        self.queue   = []                                  # waiting list of readers and writers
        self.lock    = threading.Lock()                    # the underlying condition lock
        self.read_condition = threading.Condition(self.lock) # the single reader condition
        self.readers = 0                                   # the number of current readers
        self.writer  = False                               # is there a current writer

    def __is_pending_writer(self):
        return (self.writer                                # if there is a current writer
            or (self.queue                                 # or if queue is not empty
           and (self.queue[0] != self.read_condition)))    # and the queue head is a writer

    def acquire_reader(self):
        ''' Notifies the lock that a new reader is requesting
        the underlying resource.
        '''
        with self.lock:
            if self.__is_pending_writer():                 # if there are existing writers waiting
                if self.read_condition not in self.queue:  # do not pollute the queue with more than 1 reader condition
                    self.queue.append(self.read_condition) # add the readers in line for the queue
                while self.__is_pending_writer():          # until the current writer is finished
                    self.read_condition.wait(1)            # wait on our condition
                if self.queue and self.read_condition == self.queue[0]: # if the read condition is at the queue head
                    self.queue.pop(0)                      # then go ahead and remove it
            self.readers += 1                              # update the current number of readers

    def acquire_writer(self):
        ''' Notifies the lock that a new writer is requesting
        the underlying resource.
        '''
        with self.lock:
            if self.writer or self.readers:                # if we need to wait on a writer or readers
                condition = threading.Condition(self.lock) # create a condition just for this writer
                self.queue.append(condition)               # and put it on the waiting queue
                while self.writer or self.readers:         # until the write lock is free
                    condition.wait(1)                      # wait on our condition
                # when this condition is released, it must be at the queue head
                self.queue.pop(0)                          # remove our condition after our condition is met
            self.writer = True                             # stop other writers from operating

    def release_reader(self):
        ''' Notifies the lock that an existing reader is
        finished with the underlying resource.
        '''
        with self.lock:
            self.readers = max(0, self.readers - 1)        # readers should never go below 0
            if not self.readers and self.queue:            # if there are no active readers
                self.queue[0].notify_all()                 # then notify any waiting writers

    def release_writer(self):
        ''' Notifies the lock that an existing writer is
        finished with the underlying resource.
        '''
        with self.lock:
            self.writer = False                            # give up current writing handle
            if self.queue:                                 # if someone is waiting in the queue
                self.queue[0].notify_all()                 # wake them up first
            else: self.read_condition.notify_all()         # otherwise wake up all possible readers

    @contextmanager
    def get_reader_lock(self):
        ''' Wrap some code with a reader lock using the
        python context manager protocol::

            with rwlock.get_reader_lock():
                do_read_operation()
        '''
        try:
            self.acquire_reader()
            yield self
        finally: self.release_reader()

    @contextmanager
    def get_writer_lock(self):
        ''' Wrap some code with a writer lock using the
        python context manager protocol::

            with rwlock.get_writer_lock():
                do_read_operation()
        '''
        try:
            self.acquire_writer()
            yield self
        finally: self.release_writer()
        
        
class ThreadSafeDataBlock(object):
    ''' This is a simple decorator for a data block. This allows
    a user to inject an existing data block which can then be
    safely operated on from multiple cocurrent threads.

    It should be noted that the choice was made to lock around the
    datablock instead of the manager as there is less source of 
    contention (writes can occur to slave 0x01 while reads can
    occur to slave 0x02).
    '''

    def __init__(self, block):
        ''' Initialize a new thread safe decorator

        :param block: The block to decorate
        '''
        self.rwlock = ReadWriteLock()
        self.block  = block

    def validate(self, address, count=1):
        ''' Checks to see if the request is in range

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        '''
        with self.rwlock.get_reader_lock():
            return self.block.validate(address, count)

    def getValues(self, address, count=1):
        ''' Returns the requested values of the datastore

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        with self.rwlock.get_reader_lock():
            return self.block.getValues(address, count)
 
    def setValues(self, address, values):
        ''' Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        '''
        with self.rwlock.get_writer_lock():
            return self.block.setValues(address, values)
      
        
class ModbusServer(object):
    def __init__(self, configFile, simulation):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            raise Exception("Configuration file not found: %s" % configFile) 
        self.get_register_info()
        # if the block size is set to the desired size, I find that only size-1 can be read, at least on my laptop.
        # so I set the block to be size + 1     (Yuan 2017)
        store = ModbusSlaveContext(
            di = ThreadSafeDataBlock(ModbusSequentialDataBlock(0x00, [0]*(1+self.register_variables[0]['size']))),
            co = ThreadSafeDataBlock(ModbusSequentialDataBlock(0x00, [0]*(1+self.register_variables[1]['size']))),
            hr = ThreadSafeDataBlock(ModbusSequentialDataBlock(0x00, [0]*(1+self.register_variables[2]['size']))),
            ir = ThreadSafeDataBlock(ModbusSequentialDataBlock(0x00, [0]*(1+self.register_variables[3]['size'])))
        )
        self.context = ModbusServerContext(slaves=store, single=True)

        identity = ModbusDeviceIdentification()
        identity.VendorName  = 'Picarro'
        identity.ProductCode = 'SI2000'
        identity.VendorUrl   = 'http://www.picarro.com'
        identity.ProductName = 'Picarro Modbus Server'
        identity.ModelName   = 'Picarro Modbus Server'
        identity.MajorMinorRevision = '1.0'
        self.serverConfig = {
            "context": self.context, 
            "framer": ModbusRtuFramer, 
            "identity": identity, 
            "port": self.config.get("SerialPortSetup", "Port").strip(),
            "baudrate": self.config.getint("SerialPortSetup", "BaudRate", 19200),
            "timeout": self.config.getfloat("SerialPortSetup", "TimeOut", 1.0),
            "bytesize": self.config.getint("SerialPortSetup", "ByteSize", 8),
            "parity": self.config.get("SerialPortSetup", "Parity", "N"),
            "stopbits": self.config.getint("SerialPortSetup", "StopBits", 1)}
        if simulation:
            self.get_simulation_params()
            self.data_thread = threading.Thread(target=self.simulate_data)
            self.data_thread.daemon = True
            self.data_thread.start()
        else:
            self.source = self.config.get("Main", "Source")
            self.data_thread = Listener.Listener(None,
                                        SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                        StringPickler.ArbitraryObject,
                                        self._streamFilter,
                                        retry = True,
                                        name = APP_NAME)
        self.control_thread = threading.Thread(target=self.controller)
        self.control_thread.daemon = True
        
    def get_value(self, name):
        if name in self.variable_params:
            d = self.variable_params[name]
            reg = d["register"]
            addr = d["address"]
            if reg < 2:
                return self.context[0].getValues(reg, addr, 1)[0]
            else:
                bit = d["bit"]
                type = d["type"]
                count = bit/16
                values = self.context[0].getValues(reg, addr, count)
                value_str = pack("%s%dH" % (self.endian, count), *values)
                ret = unpack("%s%s" % (self.endian, get_variable_type(bit, type)), value_str)
                return ret[0]
                
    def set_value(self, name, value):
        if name in self.variable_params:
            d = self.variable_params[name]
            reg = d["register"]
            addr = d["address"]
            if reg < 2:
                self.context[0].setValues(reg, addr, value)
            else:
                bit = d["bit"]
                type = d["type"]
                count = bit/16
                value_str = pack("%s%s" % (self.endian, get_variable_type(bit, type)), value)
                value_to_write = list( unpack('%s%dH' % (self.endian, count), str) )
                self.context[0].setValues(reg, addr, value_to_write)       
    
    def get_register_info(self):
        self.register_variables = [{}, {}, {}, {}]
        self.variable_params = {}
        self.endian = ">" if self.config.get("Main", "Endian", "Big").lower() == "big" else "<"
        script_path = self.config.get("Main", "Script", "")
        scriptEnv = {
            "GetValue": self.get_value,
            "SetValue": self.set_value
        }
        if os.path.exists(script_path):
            script = file(script_path, 'r')
            scriptObj = compile(script.read().replace("\r\n","\n"), script_path, 'exec')
            exec scriptObj in scriptEnv
        for s in self.config:
            name = ""
            d = {}
            if s.startswith("Variable_"):
                name = s[9:]
                d["bit"] = self.config.getint(s, "Bit")
                d["type"] = self.config.get(s, "Type")
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
            if name:
                d["name"] = name
                d["address"] = self.config.getint(s, "Address")
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
        for v in variable_list:
            addr += var_size
            if v["address"] != addr:
                raise Exception("Variable address of %s is wrong. Should be %s!" % (v["name"], addr))
            var_size = v["bit"] / 16
        return addr + var_size
        
    def check_bit_address(self, bit_list):
        addr = 0
        for b in bit_list:
            if b["address"] != addr:
                raise Exception("Bit address of %s is wrong. Should be %s!" % (b["name"], addr))
            addr += 1
        return addr
        
    def get_simulation_params(self):
        self.simulation_dict = {}
        for s in self.config:
            if s.startswith("Variable_"):
                self.simulation_dict[s[9:]] = self.config.get("Simulation", s)
        self.simulation_env = {func: getattr(math, func) for func in dir(math) if not func.startswith("__")}
        self.simulation_env.update({'random':  random.random, 'time': time, 'x': 0})
        self.simulation_max_index = self.config.getint('Simulation', 'Max_Index', 100)
    
    def write_readonly_registers(self, value_dict):
        try:
            # write ir variables
            values = [value_dict[v] for v in self.register_variables[INPUT_REGISTER-1]["variables"]]
            if len(values) > 0:
                str = pack(self.register_variables[3]['format'], *values)
                value_to_write = list( unpack('%s%dH' % (self.endian, self.register_variables[3]['size']), str) )
                self.context[0].setValues(INPUT_REGISTER, 0, value_to_write)
                #print "ir=", values
            # write di bits
            values = [value_dict[v] for v in self.register_variables[DISCRETE_INPUT-1]["variables"]]
            if len(values) > 0:
                self.context[0].setValues(DISCRETE_INPUT, 0, values)
                #print "di=", values
        except KeyError:
            pass
        
    def _streamFilter(self, streamOut):
        try:
            if streamOut["source"] == self.source:
                data = streamOut["data"]
                result = self.process_data(data)
                self.write_readonly_registers(result)
        except:
            pass
            
    def process_data(self, data_dict):
        result = {}
        for v in self.readonly_variables:
            if "function" in self.variable_params[v]:
                if "input" in self.variable_params[v]:
                    input = [data_dict[n] for n in self.variable_params[v]["input"]]
                else:
                    input = []
                result[v] = self.variable_params[v]["function"](*input)
            else:
                result[v] = data_dict[v]
        return result
        
    def simulate_data(self):
        data = {}
        while True:
            time.sleep(1)
            for k in self.simulation_dict:
                data[k] = self.run_simulation_expression(self.simulation_dict[k])
            result = self.process_data(data)
            self.write_readonly_registers(result)
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
        """
        Periodically read coil. If a bit is set to 1, execute corresponding function.
        After execution, set all bits to 0 
        
        Note: functions are executed sequentially and controller waits until all functions 
        are finished before proceeding. If a function takes long time to finish, user need
        to start a new thread in python script.
        """
        bits_to_read = self.register_variables[COIL-1]['size']
        while True:
            time.sleep(1)
            result = self.context[0].getValues(COIL, 0, bits_to_read)
            print "co=", result
            for bit, variable in zip(result, self.register_variables[COIL-1]['variables']):
                if bit: # execute predefined function if the bit is set
                    if "function" in self.variable_params[variable]:
                        ret = self.variable_params[variable]["function"]()
            if sum(result) > 0:
                self.context[0].setValues(COIL, 0, [0]*bits_to_read)
        
    def run(self):
        self.control_thread.start()
        StartSerialServer(**self.serverConfig)
        
HELP_STRING = """ModbusServer.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./ModbusServer.ini"
-s                   simulation mode
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:s'
    longOpts = ["help"]
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
    configFile = os.path.dirname(AppPath) + "/ModbusServer.ini"
    simulation = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options:
        simulation = True
    return (configFile, simulation)

if __name__ == "__main__":
    server = ModbusServer(*handleCommandSwitches())
    server.run()