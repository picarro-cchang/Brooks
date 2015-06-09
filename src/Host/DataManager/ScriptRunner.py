#!/usr/bin/python
#
# File Name: ScriptRunner.py
# Purpose:
#   Contains the code for running dynamic scripts in the prepared environment
#   suitable for CRDS DataManager scripts.
#
# Notes:
#
# ToDo:
#
# File History:
# 06-12-15 russ  First real release
# 06-12-21 russ  Script name override; Logging of script exceptions
# 09-01-21 alex  Added pulse analyzer
# 11-04-11 sze   Added _GLOBALS_ for information to be shared between all data manager scripts
# 11-04-13 sze   Add Synchronizer class and _SYNC_OUT_ function to support multiple data-driven
#                 resynchronization processes

from Host.DataManager import DataSynchronizer
from Host.Common import timestamp
from Host.Common import DoAdjustTempOffset
import string

#Input prefix definitions
SOURCE_TIME_ID = "_MEAS_TIME_"
SOURCE_TIMESTAMP_ID = "_MEAS_TIMESTAMP_"
DATA_ID = "_DATA_"
INSTR_ID = "_INSTR_"
SENSOR_ID = "_SENSORS_"
OLD_DATA_ID = "_OLD_DATA_"
OLD_REPORTS_ID = "_OLD_REPORT_"
OLD_SENSORS_ID = "_OLD_SENSOR_"
DRIVER_RPC_SERVER_ID = "_DRIVER_"
MEAS_SYS_RPC_SERVER_ID = "_MEAS_SYS_" # provides tagalong data calls
FREQ_CONV_RPC_SERVER_ID = "_FREQ_CONV_" # provides getWlmOffset and setWlmOffset calls
SPEC_COLL_RPC_SERVER_ID = "_SPEC_COLL_" # provides getSequenceNames and setSequence calls
DATA_LOGGER_RPC_SERVER_ID = "_DATA_LOGGER_" # provides DATALOGGER_stopLogRpc and DATALOGGER_startLogRpc calls
PERIPH_INTRF_ID = "_PERIPH_INTRF_"
PERIPH_INTRF_COLS_ID = "_PERIPH_INTRF_COLS_"
NEW_DATA_ID = "_NEW_DATA_"
SCRIPT_ARGS_ID = "_ARGS_"
INSTR_STATUS_ID = "_INSTR_STATUS_"
SERIAL_INTERFACE_ID = "_SERIAL_"
USER_CAL_ID = "_USER_CAL_"
UTILS_ID = "_UTILS_"


# Synchronizer output function name...
SYNC_OUT_ID = "_SYNC_OUT_"

#Output prefix definitions...
REPORT_ID = "_REPORT_"
FORWARD_ID = "_ANALYZE_"
MEAS_GOOD_ID = "_MEAS_GOOD_"
SCRIPT_NAME_ID = "_SCRIPT_NAME_"

OPTIONS_ID = "_OPTIONS_"

persistentDict = {}
globals = {}

class Synchronizer(object):
    def __init__(self,analyzer,varList=[],syncInterval=100,syncLatency=500,processInterval=500,maxDelay=2000):
        if "synchronizer" not in globals: globals["synchronizer"] = {}
        if analyzer in globals["synchronizer"]:
            raise ValueError("Synchronizer %s already exists" % analyzer)
        globals["synchronizer"][analyzer] = dict(varList=varList,syncInterval=syncInterval,
                                                 syncLatency=syncLatency,processInterval=processInterval,maxDelay=maxDelay)
        self.analyzer = analyzer
        self.processInterval = processInterval
        self.lastTimestamp = None

    def dispatch(self,timestamp,forwarder):
        if self.lastTimestamp == None or (timestamp - self.lastTimestamp)>self.processInterval:
            forwarder[self.analyzer] = dict(timestamp=timestamp)
            self.lastTimestamp = timestamp

