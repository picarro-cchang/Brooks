from glob import glob
import json
import os
import csv

dupDatFile = r'dups.dat.log'
dupPeaksFile = r'dups.peak.log'
dupAnalysesFile = r'dups.analysis.log'
dirName = r'/usr/local/picarro/p3SurveyorRpt/ReportGen/metrisis'

dupDatSet = set()
with open(dupDatFile, 'r') as fp:
    for line in fp:
        dupDatSet.add(line.split(" ")[-1].strip())

dupPeaksSet = set()
with open(dupPeaksFile, 'r') as fp:
    for line in fp:
        dupPeaksSet.add(line.split(" ")[-1].strip())
        
dupAnalysesSet = set()
with open(dupAnalysesFile, 'r') as fp:
    for line in fp:
        dupAnalysesSet.add(line.split(" ")[-1].strip())

users = []
for dname in glob(os.path.join(dirName, 'users', '*')):
    users.append(os.path.split(dname)[-1])

with open("badReports.csv", "wb") as csvp:
    for user in users:
        userdb = os.path.join(dirName, 'users', user, '*.db')
        print userdb
        dbName = glob(userdb)[0]
        
        jobs = {}
        with open(dbName, 'r') as fp:
            for line in fp:
                d = json.loads(line)
                jobs[d['key']] = d
        
        print 'User database name', dbName
        print "User %s has %d jobs" % (user, len(jobs))
        badJobs = 0
        for key in jobs:
            job = jobs[key]
            md5, etm = key.split("_")
            jobdir = os.path.join(dirName, md5[:2], md5, etm)
            try:
                with open(os.path.join(jobdir,"key.json"), "r") as kp:
                    keyText = kp.read()
                    keyData = json.loads(keyText)
                    try:
                        peaksFiles = keyData["SUBTASKS"]["getPeaksData"]["OUTPUTS"]["SURVEYS"]
                        peaksSet = set(map(str, peaksFiles.values()))
                        intersection = peaksSet & dupPeaksSet
                        badPeaks = []
                        if intersection:
                            badPeaks = [pk for pk in intersection]
                    except KeyError:
                        # print "No peaks files for %s" % key
                        pass
                    try:
                        analysesFiles = keyData["SUBTASKS"]["getAnalysesData"]["OUTPUTS"]["SURVEYS"]
                        analysesSet = set(map(str, analysesFiles.values()))
                        badAnalyses = []
                        intersection = analysesSet & dupAnalysesSet
                        if intersection:
                            badAnalyses = [an for an in intersection]
                    except KeyError:
                        # print "No analyses files for %s" % key
                        pass
                    try:
                        datFiles = keyData["SUBTASKS"]["getFovsData"]["OUTPUTS"]["SURVEYS"]
                        datSet = set(map(str, datFiles.values()))
                        badDat = []
                        intersection = datSet & dupDatSet
                        if intersection:
                            badDat = [dat for dat in intersection]
                    except KeyError:
                        # print "No dat files for %s" % key
                        pass
                    
                    if badPeaks or badAnalyses or badDat:        
                        # print md5, etm, user, job["val"]["startLocalTime"], job["val"]["title"]
                        csv.writer(csvp).writerow([md5, etm, user, job["val"]["startLocalTime"], job["val"]["title"]] + badPeaks + badAnalyses + badDat)
                        badJobs += 1
                        
            except IOError:
                # print "No key.json file for %s" % key
                pass
                
        print "User %s: (%d bad/ %d total)" % (user, badJobs, len(jobs))