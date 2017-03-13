import sys,time,os
import math
import serial
import getopt
from Host.Common.CustomConfigObj import CustomConfigObj
import threading
from itertools import chain

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
APP_NAME = "4to20Server"

class Four220Server(object):
    def __init__(self, configFile, simulation):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            raise Exception("Configuration file not found: %s" % configFile)
        
        if simulation:
            self.data_thread = threading.Thread(target=self.simulate_data)
            self.data_thread.daemon = True
            self.data_thread.start()
        else:
            print "not in simulation mode."
            pass
        
            
    def simulate_data(self):
        self.simulation_env = {}
        self.simulation_env['is_logScale'] = self.config.getboolean('Simulation', 'LogScale')
        self.simulation_env['data_min'] = self.config.getfloat('Simulation', 'Min')
        self.simulation_env['data_max'] = self.config.getfloat('Simulation', 'Max')
        x = 0.0
        if self.simulation_env['is_logScale']:
            print "Concentration Simulation in LogScale..."
            points = (0.0001*i*10**exp for exp in range(1,7) for i in range(1,10))
            sample_points = chain(points, (i*100 for i in range(9,21)))
            while True:
                try:
                    data = sample_points.next()
                    print "simulated concentration: ", data, 'ppb'
                    try:
                        self.data_processor(data)
                    except:
                        print "Can not send to serial port."
                except:
                    print "End of simulated sample points."
                    break
                time.sleep(5)
        else:
            for i in range(1001):
                data = i 
                print "simulated concentration: ", i, 'ppb'
                self.data_processor(data)
        
        
    def data_processor(self, data):
        self.slope = self.config.getfloat('Channel1', 'SLOPE')
        self.offset = self.config.getfloat('Channel1', 'OFFSET')

        cur = float(self.slope * math.log(data,10) + self.offset)
        try:
            ser = serial.Serial('COM3')
        except:
            print "Can not connect to COM3 port."
        if cur < 10.0:
            cur_str = '0'+ format(cur, '.3f')
        else:
            cur_str = format(cur, '.3f')
        cmd_str = '#010+' + cur_str
        try:
            ser.write(cmd_str + '\r')
            ser.close()
            print "Write current %f to serial port COM3."%cur
            print "Write cur_str", cmd_str
        except:
            "Failed to write to serial port."
        
        
        
    def run(self):
        while True:
            time.sleep(10)
        
        
        
        
        
HELP_STRING = """Four220Server.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./4to20Server.ini"
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
    configFile = os.path.dirname(AppPath) + "\\4to20Server.ini"
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
    server = Four220Server(*handleCommandSwitches())
    server.run()