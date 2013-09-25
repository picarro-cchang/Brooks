#!/usr/bin/python

import cPickle
import pymongo
import time
import json
import bz2

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
        self.counters = self.dbase["counters"]
        self.immutable_names = self.dbase["immutable_names"]
        self.analyzer = self.dbase["analyzer"]
        self.analyzer_dat_logs_list = self.dbase["analyzer_dat_logs_list"]
        self.analyzer_dat_logs = self.dbase["analyzer_dat_logs"]
        #print self.analyzer.find().count()
        #print self.analyzer_dat_logs_list.find().count()
        #print self.analyzer_dat_logs.find().count()

    def export(self, name):
        result = {}
        log_meta = self.analyzer_dat_logs_list.find({'name': name})
        nMatches = log_meta.count()
        print "Number of matches in log_list", nMatches
        if nMatches != 1:
            raise ValueError("Should be exactly one match for specified log")
        l = log_meta.next()
        del l["_id"]
        result['meta'] = l
        anz = l['anz']
        docmap = l['docmap']
        fileIndex = l['fnm']
        analyzer = self.analyzer.find({'anz': anz})
        nMatches = analyzer.count()
        print "Number of matches in analyzer collection", nMatches
        if nMatches != 1:
            raise ValueError("Should be exactly one match for specified analyzer")
        a = analyzer.next()
        del a["_id"]
        result['analyzer'] = a
        print a
        log = self.analyzer_dat_logs.find({'fnm': fileIndex})
        nMatches = log.count()
        print "Number of log entries", nMatches
        start = time.time()
        dat = []
        for rec in log:
            del rec["_id"]
            dat.append(rec)
        result['dat'] = dat
        dat = bz2.compress(cPickle.dumps(result,-1))
        print "Bytes used", len(dat)
        print "Time taken", time.time()-start
        with open("dump.bz2", "wb") as fp:
            fp.write(dat)

    def close(self):
        self.client.close()

if __name__ == "__main__":
    logName = 'FDDS2021-20130503-010319Z-DataLog_User_Minimal.dat'
    dbi = DatabaseInterface()
    try:
        dbi.export(logName)
    finally:
        dbi.close()