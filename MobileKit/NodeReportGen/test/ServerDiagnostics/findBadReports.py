from glob import glob
import json
import os
import csv

dupPeaksFile = r'C:\temp\PGEDups\pge.dups.peak.log'
dupAnalysesFile = r'C:\temp\PGEDups\pge.dups.analysis.log'
dirName = r'c:\temp\Pge'

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
                    keyData = json.loads(kp.read())
                    try:
                        peaksFiles = keyData["SUBTASKS"]["getPeaksData"]["OUTPUTS"]["SURVEYS"]
                        peaksSet = set(map(str, peaksFiles.values()))
                        intersection = peaksSet & dupPeaksSet
                        badPeaks = []
                        if intersection:
                            badPeaks = [pk for pk in intersection]
                    except IndexError:
                        # print "No peaks files for %s" % key
                        pass
                    try:
                        analysesFiles = keyData["SUBTASKS"]["getAnalysesData"]["OUTPUTS"]["SURVEYS"]
                        analysesSet = set(map(str, analysesFiles.values()))
                        badAnalyses = []
                        intersection = analysesSet & dupAnalysesSet
                        if intersection:
                            badAnalyses = [an for an in intersection]
                    except IndexError:
                        # print "No analyses files for %s" % key
                        pass
                    if badPeaks or badAnalyses:        
                        # print md5, etm, user, job["val"]["startLocalTime"], job["val"]["title"]
                        csv.writer(csvp).writerow([md5, etm, user, job["val"]["startLocalTime"], job["val"]["title"]] + badPeaks + badAnalyses)
                        badJobs += 1
                        
            except IOError:
                # print "No key.json file for %s" % key
                pass
                
        print "User %s: (%d bad/ %d total)" % (user, badJobs, len(jobs))