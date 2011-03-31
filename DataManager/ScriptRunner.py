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

import string

#Input prefix definitions
SOURCE_TIME_ID = "_MEAS_TIME_"
DATA_ID = "_DATA_"
INSTR_ID = "_INSTR_"
SENSOR_ID = "_SENSORS_"
OLD_DATA_ID = "_OLD_DATA_"
OLD_REPORTS_ID = "_OLD_REPORT_"
OLD_SENSORS_ID = "_OLD_SENSOR_"
DRIVER_RPC_SERVER_ID = "_DRIVER_"
MEAS_SYS_RPC_SERVER_ID = "_MEAS_SYS_" # provides tagalong data calls
FREQ_CONV_RPC_SERVER_ID = "_FREQ_CONV_" # provides getWlmOffset and setWlmOffset calls
SENSOR_INTERPOLATOR_ID = "_SENSOR_INTERP_"
NEW_DATA_ID = "_NEW_DATA_"
SCRIPT_ARGS_ID = "_ARGS_"
INSTR_STATUS_ID = "_INSTR_STATUS_"
SERIAL_INTERFACE_ID = "_SERIAL_"
USER_CAL_ID = "_USER_CAL_"

#Output prefix definitions...
REPORT_ID = "_REPORT_"
FORWARD_ID = "_ANALYZE_"
MEAS_GOOD_ID = "_MEAS_GOOD_"
SCRIPT_NAME_ID = "_SCRIPT_NAME_"

persistentDict = {}

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
                      SensorInterpolator,
                      SerialInterface,
                      ScriptName,
                      ExcLogFunc,
                      UserCalDict,
                      CalEnabled = True,
                      PulseAnalyzerIni = None):
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
    global persistentDict
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
        persistentDict[ScriptName] = {"init": True, "pulseData": {}, "status": {}, "pulseAnalyzer": {},
                                      "params": {"allConcList": [], "externalTrigger": {}, "firstDataIn": {}}}    
        thresholdDict = {}
        speciesDict = {}
        if PulseAnalyzerIni != None:
            if "specs" in PulseAnalyzerIni:
                for conc in PulseAnalyzerIni["specs"]:
                    try:
                        parsedValues = string.split(PulseAnalyzerIni["specs"][conc], ',')
                        thresholdDict[conc] = float(parsedValues[0])
                        specValues = parsedValues[1:]
                        for speciesNum in specValues:
                            speciesNum = int(speciesNum)
                            if speciesNum not in speciesDict:
                                speciesDict[speciesNum] = [conc]
                            else:    
                                speciesDict[speciesNum].append(conc)
                        persistentDict[ScriptName]["params"]["allConcList"].append(conc)    
                    except:
                        print "Pulse analyzer for conc %s is skipped - threshold and species are not properly defined" % conc
                        
                if "configInt" in PulseAnalyzerIni:
                    for configKey in PulseAnalyzerIni["configInt"]:
                        persistentDict[ScriptName]["params"][configKey] = int(PulseAnalyzerIni["configInt"][configKey])
                        
                if "configFloat" in PulseAnalyzerIni:
                    for configKey in PulseAnalyzerIni["configFloat"]:
                        persistentDict[ScriptName]["params"][configKey] = float(PulseAnalyzerIni["configFloat"][configKey])
            else:
                print "Not running pulse analyzer for script %s - specifications are not given" % ScriptName
        persistentDict[ScriptName]["params"]["threshold"] = thresholdDict
        persistentDict[ScriptName]["params"]["species"] = speciesDict
        
    dataEnviron = {"_PERSISTENT_" : persistentDict[ScriptName] }
    dataEnviron[SOURCE_TIME_ID] = SourceTime_s
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
    dataEnviron[SENSOR_INTERPOLATOR_ID] = SensorInterpolator
    dataEnviron[NEW_DATA_ID] = NewDataDict(dataEnviron[DATA_ID])
    dataEnviron[SCRIPT_ARGS_ID] = tuple(ScriptArgs)
    dataEnviron[MEAS_GOOD_ID] = True #script guy has to consciously make it false
    dataEnviron[INSTR_STATUS_ID] = InstrumentStatus
    dataEnviron[SCRIPT_NAME_ID] = ScriptName
    dataEnviron[SERIAL_INTERFACE_ID] = SerialInterface
    dataEnviron[USER_CAL_ID] = UserCalDict.copy()
    ##Now set up the direct variables (couldn't decide which one was best, so both!)...
    #for k in DataDict.keys():
        #dataEnviron["%s%s" % (DATA_ID, k)] = DataDict[k]
    #for k in InstrDataDict.keys():
        #dataEnviron["%s%s" % (INSTR_ID, k)] = InstrDataDict[k]
    #for k in OldDataDict.keys():
        #dataEnviron["%s%s" % (OLD_DATA_ID, k)] = OldDataDict[k]
    try:
        exec ScriptCodeObj in dataEnviron
    except Exception, excData:
        ExcLogFunc("UNHANDLED EXCEPTION IN ANALYSIS SCRIPT")
        if __debug__: print "SCRIPT EXCEPTION: %s %r" % (excData, excData)
        raise

    persistentDict[ScriptName] = dataEnviron["_PERSISTENT_"]
    pulseData = persistentDict[ScriptName]["pulseData"]
    pulseStatus = persistentDict[ScriptName]["status"]
    pulseParams = persistentDict[ScriptName]["params"]
    pulseDict = {"data": pulseData, "status": pulseStatus, "params": pulseParams}
    
    #Now check for magic keywords created by the script...
    reportedData = dataEnviron[REPORT_ID]
    forwardedData = dataEnviron[FORWARD_ID]
    newData = dataEnviron[NEW_DATA_ID]
    measGood = dataEnviron[MEAS_GOOD_ID]
    scriptName = dataEnviron[SCRIPT_NAME_ID]
    return (reportedData, forwardedData, newData, measGood, scriptName, pulseDict)
