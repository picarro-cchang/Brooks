#!/usr/bin/python
#
# File Name: MeasData.py
# Purpose:
#
#   Defines the class for tossing data bundles around between CRDS
#   applications. This is primarily for data provided by DataManager to the
#   apps in the user layer, but can be used elsewhere.
#
# Notes:
#
# ToDo:
#
# File History:
# 06-11-xx russ  First release
# 06-12-15 russ  Added MeasGood
# 06-12-19 russ  Fixed/improved version handling
# 08-03-07 sze   Convert data in MeasData object to floats to avoid issues with pickling numpy output

import StringPickler

class IncompatibleMeasDataPickleVer(Exception): pass
class InvalidMeasDataPickle(Exception): pass

class MeasData(object):
    ver = 3  # Version of the MeasData data structure
    def __init__(self, DataSource = "", DataTimeStamp_s = -1, Data = {}, MeasGood = True, Mode = ""):
        self.Source = DataSource            # A string (eg: script name)
        self.Time = DataTimeStamp_s         # Time in seconds since epoch (internal HostCore time standard)
                                            #   - epoch is the unix one... the start of 1970 (Midnight Dec 31 1969)
        self.MeasGood = MeasGood
        self.Mode = Mode                    # Current data manager mode (measurement mode or warming mode)
        self.Data = {}                      # Keys = data names, Values = data values
                                            #  - may have values as two-tuples with (value, timestamp) later.
        if Data:
            for key in Data:
                try:
                    self.Data[key] = float(Data[key])
                except:
                    self.Data[key] = Data[key]

    def dumps(self):
        dumpDict = {}
        dumpDict["ver"] = self.ver
        dumpDict["source"] = self.Source
        dumpDict["time"] = self.Time
        dumpDict["good"] = self.MeasGood
        dumpDict["data"] = self.Data
        dumpDict["mode"] = self.Mode
        pickle = StringPickler.PackArbitraryObject(dumpDict)
        return pickle

    def ImportPickleDict(self, PickleDict):
        """Translates the pickled/transmitted PickleDict into this MeasData instance.

        MeasData is bundled into a standard dictionary when pickled for
        transmission (more efficient and flexible). This routine unpacks from this
        dict form into an actual MeasData object (self).

        """
        try:
            if PickleDict["ver"] != self.ver:
                raise IncompatibleMeasDataPickleVer
            self.Source = PickleDict["source"]
            self.Time = PickleDict["time"]
            self.MeasGood = PickleDict["good"]
            self.Mode = PickleDict["mode"]
            self.Data = PickleDict["data"].copy()
        except IncompatibleMeasDataPickleVer:
            raise
        except:
            raise InvalidMeasDataPickle

    def __str__(self):
        ret = "Source = %10s; Time = %10.3f; Good = %s; Mode = %s; Data = %r" % (self.Source, self.Time, self.MeasGood, self.Mode, self.Data)
        return ret

if __name__ == "__main__":
    import Broadcaster
    import SharedTypes
    import random
    import time

    print "Executing test code for MeasData.py"
    #bc = Broadcaster.Broadcaster(SharedTypes.BROADCAST_PORT_DATA_MANAGER, "Test")
    bc = Broadcaster.Broadcaster(50001, "Test") #50001 so I can use Test-ArbListen

    sourceOptions = ["Source_A", "Source_B", "Source_C"]

    bogusSourceDef = dict(Source_A = dict(a=0,b=0,c=0),
                          Source_B = dict(x=0,y=0,z=0),
                          Source_C = dict(single_val=0))
    while 1:
        testSource = random.choice(bogusSourceDef.keys())
        testData = MeasData(testSource, time.time())
        for key in bogusSourceDef[testSource].keys():
            testData.Data[key] = random.gauss(0, 1)
        msg = testData.dumps()
        print "Sending %s" % testData
        bc.send(msg)
        time.sleep(0.05)
        unpackedDict = StringPickler.UnPackArbitraryObject(msg)[0]
        unpackedMD = MeasData()
        unpackedMD.ImportPickleDict(unpackedDict)
