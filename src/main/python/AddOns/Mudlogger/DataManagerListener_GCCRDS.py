import Queue
import Listener
import StringPickler
import time

class DataManagerListener(object):
    ### class object that is used to collect and filter data
    def __init__(self):
        self.BROADCAST_PORT_DATA_MANAGER = 40060
        ### max queue size is roughly 1.5 hours at 2 Hz
        self.queue = Queue.Queue(10000)
        self.listener = Listener.Listener(self.queue, self.BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject, 
                                          streamFilter=self.dataFilter,
                                          retry = True, logFunc = self.logFunc)
    def logFunc(self, msg):
        ### defines Lister
        msg = "Listener %s: %s" % (time.ctime(time.time),msg)
        print msg
                                          
    def dataFilter(self, rawData):
        goodKeys = ['CO2_dry', 'Delta13C', 'CH4']
        if 'analyze_iCO2_lct' == rawData['source']:
            dataDict = rawData['data']
            goodData = {key:dataDict[key] for key in dataDict if key in goodKeys}
            goodData['time'] = rawData['time']
            return goodData
            
    def clear(self, queue):
        while True:
            try:
                queue.get(False)
            except Queue.Empty:
                break