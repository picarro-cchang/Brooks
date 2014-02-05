#!/usr/bin/python

# Determine all the database LRT and FOV entries and report generation files associated with 
#  a list of minimal log names

import cPickle
import json
import numpy as np
import os
import shutil
# import pymongo
import re
import time

class DbaseError(Exception):
    pass

class DatabaseInterface(object):

    def __init__(self):
        # ports = [27017, 37017, 37018]
        # for p in ports:
        #     try:
        #         self.client = pymongo.MongoClient(port=p)
        #     except pymongo.errors.ConnectionFailure:
        #         continue
        #     if self.client.is_primary:
        #         break
        #     self.client.close()
        # else:
        #     raise DbaseError("Unable to connect to primary database")

        # # Get the various collections of interest

        # self.dbase = self.client["main_metrisis"]
        # self.counters = self.dbase["counters"]
        # self.immutable_names = self.dbase["immutable_names"]
        # self.analyzer = self.dbase["analyzer"]
        # self.analyzer_dat_logs_list = self.dbase["analyzer_dat_logs_list"]

        # self.analyzer_peak_logs_list = self.dbase["analyzer_peak_logs_list"]
        # self.analyzer_peak_logs = self.dbase["analyzer_peak_logs"]

        # self.analyzer_analysis_logs_list = self.dbase["analyzer_analysis_logs_list"]
        # self.analyzer_analysis_logs = self.dbase["analyzer_analysis_logs"]

        # self.lrt_meta = self.dbase["lrt_meta"]

        self.reportDir = "c:/temp/metrisis/"

        #self.analyzer_peak_logs = self.dbase["analyzer_peak_logs"]
        #print self.analyzer.find().count()
        #print self.analyzer_peak_logs_list.find().count()
        #print self.analyzer_peak_logs.find().count()

    def analyze(self, logNames):
        # Find all lrt_meta records that refer to the logs
        for logName in logNames:
            # regx = re.compile(logName, re.IGNORECASE)

            # print logName
            # for lrt in self.lrt_meta.find({"lrt_prms_str":regx}):
            #     print lrt["lrt_collection"]

            for root, dirs, files in os.walk(self.reportDir):
                if "key.json" in files:
                    with open(os.path.join(root, "key.json"),"rb") as fp:
                        if logName in fp.read():
                            if "status.dat" in files:
                                sFile = os.path.join(root, "status.dat")
                                with open(sFile,"rb") as sp:
                                    statusDict = {}
                                    for line in sp:
                                        statusDict.update(json.loads(line))
                                if "flag" not in statusDict:
                                    with open(sFile,"ab") as sp:
                                        print "Adding flag to %s" % sFile
                                        print >>sp, '{"flag":"*"}'
                                if statusDict["instructions_type"] == "makeReport":
                                    if statusDict["status"] == -16:
                                        print sFile
                                        with open(sFile,"rb") as sp:
                                            with open("temp.tmp","wb") as tp:
                                                temp = None
                                                for line in sp:
                                                    if temp is not None:
                                                        tp.write(temp)
                                                    temp = line
                                        # raw_input("Please check %s" % os.path.abspath("temp.tmp"))
                                        shutil.copyfile("temp.tmp", sFile)

                                    #    print "Setting status -16 in %s" % sFile
                                    #    print >>sp, '{"status":-16}'

                            # iFile = os.path.join(os.path.split(root)[0],"instructions.json")
                            # with open(iFile, "rb") as ip:
                            #     instr = json.load(ip)
                            # if instr['instructions_type'] == "makeReport":
                            #     #if 'force' not in instr or not instr['force']:
                            #     if 'generation' in instr:
                            #         del instr['generation']
                            #     instr['force'] = False
                            #     print "Removing force from %s" % iFile
                            #     with open(iFile, "wb") as ip:
                            #         result = json.dumps(instr,sort_keys=True,indent=2)
                            #         result = result.replace(" \n", "\n")
                            #         ip.write(result)


    def close(self):
        # self.client.close()
        pass

if __name__ == "__main__":
    dbi = DatabaseInterface()
    logNames = ["FDDS2029-20130703-183920Z-DataLog_User_Minimal.dat"]
    try:
        dbi.analyze(logNames)
    finally:
        dbi.close()
