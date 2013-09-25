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
import datetime

try:
    import simplejson as json
except:
    import json

import math
from P3RestApi import P3RestApi

class AccessReportServer(object):
    def __init__(self):
        self.p3RestApi = P3RestApi(host="p3.picarro.com", port=443, site="stage", 
            identity="zYa8P106vCc8IfpYGv4qcy2z8YNeVjHJw1zaBDth", psys="stage", svc="gdu",
            debug=False, sleep_seconds=0, version='1.0', resource='SurveyorRpt',
            rprocs=["SurveyorRpt:resource","SurveyorRpt:getStatus","SurveyorRpt:submit",
                    "SurveyorRpt:updateDashboard","SurveyorRpt:getDashboard"])

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
    rptServer = AccessReportServer()
    rptServer.getDashboard("aaron@AGA")
    rptServer.getDashboard("chris@STAGE")
    rptServer.getDashboard("demoUser")
    rptServer.getDashboard("pfranz@STAGE")
    rptServer.getDashboard("aaron@STAGE")
    rptServer.getDashboard("CTO@picarro")
    rptServer.getDashboard("dsteele@STAGE")
    rptServer.getDashboard("sdavis@AGA")
    rptServer.getDashboard("admin@CENTERPOINT2")
    rptServer.getDashboard("demo@AGA")
    rptServer.getDashboard("jesse@STAGE")
    rptServer.getDashboard("sdavis@STAGE")
    rptServer.getDashboard("admin@STAGE")
    rptServer.getDashboard("demo@STAGE")
    rptServer.getDashboard("jyiu@STAGE")
    rptServer.getDashboard("stan@STAGE")
