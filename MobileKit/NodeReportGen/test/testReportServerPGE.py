#! /usr/bin/python
'''
Interact with the report generation software on a remote P3 server via Python rather 
than through a browser to test the node.js code
'''
import os
import sys
import subprocess
import glob
import shutil

from optparse import OptionParser

import time
import calendar
import datetime

try:
    import simplejson as json
except:
    import json

import math
import urllib
from P3RestApi import P3RestApi

REPORTROOT = "c:/temp/Pge/"

def getMsUnixTime(timeString=None):
    if timeString is None:
        return int(1000 * time.time())
    else:
        if len(timeString) != 24 or timeString[-5] != "." or timeString[-1] != "Z":
            raise ValueError("Bad time string: %s" % timeString)
        return 1000 * calendar.timegm(time.strptime(timeString[:-5], "%Y-%m-%dT%H:%M:%S")) + int(timeString[-4:-1])


def msUnixTimeToTimeString(msUnixTime):
    u = msUnixTime // 1000
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(u)) + ".%03dZ" % (msUnixTime % 1000,)


def timeStringAsDirName(ts):
    return "%013d" % getMsUnixTime(ts)


class AccessReportServer(object):

    def __init__(self, host, site, identity, sys):
        self.p3RestApi = P3RestApi(host=host, port=443, site=site,
                                   identity=identity, psys=sys, svc="gdu",
                                   debug=False, sleep_seconds=5, version='1.0', resource='SurveyorRpt',
                                   rprocs=[
                                   "SurveyorRpt:resource", "SurveyorRpt:getStatus", "SurveyorRpt:submit",
                                   "SurveyorRpt:updateDashboard", "SurveyorRpt:getDashboard"])

    def submitJob(self, instrFile, user, force=False):
        with open(instrFile, 'r') as fp:
            contents = fp.read()
        params_dict = {}
        params_dict['existing_tkt'] = True
        params_dict['qryobj'] = {}
        params_dict['qryobj']['qry'] = 'submit'
        params_dict['qryobj']['contents'] = urllib.quote(contents)
        params_dict['qryobj']['user'] = user
        params_dict['qryobj']['force'] = force
        rtn = self.p3RestApi.get(params_dict)
        if ("error" in rtn) and (rtn["error"] != None):
            raise RuntimeError('%s' % rtn)
        else:
            # print "Status: ", rtn[0]
            hash = rtn[1]['rpt_contents_hash']
            start_ts = rtn[1]['rpt_start_ts']
        return rtn[0], dict(hash=hash, start_ts=start_ts)

    def getStatus(self, hash, start_ts):
        params_dict = {}
        params_dict['existing_tkt'] = True
        params_dict['qryobj'] = {}
        params_dict['qryobj']['qry'] = 'getStatus'
        params_dict['qryobj']['contents_hash'] = hash
        params_dict['qryobj']['start_ts'] = start_ts
        rtn = self.p3RestApi.get(params_dict)
        if ("error" in rtn) and (rtn["error"] != None):
            raise RuntimeError('%s' % rtn)
        else:
            # print "Status: ", rtn[0]
            status = rtn[1]['status']
            hash = rtn[1]['contents_hash']
            dirname = timeStringAsDirName(start_ts)
            # print status, hash, dirname
        return rtn[0], dict(status=status, hash=hash, dirname=dirname)

    def getFile(self, filePath):
        params_dict = {}
        params_dict['existing_tkt'] = True
        resourcePath = filePath
        rtn = self.p3RestApi.get(params_dict, resourcePath)
        if ("error" in rtn) and (rtn["error"] != None):
            raise RuntimeError('%s' % rtn)
        return rtn

    def getDashboard(self, user):
        params_dict = {}
        params_dict['existing_tkt'] = True
        params_dict['qryobj'] = {}
        params_dict['qryobj']['qry'] = 'getDashboard'
        params_dict['qryobj']['user'] = user

        rtn = self.p3RestApi.get(params_dict)
        if ("error" in rtn) and (rtn["error"] != None):
            print "Error", rtn
        else:
            # print "Status: ", rtn[0]
            dashboard = rtn[1]["dashboard"]
            print "User %s: %d" % (user, len(dashboard))
            for job in dashboard:
                params_dict['qryobj'] = {}
                params_dict['qryobj']['qry'] = 'getStatus'
                params_dict['qryobj']['contents_hash'] = job['hash']
                params_dict['qryobj']['start_ts'] = job['rpt_start_ts']
                rtn = self.p3RestApi.get(params_dict)
                if ("error" in rtn) and (rtn["error"] != None):
                    raise RuntimeError(rtn)
                else:
                    if rtn[1]["status"] != job['status']:
                        print rtn[1]["status"], job['status'], job['hash'], job['directory']

if __name__ == "__main__":
    rptServer = AccessReportServer(
        host='p3.picarro.com', site='pge', identity='M8J5Co0I3XxCOR92RUd6f8CLQULmOq1puY6R6NqiJVw=', sys='pge')
    user = 'stan@picarro.com'
    # rptServer.getDashboard(user)

    for loop in range(100):
        sys.stdout.write('%4d ' % loop)
        instrFile = r'C:\Users\stan\Downloads\PGE_makeFov_bad_path.json'
        retCode, jobDict = rptServer.submitJob(instrFile, user, force=True)
        if retCode != 200:
            raise RuntimeError('Bad return code from submitJob %s' % ((retCode, jobDict),))
        
        while True:
            retCode, statDict = rptServer.getStatus(jobDict['hash'], jobDict['start_ts'])
            if retCode != 200:
                raise RuntimeError('Bad return code from getStatus %s' % ((retCode, statDict),))
            if statDict['status'] == 16: break
            sys.stdout.write('.')
            time.sleep(5.0)
        sys.stdout.write('\n')

        filePath = statDict['hash'][:2] + '/' + statDict['hash'] + '/' + statDict['dirname'] + '/key.json'
        retCode, keyData = rptServer.getFile(filePath)
        if retCode != 200:
            raise RuntimeError('Bad return code from getting key file %s' % ((retCode, keyData),))

        for f in keyData['OUTPUTS']['FILES']:
            filePath = statDict['hash'][:2] + '/' + statDict['hash'] + '/' + statDict['dirname'] + ('/%s' % f)
            retCode, fileData = rptServer.getFile(filePath)
            if retCode != 200:
                raise RuntimeError('Bad return code from getting file %s' % ((retCode, fileData),))
            with open(f,'r') as fp:
                if json.loads(fp.read()) != fileData:
                    dirname = statDict['dirname']
                    try:
                        os.mkdir(dirname)
                    except OSError:
                        pass
                    with open(os.path.join(dirname,f),"w") as op:
                        op.write(fileData)
                    print "Mismatched data in", os.path.join(dirname,f)