"""
Copyright 2014, Picarro Inc.
"""

import calendar
import time
import sys
import os
import zmq
import json

import Queue
from Host.Common import Listener
from Host.Common import SharedTypes
from Host.Common import StringPickler
from Host.Common import AppStatus
from Host.Common import EventManagerProxy as EventManager
from Host.Common.CustomConfigObj import CustomConfigObj

EventManager.EventManagerProxy_Init('DataManagerPublisher')

class DataManagerPublisher(object):

    def __init__(self, configFile):
        if os.path.exists(configFile):
            print "Configuration file is loaded from %s" % configFile
            config = CustomConfigObj(configFile)
            self.measurement_source = config.get("Main", "Measurement_Source")
            self.measurement_mode = config.get("Main", "Measurement_Mode")
            self.debug = config.getboolean("Main", "Debug_Mode")
        else:
            print "Configuration file not found %s" % configFile
            sys.exit(1)
        self.context = zmq.Context()

        self.broadcastSocket = self.context.socket(zmq.PUB)
        self.broadcastSocket.bind("tcp://127.0.0.1:%d" % SharedTypes.TCP_PORT_DATAMANAGER_ZMQ_PUB)

        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue, SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject,
                                          streamFilter=self.jsonifyMeasurements, retry=True)
        #self.instrumentStatusListener = Listener.Listener(self.queue, SharedTypes.STATUS_PORT_INST_MANAGER,
        #                                                  AppStatus.STREAM_Status,
        #                                                  streamFilter=self.jsonifyStatus, retry=True)

    def run(self):
        try:
            while True:
                msg = self.queue.get()
                self.broadcastSocket.send_string("%s" % msg)
        finally:
            self.broadcastSocket.close()
            self.context.term()
            self.listener.stop()

    def jsonifyMeasurements(self, entry):
        if self.debug:
            print entry
            print "----------------------------------------"
        source = entry['source']
        if source == 'Sensors' or source == self.measurement_source:
            if 'species' in entry['data'] and (entry['data']['species'] == 0.0 or entry['data']['species'] == "0.0"):
                print "Rejected species 0"
                return None
            elif source == 'Sensors' and entry['mode'] == self.measurement_mode:
                # block these data during the measurement, otherwise non-cavity parameters will be treated as 0 by surveyor programs
                # CH4 and flow values shown on tablet will jump between 0 and normal reading.
                return None
            return json.dumps({'type': 'measurement', 'mode': entry['mode'], 'data': entry['data']})
        elif source == 'parseGPS' or source == 'parseGillAnemometer':
            entry['data']['EPOCH_TIME'] = entry['time']
            return json.dumps({'type': 'gps' if source == 'parseGPS' else 'anemometer', 'data': entry['data']})
        else:
            #print "Skip %s" % entry['source']
            return None

    def jsonifyStatus(self, entry):
        # Status messages do not contain timestamps!
        epochTime = calendar.timegm(time.gmtime())

        if self.lastInstrumentStatus == entry.status:
            return None

        result = json.dumps({'type': 'inst_status', 'data': {'timestamp': epochTime, 'status': entry.status}})
        print result
        self.lastInstrumentStatus = entry.status
        return result

HELP_STRING = \
"""\
DataManagerPublisher.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./DataManagerPublisher.ini"
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    executeTest = False
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit(0)
    
    #Start with option defaults...
    configFile = "DataManagerPublisher.ini"

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile
    
if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    pub = DataManagerPublisher(configFile)
    pub.run()
