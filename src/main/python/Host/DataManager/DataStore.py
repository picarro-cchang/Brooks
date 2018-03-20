
import Queue
import time
import collections
from PyQt4 import QtCore
from Host.Common import Listener, StringPickler
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER
from Host.Common import GraphPanel

"""
DataStoreForGraphPanels
DataStoreForGraphPanels is a class to collect data broadcasted by the DataManager.
Data are stored in GraphPanel Sequences which are like Python Queues.
DataStoreForGraphPanels should be instantiated by each process that wants to 
display time series data with the wxPython based GraphPanel.

Call getQueuedData() periodically to load sequences with data.
getDataSequence() returns a sequence for plotting.
"""
class DataStoreForGraphPanels(object):
    """
    Holds the data queried by AlarmViewListCtrl to update the alarm LEDs and names.
    """
    def __init__(self,config = None):
        self.INDEX = 0 # RSF
        self.config = None
        self.seqPoints = 500
        if config:
            self.config = config
            self.loadConfig()
        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue,
                                          BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject,
                                          retry = True)
        self.sourceDict = {}
        self.oldData = {}
        self.alarmStatus = 0
        self.mode = ""

    def loadConfig(self):
        self.seqPoints = self.config.getint('DataManagerStream','Points')

    def getQueuedData(self):
        """
        Get data from a queue.  The queue'd data is captured from the DataManager broadcast.
        The format is a dict of dicts.
        The top level dict keys are "data", "good", "mode", "source", "time", and "ver". See
        the MeasData.py wrapper class.

        good - True or 0.  Does this flag "measurement mode"?
        mode - warming_mode, CFADS_mode, etc. (Don't know where the definitions are nor how the
                value is set.
        source - sensors, analyze_CFADS.  Appears to contain a DataManager script name when there
                is a valid measurement.
        time - Unix timestamp. Source of timestamp...???
        ver - ???

        The value associated with the "data" key is a dict of hardware readings, fit parameters,
        and gas concentrations from DataManager.  For example. obj["data"]["CO2"] contains
        the CO2 gas concentration.

        What is happening below is not obvious.  To plot the data in a time series, we need several
        hundreds of points per data stream.  As there are at least several 10's of steams that can be
        selected for plotting we would have to push a lot of data through the RPC pipe if the QuickGui
        had to get all that data for each plot update.

        The data is collected in self.sourceDict and self.oldData.  When working with self.sourceDict
        it is bound to 'd'.

            d = self.sourceDict[source]

        When starting out self.sourceDict is empty so we initialize it with ring buffers n elements long.

            d[k] = GraphPanel.Sequence(n)

        Yes, Sequence is a ring buffer, not a Python sequence.
        As new data comes in, it is pushed, or added, to the ring buffer if it's not full, or overwrites
        an old value if we have reached capacity.

            d[k].Add(obj['data'][k])

        GetPointers() return the indicies of where the next data is added.  We track the pointers outside
        of the Sequence class so that we can advance the indices of ring buffers that don't receive new
        data in the current update event.  This is necessary keep all data on the same time axis range
        in the plots.
        """
        n = self.seqPoints
        while True:
            try:
                obj = self.queue.get_nowait()
                if "mode" in obj:
                    self.mode = obj["mode"]
                    #print("mode", self.mode)
                if "data" in obj and "ALARM_STATUS" in obj["data"]:
                    # diagnostics
                    #pprint.pprint(obj)
                    #time.sleep(1000)
                    self.alarmStatus = obj["data"]["ALARM_STATUS"]
                source = obj['source']
                if source not in self.oldData:
                    self.oldData[source] = {}

                if source not in self.sourceDict:
                    self.sourceDict[source] = {}
                    d = self.sourceDict[source]
                    d['good'] = GraphPanel.Sequence(n)
                    d['time'] = GraphPanel.Sequence(n)
                    for k in obj['data']:
                        d[k] = GraphPanel.Sequence(n)
                else:
                    d = self.sourceDict[source]
                # Find where new data have to be placed in the sequence
                cptrs = d['time'].GetPointers()
                for k in d:
                    try:
                        if k in ('time','good'):
                            d[k].Add(obj[k])
                        else:
                            d[k].Add(obj['data'][k])
                    except KeyError:
                        if k in self.oldData[source]:
                            d[k].Add(self.oldData[source][k].GetLatest())
                        else:
                            d[k].Add(0)
                for k in obj['data']:
                    if k not in d:
                        d[k] = GraphPanel.Sequence(n)
                        d[k].SetPointers(cptrs)
                        d[k].Add(obj['data'][k])
                self.oldData[source].update(d)
                time.sleep(0)
            except Queue.Empty:
                return

    def getSources(self):
        return sorted(self.sourceDict.keys())

    def getTime(self,source):
        return self.sourceDict[source]['time']

    def getKeys(self,source):
        return self.sourceDict[source].keys()

    def getDataSequence(self,source,key):
        try:
            return self.sourceDict[source][key]
        except:
            return None

