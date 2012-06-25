import Queue
import time
from cPickle import dumps
from struct import pack
from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.Listener import Listener
from Host.Common.InstErrors import INST_ERROR_DATA_MANAGER
from Host.Common import AppStatus

def Log(msg):
    print msg
    
class DataManagerOutput(object):
    def __init__(self):
        self.dmQueue = Queue.Queue(0)
        
    def listen(self):
        self.dmListener = Listener(self.dmQueue,
                                    BROADCAST_PORT_DATA_MANAGER,
                                    StringPickler.ArbitraryObject,
                                    retry = True,
                                    name = "DataManagerOutput Listener",
                                    logFunc = Log)
    def run(self):
        while True:
            while not self.dmQueue.empty():
                output = self.dmQueue.get()
                if output['source'] == 'analyze_CFADS':
                    print  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(output["data"]["time"])), output["data"]["CO2"], output["data"]["CH4"], output["data"]["H2O"]
            time.sleep(1)
    
    def getOutput(self,maxWait=10):
        return self.dmQueue.get(1,maxWait)
        
    def stop(self):
        self.dmListener.stop()
        
if __name__ == "__main__":
    dm = DataManagerOutput()
    dm.listen()
    dm.run()
    