class NewDataDict(dict):
    """Class to allow new data in the script to be managed like a dict, but
    restricted in what keys can be added by the OldDataDict.

    """
    def __init__(self, OldDataDict):
        dict.__init__(self)
        self._OldData = OldDataDict
    def __setitem__(self, key, value):
        if key in self._OldData:
            raise Exception("Key already exists in old data!  New data keys must be new.")
        return dict.__setitem__(self, key, value)

def RunAnalysisScript(ScriptCodeObj,
                      ScriptArgs,
                      SourceTime_s,
                      DataDict,
                      InstrDataDict,
                      SensorDataDict,
                      DataHistory,
                      ReportHistory,
                      SensorHistory,
                      DriverRpcServer,
                      InstrumentStatus,
                      MeasSysRpcServer,
                      FreqConvRpcServer,
                      SpecCollRpcServer,
                      DataLoggerRpcServer,
                      PeriphIntrfFunc,
                      PeriphIntrfCols,
                      SerialInterface,
                      ScriptName,
                      ExcLogFunc,
                      UserCalDict,
                      CalEnabled = True,
                      PulseAnalyzerIni = None,
                      Options = ""):
    """Executes the CodeObj in an environment built with the other parameters.

    Returns a tuple: (ReportedData, ForwardedData, NewData, MeasGood, ScriptName)
      - ReportedData = dict of values added with REPORT_ID
      - ForwardedData = dict of what should be added to the incoming to-be-analyzed
                        queue.  It is a dict of dicts, with the first key being the
                        label to trigger analysis.  Done with FORWARD_ID.
      - NewData = dict of new data added to the incoming data set with NEW_DATA_ID.
      - MeasGood = A boolean that defaults to True but can be overridden in the
                   script with _MEAS_GOOD_
      - ScriptName = The name to use to label the MeasData packet that contains
                     the ReportedData.  This defaults to the value passed in, but
                     can be overriden in the script.

    Collecting the data history is the responsibility of the caller.  It is expected that OldDataDict
    will be a dict of lists, where the list is of two-tuples (timestamp, value).

    Script usage examples for old data would be:

    OLD["H2S"][-10].time  -> gets the timestamp of the H2S data from 10 points ago
    OLD["H2S"][-10].value -> gets the value of the H2S data from 10 points ago

    _old_H2S[-10][0] -> gets the timestamp of the H2S data from 10 points ago
    _old_H2S[-10][1] -> gets the value of the H2S data from 10 points ago

    Went with _DATA_["NAME"] rather than adding a suite of variables like
    _data_NAME to the data environment so that the script can work with the
    dictionaries, rather than a bunch of single variables.

    """
    global persistentDict, globals

    #need to support inputs (given to the script):
    # - cal data from provided files (INSTR_DATA)
    # - all data from meas system    (DATA)
    # - meas data history            (OLD_DATA list)
    # - old report history           (OLD_REPORT)
    # - old forward history          (OLD_FORWARD)
    #need to support outputs (collected from the script):
    # - data to be broadcasted       (REPORT)
    # - data to be fed forward       (FORWARD_xxx)
    #also need to provide
    # - portal for making Driver calls    (_DRIVER_RPC as CmdFIFOServerProxy)
    #Set up the dictionaries for use in the script environment...
    # - providing copies to make sure the script doesn't screw the data up

    if ScriptName not in persistentDict:
        persistentDict[ScriptName] = {"init": True}
    dataEnviron = {"_GLOBALS_" : globals, "_PERSISTENT_" : persistentDict[ScriptName], "Synchronizer" : Synchronizer }

    dataEnviron[SOURCE_TIME_ID] = SourceTime_s
    dataEnviron[SOURCE_TIMESTAMP_ID] = timestamp.unixTimeToTimestamp(SourceTime_s)
    dataEnviron[DATA_ID] = DataDict.copy()
    dataEnviron[DATA_ID].update({"cal_enabled":CalEnabled})
    dataEnviron[INSTR_ID] = InstrDataDict.copy()
    dataEnviron[SENSOR_ID] = SensorDataDict.copy()
    dataEnviron[OLD_DATA_ID] = DataHistory.copy()
    dataEnviron[OLD_REPORTS_ID] = ReportHistory.copy()
    dataEnviron[OLD_SENSORS_ID] = SensorHistory.copy()
    dataEnviron[REPORT_ID] = {}
    dataEnviron[FORWARD_ID] = {}
    dataEnviron[DRIVER_RPC_SERVER_ID] = DriverRpcServer
    dataEnviron[MEAS_SYS_RPC_SERVER_ID] = MeasSysRpcServer
    dataEnviron[FREQ_CONV_RPC_SERVER_ID] = FreqConvRpcServer
    dataEnviron[SPEC_COLL_RPC_SERVER_ID] = SpecCollRpcServer
    dataEnviron[DATA_LOGGER_RPC_SERVER_ID] = DataLoggerRpcServer
    dataEnviron[PERIPH_INTRF_ID] = PeriphIntrfFunc
    dataEnviron[PERIPH_INTRF_COLS_ID] = PeriphIntrfCols
    dataEnviron[NEW_DATA_ID] = NewDataDict(dataEnviron[DATA_ID])
    dataEnviron[SCRIPT_ARGS_ID] = tuple(ScriptArgs)
    dataEnviron[MEAS_GOOD_ID] = True #script guy has to consciously make it false
    dataEnviron[INSTR_STATUS_ID] = InstrumentStatus
    dataEnviron[SCRIPT_NAME_ID] = ScriptName
    dataEnviron[SERIAL_INTERFACE_ID] = SerialInterface
    dataEnviron[USER_CAL_ID] = UserCalDict.copy()
    dataEnviron[OPTIONS_ID] = Options

    # Put the functions we want to expose to runtime scripts in a dictionary
    # For now we are exposing functions by name. If there are any conflicts,
    # using a dictionary gives future flexibility to expose them as a
    # nested dictionary by module name.
    #
    # Warning: Do not remove existing dictionary keys that are function names
    #          or you may break existing scripts!
    dataEnviron[UTILS_ID] = { "doAdjustTempOffset": DoAdjustTempOffset.doAdjustTempOffset }

    ##Now set up the direct variables (couldn't decide which one was best, so both!)...
    #for k in DataDict.keys():
        #dataEnviron["%s%s" % (DATA_ID, k)] = DataDict[k]
    #for k in InstrDataDict.keys():
        #dataEnviron["%s%s" % (INSTR_ID, k)] = InstrDataDict[k]
    #for k in OldDataDict.keys():
        #dataEnviron["%s%s" % (OLD_DATA_ID, k)] = OldDataDict[k]

    def synchronizer(analyzer):
        return DataSynchronizer.resync(analyzer,dataEnviron)

    dataEnviron.update({SYNC_OUT_ID : synchronizer})

    try:
        exec ScriptCodeObj in dataEnviron
    except Exception, excData:
        ExcLogFunc("UNHANDLED EXCEPTION IN ANALYSIS SCRIPT")
        if __debug__: print "SCRIPT EXCEPTION: %s %r" % (excData, excData)
        raise

    persistentDict[ScriptName] = dataEnviron["_PERSISTENT_"]

    #Now check for magic keywords created by the script...
    reportedData = dataEnviron[REPORT_ID]
    forwardedData = dataEnviron[FORWARD_ID]
    newData = dataEnviron[NEW_DATA_ID]
    measGood = dataEnviron[MEAS_GOOD_ID]
    scriptName = dataEnviron[SCRIPT_NAME_ID]
    # Calculate the latency from source time to data manager completion time and report
    #  maximum fitter latency
    if reportedData:
        reportedData["dm_latency"] = timestamp.unixTime(timestamp.getTimestamp()) - SourceTime_s
        if "max_fitter_latency" in DataDict:
          reportedData["max_fitter_latency"] = DataDict["max_fitter_latency"]
    return (reportedData, forwardedData, newData, measGood, scriptName)