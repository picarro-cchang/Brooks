# Get Peripheral Data listens to the output of the data manager and filters out information 
#  which came from the peripherals

import Queue
import threading
import time
import traceback
from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER
from Host.Common.Listener import Listener

def Log(msg):
    print msg
    
class DataManagerOutput(object):
    def __init__(self):
        self.dmQueue = Queue.Queue(0)
        self.gpsQueue = Queue.Queue(100)
        self.wsQueue = Queue.Queue(100)
        self.scriptEnviron = dict(QUEUES=[self.gpsQueue,self.wsQueue])
        self.scriptFile = "periphDataProcessor.py"
        sourceString = file(self.scriptFile,"r").read().strip()
        sourceString = sourceString.replace("\r\n","\n")
        self.scriptCode = compile(sourceString, self.scriptFile, "exec") #providing path accurately allows debugging of script
        
    def listen(self):
        self.dmListener = Listener(self.dmQueue,
                                    BROADCAST_PORT_DATA_MANAGER,
                                    StringPickler.ArbitraryObject,
                                    retry = True,
                                    name = "DataManagerOutput Listener",
                                    logFunc = Log)
                                    
    def runScript(self):
        try:
            exec self.scriptCode in self.scriptEnviron
        except Exception:
            print "Exception in PeriphDataProcessorScript"
            print traceback.format_exc()   
        print "PeriphDataProcessorScript terminated unexpectedly"
        
    def run(self):
        self.scriptThread = threading.Thread(target=self.runScript)
        self.scriptThread.setDaemon(True)
        self.scriptThread.start()
        while True:
            output = self.dmQueue.get()
            if output['source'] == 'parseGPS':
                ts = int(timestamp.unixTimeToTimestamp(output['time']))
                self.gpsQueue.put((ts,output['data']))
            elif output['source'] == 'parseWeatherStation':
                ts = int(timestamp.unixTimeToTimestamp(output['time']))
                self.wsQueue.put((ts,output['data']))

            
    def stop(self):
        self.dmListener.stop()
        
if __name__ == "__main__":
    dm = DataManagerOutput()
    dm.listen()
    dm.run()
    