#!/usr/bin/python
#
# File Name: DataSynchronizer.py
# Purpose:
#   Utility functions for data-driven resampling in the data manager. Within the raw data script,
#  we instantiate a Synchronizer object (class defined in ScriptRunner) when the script is first
#  run. The parameters of the constructor are:
#
#  analyzer: An identifier corresponding to a SPECTRUM_ID in the mode file whose name specifies the 
#             analyzer for the synchronized data. 
#  varList: A list of tuples specifying which variables are to be synchronized. Each tuple is of 
#             the form (raw_var_name, sync_var_name, cond_var_name, cond_var_value). The raw variable
#             is assumed to be valid when cond_var_name takes on the value cond_var_value. This is 
#             typically used to specify a subscheme Id. If cond_var_name is set to None, the raw 
#             variable is assumed to update on every raw data row.
#  syncInterval: The time between synchronized samples in milliseconds. The resulting timestamps are
#             integer multiples of the syncInterval.
#  syncLatency: When a raw data point arrives with a given timestamp, the resampled datapoints are
#             computed while the resulting timestamps are less than the timestamp minus the syncLatency.
#             The syncLatency is chosen so that after this amount of time, we have enough information 
#             to interpolate all the variables in varList up to that instant.
#  processInterval: Number of milliseconds between the times at which the raw analysis script calls the
#             synchronizer.
#  maxDelay: If the resynchronizer falls behind the raw data time by longer than maxDelay milliseconds,
#             the resynchronizer is reset and attempts to restart resynchronization from the multiple
#             of syncInterval which is just less than the raw data timestamp.
# This Synchronizer object attaches a dictionary to _GLOBALS_["synchronizer"][analyzer] which contains
#  the parameters of the requested synchronization process.

# When a raw data entry arrives, we call the dispatch method of the Synchronizer object. This triggers the
#  synchronization analysis script provided at the new timestamp is at least processInterval more than
#  the timestamp associated with the last trigger. 
#
# When the synchronization analysis script is triggered, it repeatedly calls itself, performing as
#   many interpolatioin steps as it can. To do this, it stores "lastMeasTimestamp" and "resampTimestamp"
#   in a dictionary called "synchronizer" in the persistent environment associated with this script.
# Within the synchronization analysis script it is only necessary to have the line:
#   rdict = _SYNC_OUT_(analyzer)
# which returns a dictionary containing the synchronized data, or an empty dictionary if none is available.
#
# Notes:
#
# ToDo:
#
# File History:
# 11-04-12 sze   Initial version
APP_NAME = "DataSynchronizer"
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

def interp(old,var,condVar,condVal,ts):
    status = True
    result = 0.0
    if (var not in old) or (condVar and condVar not in old):
        status = False
    else:
        tsLast = None
        valLast = None
        if condVar:
            i = 0
            while True:
                i -= 1
                try:
                    v = old[var][i]
                    cv = old[condVar][i]
                except IndexError:
                    raise LookupError("Cannot find timestamp in saved data")
                ts1 = v.timestamp
                if ts1 != cv.timestamp:
                    Log("Timestamp mismatch between condition %s (%s) and variable %s (%s)" % (condVar,cv.timestamp,var,ts1),Level=2)
                if cv.value == condVal:
                    if ts1<=ts:
                        if tsLast is None:
                            result = v.value
                            status = False
                        else:
                            if tsLast != ts1:
                                result = valLast + (ts - tsLast)*(v.value-valLast)/(ts1 - tsLast)
                            else:
                                result = 0.5*(v.value + valLast)
                        break
                    tsLast = ts1
                    valLast = v.value
        else:
            i = 0
            while True:
                i -= 1
                try:
                    v = old[var][i]
                except IndexError:
                    raise LookupError("Cannot find timestamp in saved data")
                ts1 = v.timestamp
                if ts1<=ts:
                    if tsLast is None:
                        result = v.value
                        status = False
                    else:
                        if tsLast != ts1:
                            result = valLast + (ts - tsLast)*(v.value-valLast)/(ts1 - tsLast)
                        else:
                            result = 0.5*(v.value + valLast)
                    break
                tsLast = ts1
                valLast = v.value
    return result, status

def resync(analyzer,env):
    pp = env["_PERSISTENT_"]
    gg = env["_GLOBALS_"]
    dd = env["_DATA_"]
    oo = env["_OLD_DATA_"]
    aa = env["_ANALYZE_"]

    report = {}
    
    if "synchronizer" not in pp:
        pp["synchronizer"] = dict(resampTimestamp=None,lastMeasTimestamp=None)

    p = pp["synchronizer"]
    g = gg["synchronizer"][analyzer]

    lastMeasTimestamp = p["lastMeasTimestamp"]
    syncInterval = g["syncInterval"]
    resampTimestamp = p["resampTimestamp"]
    maxDelay = g["maxDelay"]
    varList = g["varList"]
    
    ts = int(dd["timestamp"])
    if lastMeasTimestamp is None or ts>lastMeasTimestamp:
        p["lastMeasTimestamp"] = lastMeasTimestamp = ts
    if resampTimestamp is None or lastMeasTimestamp-resampTimestamp>maxDelay:
        p["resampTimestamp"] = syncInterval*(lastMeasTimestamp//syncInterval)
        return report
    else:
        nextResampTimestamp = resampTimestamp+g["syncInterval"]
        
    if nextResampTimestamp<lastMeasTimestamp-g["syncLatency"]:
        report = {"timestamp":nextResampTimestamp}
        good = True
        try:
            for var,syncVar,condVar,condVal in varList:
                report[syncVar],status = interp(oo,var,condVar,condVal,nextResampTimestamp)
                good = good and status
            report['syncStatus'] = int(status)
        except LookupError:
            # nextResampTimestamp = None
            report = {}
            pass
        # print "Resampling at %s" % nextResampTimestamp
        p["resampTimestamp"] = nextResampTimestamp
        aa[analyzer] = {"timestamp":lastMeasTimestamp}
    return report