# DataStoreForQt is like DataStoreForGraphPanels but it eliminates the ties with wxPython and also simplifies how
# data is stored and retrieved by using Python Deques (double ended queues).
# With a deque set to a fixed size data is pushed on to one end and pops out the other end as you add more data.
# This keeps the memory consumption constant.
# The intent here is to make it easier to get the data for display on a revamp GUI using Qt.
#
# More on how the data is stored and retrieved TBD.
# Additional convenience access methods TBD.
#
# Note that much of the exception handling with "pass" are done intentionally to keep errors silent.  This
# is necessary as the incoming data is not a constant form and keys you know to exist might not be there
# each and every time an update of the data is invoked. --poor design I know but that is what we have been given--
#
# Here is a very basic program that shows how to get a grow list of data out every second.  To use it, put in
# a *.py file and run it AFTER the DataManager of the Host has started up when running the Host code (same as when
# you start the QuickGui).  When this is code is running it will intercept broadcasts from the DataManager and
# display the received data in a terminal.
#
# -8< --------------------------------------------------------------------------------------------------------------
# import sys
# sys.path.append("/home/picarro/git/host/src/main/python")
# import time
# from Host.DataManager.DataStore import DataStoreForQt
#
# class GetDataApp():
#     def __init__(self):
#         self.ds = DataStoreForQt()
#         self.wantSensorsStream = False
#         return
#
#     def run(self):
#         print("Checking for new data a one second intervals")
#         while True:
#             self.ds.getQueuedData()
#             try:
#                 if self.wantSensorsStream:
#                     timeList = self.ds.getList("Sensors","time")
#                     pressureList = self.ds.getList("Sensors", "CavityPressure")
#                     print("Time:",timeList)
#                     print("Pressure:",pressureList)
#                 else:
#                     timeList = self.ds.getList("analyze_H2O2","time")
#                     h2o2List = self.ds.getList("analyze_H2O2", "H2O2")
#                     print("Time:",timeList)
#                     print("[H2O2]:",h2o2List)
#             except:
#                 pass
#             time.sleep(1)
#         return
#
# if __name__ == "__main__":
#     app = GetDataApp()
#     app.run()
#     exit()


class DataStoreForQt(QtCore.QObject):
    def __init__(self, config = None):
        super(DataStoreForQt, self).__init__()
        self.INDEX = 0 # RSF
        self.config = None
        self.length = 500
        if config:
            self.config = config
            self.loadConfig()
        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue,
                                          BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject,
                                          retry = True)
        self.sourceDict = {}
        self.oldData = {}
        self.offsets = {}   # For simulations
        self.alarmStatus = 0
        self.mode = ""
        return

    @QtCore.pyqtSlot()
    def run(self):
        """
        Run continuously grabbing data a storing the n'th most recent values.
        :return:
        """
        while True:
            self.getQueuedData()
            time.sleep(0.1)
        return

    def getQueuedData(self):
        """

        :return: Number of elements grabbed out of the queue. Returns 0 if no update to the data.
        """
        i = 0
        update = False
        while self.listener.isAlive() and not self.queue.empty():
            try:
                obj = self.queue.get_nowait()
                source = obj["source"]
                if source not in self.sourceDict:
                    self.sourceDict[source] = {}
                for key in obj.keys():
                    # This eliminates storing duplicate data streams like 'time'.  Here the 'time' key
                    # is a primary key at the same level as the 'data' key and 'time' is also a key
                    # in 'data'.  This passes over the primary key if it also appears in 'data'.
                    if "data" in obj.keys() and key in obj["data"].keys():
                        continue
                    # The dict in 'data' is variable.  About 1:5 to 1:10 instances do not contain any
                    # fit results.  Don't know why.  The 'ngroups' key is a product of the fit so skip
                    # any results that don't have fit data.
                    if 'ngroups' not in obj["data"].keys():
                        continue
                    if "data" in key:
                        for dataKey in obj["data"].keys():
                            if dataKey not in self.sourceDict[source]:
                                self.sourceDict[source][dataKey] = collections.deque([], self.length)
                            offset = 0.0
                            if dataKey in self.offsets:
                                offset = float(self.offsets[dataKey])
                            self.sourceDict[source][dataKey].append(obj["data"][dataKey] + offset)
                            update = True
                    else:
                        if key not in self.sourceDict[source].keys():
                            self.sourceDict[source][key] = collections.deque([], self.length)
                        self.sourceDict[source][key].append(obj[key])
                        update = True
                if update:
                    i += 1
                    update = False
            except Exception as e:
                print("Unhandled exception in DataStore.py: %s" %e)
        return i

    def getList(self, source, key):
        """
        Return the data in one of the data deques as a python list.
        :param source: Typically "Sensors" or "analyze_<molecule>" like "analyze_H2O2"
        :param key: A like like "time", "CavityPressure", or "H2O2"
        :return: A list of floating point numbers. Data at index 0 are the oldest data, index -1 the newest.
        """
        try:
            return list(self.sourceDict[source][key])
        except Exception as e:
            print("getList exception:",e)
            return None

    def setOffset(self, key, offset):
        self.offsets[key] = offset
        return




