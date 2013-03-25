# batchReport.py is used to run the report generation software for a collection of instruction files without
#  operator intervention

from collections import Counter
try:
    import json
except:
    import simplejson as json
import multiprocessing as mp
import shutil
import socket
import subprocess
import time
import unittest
import urllib
import urllib2
import sys
import zmq
from MobileKit.ReportGeneration.ReportCommon import getTicket, ReportApiService, PROJECT_SUBMISSION_PORT, STOP_WORKERS_PORT 
from MobileKit.ReportGeneration.ReportCommon import JOB_DISTRIBUTION_PORT, JOB_COMPLETE_PORT, RESOURCE_MANAGER_PORT
import MobileKit.ReportGeneration.ProjectSupport as PP

TEST_ROOT = r"c:\temp\ReportGen"
        
def setup_module():
    global  projectManagerCommand, reportServer, reportApi, resourceManager, resourceManagerCommand, zmqContext
    shutil.rmtree(TEST_ROOT,ignore_errors=True)        
    #reportServer = subprocess.Popen(["python.exe",r"..\..\ReportGeneration\reportServer.py","-r",TEST_ROOT],
    #                                stderr=file("NUL","w"))
    reportServer = subprocess.Popen(["python.exe",r"..\..\ReportGeneration\reportServer.py","-r",TEST_ROOT])
    reportApi = ReportApiService()
    reportApi.csp_url = "http://localhost:5200"
    reportApi.debug = False
    zmqContext = zmq.Context()
    resourceManagerCommand = zmqContext.socket(zmq.REQ)
    resourceManager = PP.ResourceManagerProxy(resourceManagerCommand)
    projectManagerCommand = zmqContext.socket(zmq.REQ)
    projectManagerCommand.connect("tcp://127.0.0.1:%d" % PROJECT_SUBMISSION_PORT)
    
def teardown_module():
    global  projectManagerCommand, reportServer, reportApi, resourceManager, resourceManagerCommand, zmqContext
    #resourceManager.shutDown()
    resourceManagerCommand.close()
    projectManagerCommand.close()
    # Ask the report server to shut down nicely
    #reportApi.csp_url = "http://localhost:5200"
    #qry_url = '%s/shutdown' % (reportApi.csp_url)
    #resp = urllib2.urlopen(qry_url,data=urllib.urlencode({})) # Send a POST
    #info = resp.info()
    #rtn_data = resp.read()
    reportServer.terminate()
    reportServer.wait()    
    zmqContext.term()
        
def raiseOnError(result):
    if 'error' in result and result['error'] is not None: raise RuntimeError(result['error'])
    result = result['return']
    if 'error' in result and result['error'] is not None: raise RuntimeError(result['error'])
    return result

class TestSubmitReport(unittest.TestCase):
    global  projectManagerCommand, psProcess, reportServer, reportApi, resourceManager, rmProcess, zmqContext
    def testSubmitInstructions(self):
        instructions = "instructions_20120930T163002.json"
        with open(instructions,"rb") as fp:
            contents = fp.read().splitlines()
        while contents[0].startswith("//"):
            contents.pop(0)
        # Check this is valid JSON
        contents = "\n".join(contents)
        json.loads(contents)    # Throws exception on faulty JSON
        # Get the secure hash for prepending
        qryparms = { 'qry': 'download', 'content': contents,  'filename': 'instructions.json'}
        contents = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        qryparms = { 'qry': 'validate', 'contents': contents }
        result = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        contents = result['contents']
        qryparms = { 'qry': 'submitProject', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        ticket = result["ticket"]
        print "ticket", ticket
        while True:
        # Start some workers
            nWorkers = 4
            projectManagerCommand.send(json.dumps({"msg": "SET_POOL_SIZE", "poolSize": nWorkers}))
            json.loads(projectManagerCommand.recv())
            projectManagerCommand.send(json.dumps({"msg": "GET_WORKER_STATS"}))
            reply = json.loads(projectManagerCommand.recv())
            #print reply
            nWorkers = len(reply["workers"])
            nWorkersFree = reply["nWorkersFree"]
            projectManagerCommand.send(json.dumps({"msg": "GET_STATISTICS"}))
            reply = json.loads(projectManagerCommand.recv())
            #print reply
            # Calculate pending jobs
            jobs = Counter(reply["jobs"])
            jobsDispatched = Counter(reply["jobsDispatched"])
            jobsFailed = Counter(reply["jobsFailed"])
            jobsSuccessful = Counter(reply["jobsSuccessful"])
            jobsCrashed = Counter(reply["jobsCrashed"])
            jobsLeft = sum((jobs-jobsFailed-jobsSuccessful-jobsCrashed).values())
            print sum(jobs.values()), sum(jobsDispatched.values()), sum(jobsSuccessful.values()), sum(jobsFailed.values()), sum(jobsCrashed.values()), jobsLeft, nWorkers, nWorkersFree
            if jobsLeft == 0 and nWorkers == nWorkersFree: break
            time.sleep(1.0)
        projectManagerCommand.send(json.dumps({"msg": "SET_POOL_SIZE", "poolSize": 0}))
        reply = json.loads(projectManagerCommand.recv())
        time.sleep(1.0)
        projectManagerCommand.send(json.dumps({"msg": "STOP_WORKERS"}))
        reply = json.loads(projectManagerCommand.recv())
        while True:
            projectManagerCommand.send(json.dumps({"msg": "GET_WORKER_STATS"}))
            reply = json.loads(projectManagerCommand.recv())
            print reply
            if len(reply["workers"]) == 0: break
            time.sleep(1.0)

        
if __name__ == '__main__':
    unittest.main()
