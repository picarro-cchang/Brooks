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
        self.dbase = self.client["main_metrisis"]
        self.counters = self.dbase["counters"]
        self.immutable_names = self.dbase["immutable_names"]
        self.analyzer = self.dbase["analyzer"]
        self.analyzer_dat_logs_list = self.dbase["analyzer_dat_logs_list"]
        self.analyzer_dat_logs = self.dbase["analyzer_dat_logs"]
        self.analyzer_peak_logs_list = self.dbase["analyzer_peak_logs_list"]
        self.analyzer_peak_logs = self.dbase["analyzer_peak_logs"]
        #print self.analyzer.find().count()
        #print self.analyzer_peak_logs_list.find().count()
        #print self.analyzer_peak_logs.find().count()

    def findDuplicates(self):
        with file('dat_Duplicates.csv','w') as op:
            result = {}
            log_meta = self.analyzer_dat_logs_list.find()
            nMatches = log_meta.count()
            print "Number of matches in log_list", nMatches
            for l in log_meta:
                fileIndex = l['fnm']
                docmap = l['docmap']
                log = self.analyzer_dat_logs.find({'fnm': fileIndex})
                # See if there are any duplicates
                rows = set()
                i = 0
                etime = []
                machineId = []
                processId = []
                rowList = []
                pkTime = []
                etIdx = docmap["EPOCH_TIME"]
                for pk in log:
                    rows.add(pk["row"])
                    rowList.append(pk["row"])
                    if pk[etIdx]!=0: pkTime.append(pk[etIdx])
                    i += 1
                    objectId = str(pk["_id"])
                    etime.append(int(objectId[:8],base=16))
                    machineId.append(int(objectId[8:14],base=16))
                    processId.append(int(objectId[14:18],base=16))
                logname = l['logname']
                rowList.sort()
                
                # Extract date and time associated with this file
                fields = logname.split('-')
                if etime and pkTime:
                    # set(processId) gives the distict PIDs involved in populating the table
                    # len(rows) is number of unique row indices, len(rowlist) is number of rows for this log
                    # etime contains times of the records in the database derived from Mongo ObjectIds
                    # pkTime contains times associated with the peaks from the peaks file
                    msg = "%s, %s, %s, %d, %d, %d, %d, %d, %s" % (logname, fields[1], fields[2], len(set(processId)), 
                                              len(rows), len(rowList), max(etime)-min(etime), max(pkTime)-min(pkTime), 
                                              rowList == range(1,len(rowList)+1))
                    print msg
                    print >> op, msg

    def close(self):
        self.client.close()

if __name__ == "__main__":
    dbi = DatabaseInterface()
    try:
        dbi.findDuplicates()
    finally:
        dbi.close()