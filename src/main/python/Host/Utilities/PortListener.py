import os
import sys
import getopt
import time
from Host.Common import StringPickler, Listener
from Host.autogen import interface

class PortListerner(object):
    def __init__(self, port):
        if port is not None:
            self.port = int(port)
            if self.port == 40020:
                dataType = interface.SensorEntryType
                self.streamFilterState = "COLLECTING_DATA"
                self.resultDict = {}
                self.latestDict = {}
                self.lastTime = 0
            elif self.port == 40030:
                dataType = interface.RingdownEntryType
            elif self.port == 40031:
                dataType = interface.ProcessedRingdownEntryType
            else:
                dataType = StringPickler.ArbitraryObject
            self.listener = Listener.Listener(None,
                                             self.port,
                                             dataType,
                                             self._streamFilter,
                                             retry = True,
                                             name = "Port listener")
                                             
    def run(self):
        while True:
            time.sleep(0.1)
            
    def _streamFilter(self, streamOut):
        try:
            if self.port == 40020:
                self.sensorStreamFilter(streamOut)
            else:
                print streamOut
                print
        except:
            pass
            
    def sensorStreamFilter(self, result):
        self.latestDict[interface.STREAM_MemberTypeDict[result.streamNum][7:]] = result.value

        if self.streamFilterState == "RETURNED_RESULT":
            self.lastTime = self.cachedResult.timestamp
            self.resultDict = {interface.STREAM_MemberTypeDict[self.cachedResult.streamNum][7:] : self.cachedResult.value}

        if result.timestamp != self.lastTime:
            self.cachedResult = interface.SensorEntryType(result.timestamp,result.streamNum,result.value)
            self.streamFilterState = "RETURNED_RESULT"
            if self.resultDict:
                print self.lastTime, self.resultDict
        else:
            self.resultDict[interface.STREAM_MemberTypeDict[result.streamNum][7:]] = result.value
            self.streamFilterState = "COLLECTING_DATA"

HELP_STRING = \
"""\
PortListerner.py [-h] [-p<PortNum>]

Where the options can be a combination of the following:
-h  Print this help.
-p  Number of the broadcast port

"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    
    shortOpts = 'hp:'
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

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit(0)

    port = None
    if "-p" in options:
        port = options["-p"]

    return port

def main():
    port = HandleCommandSwitches()
    pl = PortListerner(port)
    pl.run()
    
if __name__ == "__main__":
    main()
