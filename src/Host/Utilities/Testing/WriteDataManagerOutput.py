import os
import sys
import time
import Queue
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
    def __init__(self, configFile):
        co = CustomConfigObj(configFile, list_values = True)
        self.source = co.get("Main", "sourcescript")
        self.datalist = co.get("Main", "datalist")
        self.targetDir = co.get("Main", "targetDir", "C:/UserData")
        self.maxLines = co.getint("Main", "maxLines", 500)
        self.dmQueue = Queue.Queue(0)
        self.colWidth = 26
        self.createNewFile()

    def createNewFile(self):
        self.cnt = 0
        filename = "TempDataLog-%s.dat" % (time.strftime("%Y%m%d-%H%M%S",time.localtime()))
        self.filepath = os.path.abspath(os.path.join(self.targetDir, filename))
        print "%s Created" % self.filepath
        self._writeHeader()

    def _writeEntry(self, fp, string):
        fp.write((string[:self.colWidth-1]).ljust(self.colWidth))

    def _writeHeader(self):
        fp = open(self.filepath, "a")
        self._writeEntry(fp, "DATETTIME")
        for dataName in self.datalist:
            self._writeEntry(fp, dataName)
        fp.write("\n")
        fp.close()
        self.cnt += 1

    def _writeData(self, dataDict):
        fp = open(self.filepath, "a")
        self._writeEntry(fp, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dataDict["time"])))
        for data in self.datalist:
            self._writeEntry(fp, "%.10E" % dataDict[data])
        fp.write("\n")
        fp.close()
        self.cnt += 1

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
                    self._writeData(output["data"])
                    if self.cnt > self.maxLines:
                        self.createNewFile()
                    #outlist = [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(output["data"]["time"]))] + [output["data"][c] for c in self.datalist]
                    #print outlist
            time.sleep(1)

def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "c:", [])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    else:
        configFile = ".\WriteDataManagerOutput.ini"

    return configFile

if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    dm = DataManagerOutput(configFile)
    dm.listen()
    dm.run()