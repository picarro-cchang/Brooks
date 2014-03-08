#!/usr/bin/python

# Check that all the peaks files in an environment have associated dat files in AnzLogMeta table

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

        self.dbase = self.client["main_metrisis"]
        self.counters = self.dbase["counters"]
        self.immutable_names = self.dbase["immutable_names"]
        self.analyzer = self.dbase["analyzer"]
        self.analyzer_dat_logs_list = self.dbase["analyzer_dat_logs_list"]

        self.analyzer_peak_logs_list = self.dbase["analyzer_peak_logs_list"]
        self.analyzer_peak_logs = self.dbase["analyzer_peak_logs"]

        self.analyzer_analysis_logs_list = self.dbase["analyzer_analysis_logs_list"]
        self.analyzer_analysis_logs = self.dbase["analyzer_analysis_logs"]

        #self.analyzer_peak_logs = self.dbase["analyzer_peak_logs"]
        #print self.analyzer.find().count()
        #print self.analyzer_peak_logs_list.find().count()
        #print self.analyzer_peak_logs.find().count()

    def analyze(self):
        
        fnm_logs = set([log["fnm"] for log in self.analyzer_analysis_logs.find()])
        print "Analysis files in analysis logs", len(fnm_logs)
        fnm_meta = set([meta["fnm"] for meta in self.analyzer_analysis_logs_list.find()])
        nMatches = self.analyzer_analysis_logs_list.find().count()
        print "Analysis files in metadata", nMatches
        print "File numbers of analysis files in logs which are not in analysis metadata"
        for fnm in fnm_logs:
            if fnm not in fnm_meta:
                print fnm
        analysis_names = set([meta["name"].split(".")[0] for meta in self.analyzer_analysis_logs_list.find()])        
 

        fnm_logs = set([log["fnm"] for log in self.analyzer_peak_logs.find()])
        print "Peaks files in peaks logs", len(fnm_logs)
        
        fnm_meta = set()
        peaks_names = set()
        peaks_lookup = {}
        for meta in self.analyzer_peak_logs_list.find():
            fnm_meta.add(meta["fnm"])
            peaks_names.add(meta["name"].split(".")[0])
            peaks_lookup[meta["name"].split(".")[0]] = meta["fnm"]
        nMatches = self.analyzer_peak_logs_list.find().count()
        print "Peaks files in metadata", nMatches
        print "File numbers of peaks files in logs which are not in peaks metadata"
        for fnm in fnm_logs:
            if fnm not in fnm_meta:
                print fnm

        nMatches = self.analyzer_dat_logs_list.find().count()
        print "Number of dat files", nMatches
        dat_names = set([meta["name"].split(".")[0] for meta in self.analyzer_dat_logs_list.find()])

        print "Analysis files in metadata without corresponding dat files"
        for analysis_name in analysis_names:
            if analysis_name not in dat_names:
                print analysis_name

        print "Peaks files in metadata without corresponding dat files"
        for peaks_name in peaks_names:
            if peaks_name not in dat_names:
                print peaks_name, peaks_lookup[peaks_name]

    def close(self):
        self.client.close()

if __name__ == "__main__":
    #peakName = 'FCDS2008-20120610-131326Z-DataLog_User_Minimal.peaks'
    dbi = DatabaseInterface()
    try:
        dbi.analyze()
    finally:
        dbi.close()