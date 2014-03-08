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
        with open("peaklog.csv", "w") as op:
            result = {}
            log_meta = self.analyzer_peak_logs_list.find({'name': name})
            nMatches = log_meta.count()
            print "Number of matches in log_list", nMatches
            if nMatches != 1:
                print "Should be exactly one match for specified log"                
            l = log_meta.next()
            fileIndex = l['fnm']
            docmap = l['docmap']
            keyList = docmap.keys()
            log = self.analyzer_peak_logs.find({'fnm': fileIndex})
            nMatches = log.count()
            print "Number of log entries", nMatches
            # See if there are any duplicates
            rows = set()
            i = 0
            hdr = ['processId', 'machineId', 'dbTime'] + [str(k) for k in keyList]
            msg = ",".join(hdr)
            print msg
            print >>op, msg
            for pk in log:
                row = pk["row"]
                objectId = str(pk["_id"])
                etime = int(objectId[:8],base=16)
                mId = int(objectId[8:14],base=16)
                pId = int(objectId[14:18],base=16)
                data = [pId, mId, etime]
                for k in keyList:
                    data.append(pk.get(unicode(docmap[k]),''))
                msg = ",".join(["%s" % d for d in data])
                print msg
                print >>op, msg

    def close(self):
        self.client.close()

if __name__ == "__main__":
    #peakName = 'FCDS2008-20120610-131326Z-DataLog_User_Minimal.peaks'
    #peakName = 'FDDS2006-20130909-102849Z-DataLog_User_Minimal.peaks'
    #peakName = 'FDDS2006-20130430-111046Z-DataLog_User_Minimal.peaks'
    peakName = 'FDDS2018-20140106-045525Z-DataLog_User_Minimal.peaks'
    dbi = DatabaseInterface()
    try:
        dbi.analyze(peakName)
    finally:
        dbi.close()