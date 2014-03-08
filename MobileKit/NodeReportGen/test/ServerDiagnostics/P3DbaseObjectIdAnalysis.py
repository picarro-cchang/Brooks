#!/usr/bin/python

import cPickle
import pymongo
import time
import json
import numpy as np

class DbaseError(Exception):
    pass

class DatabaseInterface(object):

    def __init__(self):
        ports = [27017, 37017, 37018]
        for p in ports:
            try:
                self.client = pymongo.MongoClient(port=p)
            except pymongo.errors.ConnectionFailure:
                continue
            if self.client.is_primary:
                break
            self.client.close()
        else:
            raise DbaseError("Unable to connect to primary database")

        # Get the various collections of interest

        self.dbase = self.client["main_stage"]
        self.dbase = self.client["main_pge"]
        self.counters = self.dbase["counters"]
        self.immutable_names = self.dbase["immutable_names"]
        self.analyzer = self.dbase["analyzer"]
        self.analyzer_peak_logs_list = self.dbase["analyzer_peak_logs_list"]
        self.analyzer_peak_logs = self.dbase["analyzer_peak_logs"]
        #print self.analyzer.find().count()
        #print self.analyzer_peak_logs_list.find().count()
        #print self.analyzer_peak_logs.find().count()

    def analyze(self, name):
        result = {}
        log_meta = self.analyzer_peak_logs_list.find({'name': name})
        nMatches = log_meta.count()
        print "Number of matches in log_list", nMatches
        if nMatches != 1:
            raise ValueError("Should be exactly one match for specified log")
        l = log_meta.next()
        fileIndex = l['fnm']
        log = self.analyzer_peak_logs.find({'fnm': fileIndex})
        nMatches = log.count()
        print "Number of log entries", nMatches
        # See if there are any duplicates
        rows = set()
        i = 0
        etime = []
        machineId = []
        processId = []
        rowList = []
        for pk in log:
            rows.add(pk["row"])
            rowList.append(pk["row"])
            i += 1
            objectId = str(pk["_id"])
            print objectId
            etime.append(int(objectId[:8],base=16))
            machineId.append(int(objectId[8:14],base=16))
            processId.append(int(objectId[14:18],base=16))
        print set(machineId)
        pidSet = set(processId)
        rowList = np.asarray(rowList)
        etime = np.asarray(etime)        
        machineId = np.asarray(machineId)
        processId = np.asarray(processId)
        print pidSet
        for pid in pidSet:
            etimes = etime[processId == pid]
            subrows = rowList[processId == pid]
            consistent = len(set(subrows)) == len(subrows)
            print pid, len(etimes), time.ctime(etimes.min()), time.ctime(etimes.max()), etimes.ptp(), consistent
        print 'Rows: %d/%d' % (len(rows), i)

    def close(self):
        self.client.close()

if __name__ == "__main__":
    #peakName = 'FCDS2008-20120610-131326Z-DataLog_User_Minimal.peaks'
    peakName = 'FDDS2006-20130909-102849Z-DataLog_User_Minimal.peaks'
    dbi = DatabaseInterface()
    try:
        dbi.analyze(peakName)
    finally:
        dbi.close()