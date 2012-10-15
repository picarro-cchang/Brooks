# Test suite for the swath processor

import subprocess
import time
import unittest
import MobileKit.ReportGeneration.ProjectSupport as PP
import json
import math
import multiprocessing as mp
from collections import Counter, namedtuple
import os
import random
import shutil
import threading
import urllib
import urllib2
import zmq
from MobileKit.ReportGeneration.ReportCommon import getTicket, ReportApiService, PROJECT_SUBMISSION_PORT, STOP_WORKERS_PORT
from MobileKit.ReportGeneration.ReportCommon import JOB_DISTRIBUTION_PORT, JOB_COMPLETE_PORT, RESOURCE_MANAGER_PORT
import MobileKit.ReportGeneration.ReportGenSupport

TEST_ROOT = r"c:\temp\ReportGen"


def raiseOnError(result):
    if 'error' in result and result['error'] is not None:
        raise RuntimeError(result['error'])
    result = result['return']
    if 'error' in result and result['error'] is not None:
        raise RuntimeError(result['error'])
    return result


class DummyInterface(object):
    def __init__(self):
        self.context = zmq.Context()

    def close(self):
        self.context.term()


class TestJobs(unittest.TestCase):
    def setUp(self):
        self.grDict = {}
        self.pfList = []

    def myGetResourceStatus(self, rt):
        """This produces dummy resource objects with status"""
        return self.grDict[rt], {}

    def myPropagateFailure(self, badResources):
        self.assertEqual(badResources, self.pfList)

    def testMakeJobNoInput(self):
        rt_out = PP.ResourceTuple("1", "RESOURCE_OUT", None)
        job1 = PP.Job(None, "job1", {}, [], [rt_out])
        # The initial status should be JOB_READY_TO_RUN
        self.grDict = {rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_READY_TO_RUN)
        # If output is IN_PROGRESS, the status should be
        #  JOB_RUNNING
        self.grDict = {rt_out: PP.Resource.IN_PROGRESS}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_RUNNING)
        # If output is MAKE_SUCCEEDED, the status should be
        #  JOB_SUCCEEDED
        self.grDict = {rt_out: PP.Resource.MAKE_SUCCEEDED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_SUCCEEDED)

    def testMakeJobSingleInputSuccess(self):
        rt_in = PP.ResourceTuple("1", "RESOURCE_IN", None)
        rt_out = PP.ResourceTuple("1", "RESOURCE_OUT", None)
        job1 = PP.Job(None, "job1", {}, [rt_in], [rt_out])
        # If input is NOT_STARTED, the status should be
        #  JOB_AWAITING_RESOURCE
        self.grDict = {rt_in: PP.Resource.NOT_STARTED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_AWAITING_RESOURCE)
        # If input is IN_PROGRESS, the status should be
        #  JOB_AWAITING_RESOURCE
        self.grDict = {rt_in: PP.Resource.IN_PROGRESS, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_AWAITING_RESOURCE)
        # If input is MAKE_SUCCEEDED, the status should be
        #  JOB_READY_TO_RUN
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_READY_TO_RUN)
        # If output is IN_PROGRESS, the status should be
        #  JOB_RUNNING
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.IN_PROGRESS}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_RUNNING)
        # If output is MAKE_SUCCEEDED, the status should be
        #  JOB_SUCCEEDED
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.MAKE_SUCCEEDED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_SUCCEEDED)

    def testMakeJobSingleInputFailure(self):
        rt_in = PP.ResourceTuple("1", "RESOURCE_IN", None)
        rt_out = PP.ResourceTuple("1", "RESOURCE_OUT", None)
        job1 = PP.Job(None, "job1", {}, [rt_in], [rt_out])
        # If input is NOT_STARTED, the status should be
        #  JOB_AWAITING_RESOURCE
        self.grDict = {rt_in: PP.Resource.NOT_STARTED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.grDict = {rt_in: PP.Resource.IN_PROGRESS, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.IN_PROGRESS}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        # If output is MAKE_FAILED, the status should be
        #  JOB_FAILED
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.MAKE_FAILED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_FAILED)

    def testMakeJobSingleInputNoneStatus(self):
        rt_in = PP.ResourceTuple("1", "RESOURCE_IN", None)
        rt_out = PP.ResourceTuple("1", "RESOURCE_OUT", None)
        job1 = PP.Job(None, "job1", {}, [rt_in], [rt_out])
        # If input is NOT_STARTED, the status should be
        #  JOB_AWAITING_RESOURCE
        job1.setStatus(None)
        self.grDict = {rt_in: PP.Resource.NOT_STARTED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_AWAITING_RESOURCE)
        # If input is IN_PROGRESS, the status should be
        #  JOB_AWAITING_RESOURCE
        job1.setStatus(None)
        self.grDict = {rt_in: PP.Resource.IN_PROGRESS, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_AWAITING_RESOURCE)
        # If input is MAKE_SUCCEEDED, the status should be
        #  JOB_READY_TO_RUN
        job1.setStatus(None)
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_READY_TO_RUN)
        # If output is IN_PROGRESS, the status should be
        #  JOB_RUNNING
        job1.setStatus(None)
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.IN_PROGRESS}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_RUNNING)
        # If output is MAKE_SUCCEEDED, the status should be
        #  JOB_SUCCEEDED
        job1.setStatus(None)
        self.grDict = {rt_in: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.MAKE_SUCCEEDED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_SUCCEEDED)

    def testMakeJobTwoInputs(self):
        rt_in1 = PP.ResourceTuple("1", "RESOURCE_IN1", None)
        rt_in2 = PP.ResourceTuple("1", "RESOURCE_IN2", None)
        rt_out = PP.ResourceTuple("1", "RESOURCE_OUT", None)
        job1 = PP.Job(None, "job1", {}, [rt_in1, rt_in2], [rt_out])
        # If input is NOT_STARTED, the status should be
        #  JOB_AWAITING_RESOURCE
        self.grDict = {rt_in1: PP.Resource.NOT_STARTED, rt_in2: PP.Resource.NOT_STARTED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_AWAITING_RESOURCE)
        # If one input is MAKE_SUCCEEDED, the status should be
        #  JOB_AWAITING_RESOURCE
        self.grDict = {rt_in1: PP.Resource.MAKE_SUCCEEDED, rt_in2: PP.Resource.NOT_STARTED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_AWAITING_RESOURCE)
        # When both inputs are MAKE_SUCCEEDED, the status should be
        #  JOB_READY_TO_RUN
        self.grDict = {rt_in1: PP.Resource.MAKE_SUCCEEDED, rt_in2: PP.Resource.MAKE_SUCCEEDED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_READY_TO_RUN)

    def testMakeJobInputFails(self):
        rt_in1 = PP.ResourceTuple("1", "RESOURCE_IN1", None)
        rt_in2 = PP.ResourceTuple("1", "RESOURCE_IN2", None)
        rt_out = PP.ResourceTuple("1", "RESOURCE_OUT", None)
        job1 = PP.Job(None, "job1", {}, [rt_in1, rt_in2], [rt_out])
        # If one input is MAKE_SUCCEEDED, the status should be
        #  JOB_AWAITING_RESOURCE
        self.grDict = {rt_in1: PP.Resource.MAKE_SUCCEEDED, rt_in2: PP.Resource.NOT_STARTED, rt_out: PP.Resource.NOT_STARTED}
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_AWAITING_RESOURCE)
        # If other input is MAKE_FAILED, the status should be
        #  JOB_FAILED
        self.grDict = {rt_in1: PP.Resource.MAKE_SUCCEEDED, rt_in2: PP.Resource.MAKE_FAILED, rt_out: PP.Resource.NOT_STARTED}
        self.pfList = [rt_in2]
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_FAILED)

    def testMakeJobInputsFail(self):
        rt_in1 = PP.ResourceTuple("1", "RESOURCE_IN1", None)
        rt_in2 = PP.ResourceTuple("1", "RESOURCE_IN2", None)
        rt_out = PP.ResourceTuple("1", "RESOURCE_OUT", None)
        job1 = PP.Job(None, "job1", {}, [rt_in1, rt_in2], [rt_out])
        # If both inputs are MAKE_FAILED, the status should be
        #  JOB_FAILED
        self.grDict = {rt_in1: PP.Resource.MAKE_FAILED, rt_in2: PP.Resource.MAKE_FAILED, rt_out: PP.Resource.NOT_STARTED}
        self.pfList = [rt_in1, rt_in2]
        stat = job1.updateAndGetStatus(self.myGetResourceStatus, self.myPropagateFailure)
        self.assertEqual(stat, PP.Job.JOB_FAILED)


class TestNoProjectSupport(unittest.TestCase):
    global reportApi

    def testSubmitError(self):
        contents = 'hello'
        qryparms = {'qry': 'submitProject', 'contents': contents}
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        self.assertEqual(e.exception.__str__(), "No reply: Check project manager has been started")

    def testSubmitEmptyProject(self):
        qryparms = {'qry': 'submitProject'}
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        self.assertEqual(e.exception.__str__(), "Missing contents in submitProject")


class TestProjectSubmission(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)
        with open("sampleInstructions1.json", "rb") as fp:
            contents = fp.read().splitlines()
            while contents[0].startswith("//"):
                contents.pop(0)
            self.contents = "\n".join(contents)
        self.rmProcess = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        self.rmProcess.start()
        self.interface = DummyInterface()
        self.pm = PP.ProjectManager(TEST_ROOT, self.interface)

    def tearDown(self):
        self.pm.rm.shutDown()
        self.pm.close()
        self.rmProcess.join()

    def testInvalidSubmission(self):
        contents = "Bad JSON"
        ps = PP.ProjectSubmission(TEST_ROOT, contents, self.pm.rm)
        self.assertEqual(ps.ticket, getTicket(contents))
        with self.assertRaises(ValueError) as e:
            ps.analyzeSubmission()
        self.assertEqual(e.exception.__str__(), "No JSON object could be decoded")

    def testValidSubmission(self):
        ps = PP.ProjectSubmission(TEST_ROOT, self.contents, self.pm.rm)
        self.assertEqual(ps.ticket, getTicket(self.contents))
        ps.analyzeSubmission()
        jobs = ps.jobList
        ticket = ps.ticket
        self.pm.setJobs(ticket, jobs)
        self.assert_(ticket in self.pm.jobsByProject)
        for j in self.pm.jobsByProject[ticket]:
            self.assert_(isinstance(j, PP.Job))
            self.assertEqual(j.instructions, json.loads(self.contents))
        time.sleep(0.2)
        self.pm.deleteProject(ticket)

    def testCreateJson(self):
        # First find the number of jobs that should be submitted
        ps = PP.ProjectSubmission(TEST_ROOT, self.contents, self.pm.rm)
        ps.analyzeSubmission()
        nJobsCorrect = len(ps.jobList)
        # Generate the command to send to the project manager
        cmd = {"msg": "PROJECT", "reportRoot": TEST_ROOT, "contents": self.contents}
        ticket = getTicket(self.contents)
        rt = PP.makeResourceTuple(ticket, "INSTRUCTIONS")
        status, detailedStatus = self.pm.rm.getStatus(rt)
        self.assertEqual(status, PP.Resource.NOT_STARTED)
        # Submit for the first time
        respList = self.pm.handleSubmission(cmd)
        for resp in respList:
            if resp.type == "REPLY":
                if "error" in resp.data:
                    raise RuntimeError(resp.data["error"])
        self.assert_(os.path.isfile(os.path.join(TEST_ROOT, ticket, "json")))
        self.assert_(ticket in self.pm.activeProjects)
        status, detailedStatus = self.pm.rm.getStatus(rt)
        self.assertEqual(status, PP.Resource.MAKE_SUCCEEDED)
        nJobs = len(self.pm.jobsByProject[ticket])
        self.assertEqual(nJobs, nJobsCorrect)
        # Submit for the second time
        respList = self.pm.handleSubmission(cmd)
        for resp in respList:
            if resp.type == "REPLY":
                if "error" in resp.data:
                    raise RuntimeError(resp.data["error"])
        self.assert_(os.path.isfile(os.path.join(TEST_ROOT, ticket, "json")))
        self.assert_(ticket in self.pm.activeProjects)
        status, detailedStatus = self.pm.rm.getStatus(rt)
        self.assertEqual(status, PP.Resource.MAKE_SUCCEEDED)
        # Check no new jobs, since this is a duplicate of the first project
        self.assertEqual(nJobs, len(self.pm.jobsByProject[ticket]))
        # Now submit a (slightly) different project
        with open("sampleInstructions2.json", "rb") as fp:
            contents = fp.read().splitlines()
            while contents[0].startswith("//"):
                contents.pop(0)
            contents = "\n".join(contents)
        ticket2 = getTicket(contents)
        cmd = {"msg": "PROJECT", "reportRoot": TEST_ROOT, "contents": contents}
        respList = self.pm.handleSubmission(cmd)
        for resp in respList:
            if resp.type == "REPLY":
                if "error" in resp.data:
                    raise RuntimeError(resp.data["error"])
        self.assert_(ticket in self.pm.activeProjects)
        self.assert_(ticket2 in self.pm.activeProjects)
        self.assert_(os.path.isfile(os.path.join(TEST_ROOT, ticket2, "json")))
        # Check we now have twice the number of jobs
        # print "Jobs by project: ", self.pm.jobsByProject
        self.assertEqual(nJobs, len(self.pm.jobsByProject[ticket]))
        self.assertEqual(nJobs, len(self.pm.jobsByProject[ticket2]))
        time.sleep(0.2)
        self.pm.deleteProject(ticket)
        self.pm.deleteProject(ticket2)

    def testJobSequence1(self):
        cmd = {"msg": "PROJECT", "reportRoot": TEST_ROOT, "contents": self.contents}
        response = self.pm.handleSubmission(cmd)
        for r in response:
            ticket = r.data["ticket"]
        #print "Active projects:", self.pm.activeProjects
        while True:
            job = self.pm.findNextJob()
            if job is None:
                break
            self.verifyCorrectJob(job)
            # Create all output resources successfully and mark job as
            #  done
            for o in job.outputs:
                self.pm.rm.makeStarted(o)
                self.pm.rm.makeSucceeded(o)
            job.updateAndGetStatus()
        self.pm.deleteProject(ticket)
        time.sleep(0.1)

    def testJobSequence2(self):
        cmd = {"msg": "PROJECT", "reportRoot": TEST_ROOT, "contents": self.contents}
        response = self.pm.handleSubmission(cmd)
        for r in response:
            ticket = r.data["ticket"]
        # Now submit a second project
        with open("sampleInstructions2.json", "rb") as fp:
            contents = fp.read().splitlines()
            while contents[0].startswith("//"):
                contents.pop(0)
            contents = "\n".join(contents)
        cmd = {"msg": "PROJECT", "reportRoot": TEST_ROOT, "contents": contents}
        response = self.pm.handleSubmission(cmd)
        for r in response:
            ticket2 = r.data["ticket"]
        while True:
            job = self.pm.findNextJob()
            if job is None:
                break
            self.verifyCorrectJob(job)
            # Create all output resources successfully and mark job as
            #  done
            for o in job.outputs:
                self.pm.rm.makeStarted(o)
                self.pm.rm.makeSucceeded(o)
            job.updateAndGetStatus()
        self.pm.deleteProject(ticket)
        self.pm.deleteProject(ticket2)
        time.sleep(0.1)

    def verifyCorrectJob(self, job):
        # We must check the states of the input and output resources
        #  of this job and those of the other jobs for this ticket
        flag = "before"
        for j in self.pm.jobsByProject[job.ticket]:
            if j == job:
                flag = "after"
                self.assert_(j.status == PP.Job.JOB_READY_TO_RUN)
            elif flag == "before":
                self.assertIn(j.status, [PP.Job.JOB_RUNNING, PP.Job.JOB_SUCCEEDED, PP.Job.JOB_FAILED])
            elif flag == "after":
                self.assertIn(j.status, [None, PP.Job.JOB_AWAITING_RESOURCE, PP.Job.JOB_READY_TO_RUN])


class TestProjectSupport(unittest.TestCase):
    global reportApi, zmqContext

    @classmethod
    def setup_class(cls):
        xPort = PROJECT_SUBMISSION_PORT
        rPort = JOB_DISTRIBUTION_PORT
        sPort = JOB_COMPLETE_PORT
        cPort = STOP_WORKERS_PORT
        #cls.projectServer = subprocess.Popen(["python.exe",r"..\..\ReportGeneration\ProjectSupport.py",TEST_ROOT])

        cls.pmi = PP.ProjectManagerInterface(TEST_ROOT, os.getpid())
        cls.projectServer = mp.Process(target=cls.pmi.run)
        cls.projectServer.start()
        cls.command = zmqContext.socket(zmq.REQ)
        cls.command.connect("tcp://127.0.0.1:%d" % xPort)
        cls.controller = zmqContext.socket(zmq.SUB)
        cls.controller.connect("tcp://127.0.0.1:%d" % cPort)
        cls.controller.setsockopt(zmq.SUBSCRIBE, "INFO")
        cls.receiver = zmqContext.socket(zmq.SUB)
        cls.receiver.connect("tcp://127.0.0.1:%d" % rPort)
        cls.receiver.setsockopt(zmq.SUBSCRIBE, "")
        cls.sender = zmqContext.socket(zmq.PUSH)
        cls.sender.connect("tcp://127.0.0.1:%d" % sPort)

    @classmethod
    def teardown_class(cls):
        cls.projectServer.terminate()
        cls.projectServer.join()
        # cls.projectServer.wait()
        cls.controller.close()
        cls.sender.close()
        cls.receiver.close()
        cls.command.close()

    def setUp(self):
        self.rmProcess = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        self.rmProcess.start()
        self.rmSock = zmqContext.socket(zmq.REQ)
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def tearDown(self):
        PP.ResourceManagerProxy(self.rmSock).shutDown()
        self.rmSock.close()
        self.rmProcess.join()

    def testGetRoot(self):
        self.command.send(json.dumps({"msg": "GET_ROOT"}))
        result = json.loads(self.command.recv())
        self.assertEqual(result["root"], TEST_ROOT)

    def testSubmitProjectSuccessful(self):
        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)
        with open("sampleInstructions1.json", "rb") as fp:
            contents = fp.read().splitlines()
            while contents[0].startswith("//"):
                contents.pop(0)
            contents = "\n".join(contents)
        qryparms = {'qry': 'submitProject', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(
            reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        self.assert_('ticket' in result, "Ticket not found in result of submitProject")
        ticket = result["ticket"]
        try:
            self.assertEqual(result['contents'], contents, "Incorrect contents in submitProject")
            self.command.send(json.dumps({"msg": "ADD_WORKER", "workerIndex": 1}))
            result = json.loads(self.command.recv())
            # Single successful worker
            self.assertEqual(result["nWorkers"], 1)
            jobList = []
            try:
                while True:
                    socks = dict(poller.poll(timeout=500))
                    if socks.get(self.receiver) == zmq.POLLIN:
                        cmd = self.receiver.recv()
                        pos = cmd.find("\n")
                        workerIndex = int(cmd[:pos])
                        job = json.loads(cmd[pos + 1:])
                        jobNum = job["jobNum"]
                        jobList.append(jobNum)
                        reply = {"msg": "SUCCESS", "result": "OK", "jobNum": jobNum, "workerIndex": workerIndex, "available": True}
                        self.sender.send(json.dumps(reply))
                    else:
                        break
                self.command.send(json.dumps(
                    {"msg": "GET_PROJECT_STATUS", "ticket": ticket}))
                result = json.loads(self.command.recv())
                self.assertEqual(result["project"], "PROJECT_COMPLETE")
                for j in result['jobs']:
                    self.assertEqual(j['status'], 'JOB_SUCCEEDED')
                self.assertEqual(len(jobList), 11)  # Early failure expected
            finally:
                self.command.send(json.dumps({"msg": "REMOVE_WORKER", "workerIndex": workerIndex}))
                result = json.loads(self.command.recv())
                self.assertEqual(result["nWorkers"], 0)
        finally:
            self.command.send(json.dumps({"msg": "DELETE_PROJECT", "ticket": ticket}))
            result = json.loads(self.command.recv())
            self.assertEqual(result['status']['found'], True)

    def testSubmitProjectFailureNWorkers(self):
        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)

        for N in range(1, 11, 3):
            with open("sampleInstructions1.json", "rb") as fp:
                contents = fp.read().splitlines()
                while contents[0].startswith("//"):
                    contents.pop(0)
                contents = "\n".join(contents)
            qryparms = {'qry': 'submitProject', 'contents': contents}
            # Submit a project via the report server
            result = raiseOnError(
                reportApi.get("gdu", "1.0", "ReportGen", qryparms))
            self.assert_('ticket' in result, "Ticket not found in result of submitProject")
            ticket = result["ticket"]
            try:
                self.assertEqual(result['contents'], contents, "Incorrect contents in submitProject")
                for w in range(N):
                    self.command.send(json.dumps({"msg": "ADD_WORKER", "workerIndex": w}))
                    result = json.loads(self.command.recv())
                self.assertEqual(result["nWorkers"], N)
                jobList = []
                try:
                    while True:
                        socks = dict(poller.poll(timeout=500))
                        if socks.get(self.receiver) == zmq.POLLIN:
                            cmd = self.receiver.recv()
                            pos = cmd.find("\n")
                            workerIndex = int(cmd[:pos])
                            job = json.loads(cmd[pos + 1:])
                            jobNum = job["jobNum"]
                            jobList.append(jobNum)
                            time.sleep(0.1)
                            reply = {"msg": "FAILURE", "result": "OK", "jobNum": jobNum, "workerIndex": workerIndex, "available": True}
                            self.sender.send(json.dumps(reply))
                        else:
                            break
                    self.command.send(json.dumps(
                        {"msg": "GET_PROJECT_STATUS", "ticket": ticket}))
                    result = json.loads(self.command.recv())
                    self.assertEqual(result["project"], "PROJECT_FAILED")
                    self.assertEqual(len(jobList), min(N, 6))
                finally:
                    for w in range(N):
                        self.command.send(json.dumps({"msg": "REMOVE_WORKER", "workerIndex": w}))
                        result = json.loads(self.command.recv())
                    self.assertEqual(result["nWorkers"], 0)
            finally:
                self.command.send(json.dumps({"msg": "DELETE_PROJECT", "ticket": ticket}))
                result = json.loads(self.command.recv())
                self.assertEqual(result['status']['found'], True)

    def testSubmitProjectFailure(self):
        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)
        with open("sampleInstructions1.json", "rb") as fp:
            contents = fp.read().splitlines()
            while contents[0].startswith("//"):
                contents.pop(0)
            contents = "\n".join(contents)
        qryparms = {'qry': 'submitProject', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(
            reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        self.assert_('ticket' in result, "Ticket not found in result of submitProject")
        ticket = result["ticket"]
        try:
            self.assertEqual(result['contents'], contents, "Incorrect contents in submitProject")
            self.command.send(json.dumps({"msg": "ADD_WORKER", "workerIndex": 1}))
            result = json.loads(self.command.recv())
            # Single unsuccessful worker
            self.assertEqual(result["nWorkers"], 1)
            jobList = []
            try:
                while True:
                    socks = dict(poller.poll(timeout=500))
                    if socks.get(self.receiver) == zmq.POLLIN:
                        cmd = self.receiver.recv()
                        pos = cmd.find("\n")
                        workerIndex = int(cmd[:pos])
                        job = json.loads(cmd[pos + 1:])
                        jobNum = job["jobNum"]
                        jobList.append(jobNum)
                        # print "Running", job["args"][0], " JobNumber =",jobNum
                        reply = {"msg": "FAILURE", "result": "OK", "jobNum": jobNum, "workerIndex": workerIndex, "available": True}
                        self.sender.send(json.dumps(reply))
                    else:
                        break
                self.command.send(json.dumps(
                    {"msg": "GET_PROJECT_STATUS", "ticket": ticket}))
                result = json.loads(self.command.recv())
                self.assertEqual(result["project"], "PROJECT_FAILED")
                self.assertEqual(len(jobList), 1)  # Early failure expected
            finally:
                self.command.send(json.dumps({"msg": "REMOVE_WORKER", "workerIndex": workerIndex}))
                result = json.loads(self.command.recv())
                self.assertEqual(result["nWorkers"], 0)
        finally:
            self.command.send(json.dumps({"msg": "DELETE_PROJECT", "ticket": ticket}))
            result = json.loads(self.command.recv())
            self.assertEqual(result['status']['found'], True)

    def testSubmitInvalidProject(self):
        contents = "Invalid JSON"
        qryparms = {'qry': 'submitProject', 'contents': contents}
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        self.assert_(
            e.exception.__str__().startswith("Project Manager Exception"))

    def testSubmitEmptyProject(self):
        qryparms = {'qry': 'submitProject'}
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        self.assert_(e.exception.__str__(
            ).startswith("Missing contents in submitProject"))

    def testDownloadInstructions(self):
        return
        instructions = os.path.join('.', 'mytest.json')

        with open(instructions, "rb") as fp:
            contents = fp.read().splitlines()

        while contents[0].startswith("//"):
            contents.pop(0)
        # Check this is valid JSON
        contents = "\n".join(contents)
        json.loads(contents)    # Throws exception on faulty JSON

        # Get the secure hash for prepending
        qryparms = {'qry': 'download', 'content': contents,  'filename': 'instructions.json'}
        contents = raiseOnError(
            reportApi.get("gdu", "1.0", "ReportGen", qryparms))

        with file(os.path.join('.', 'validated.json'), "rb") as op:
            assert(contents == op.read())


class TestResources(unittest.TestCase):
    global zmqContext, reportApi
    byProject = ["INSTRUCTIONS", "SUMMARY_MAP", "PROJECT_REPORT"]
    byRegion = ["BASE_MAP", "PATH_MAP", "MARKER_MAP", "COMPOSITE_MAP", "REGIONAL_REPORT"]

    def setUp(self):
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def testResourceTuple(self):
        for p in self.byProject:
            ticket = random.randrange(1000000)
            self.assertEqual(PP.makeResourceTuple(ticket, p), (ticket, p, None))
            with self.assertRaises(ValueError) as e:
                PP.makeResourceTuple(ticket, p, 1)
            self.assertEqual(e.exception.__str__(), "Invalid resource type with a specified region")
        for r in self.byRegion:
            ticket = random.randrange(1000000)
            region = random.randrange(10)
            self.assertEqual(PP.makeResourceTuple(ticket, r, region), (ticket, r, region))
            with self.assertRaises(ValueError) as e:
                PP.makeResourceTuple(ticket, r)
            self.assertEqual(e.exception.__str__(), "Invalid resource type with no region")

    def testResourceBaseName(self):
        for p in self.byProject:
            ticket = random.randrange(1000000)
            rt = PP.makeResourceTuple(ticket, p)
            self.assertEqual(PP.resourceBaseName(rt), os.path.join("%s" % ticket, p))
        for r in self.byRegion:
            ticket = random.randrange(1000000)
            region = 0
            rt = PP.makeResourceTuple(ticket, r, region)
            self.assertEqual(PP.resourceBaseName(rt), os.path.join("%s" % ticket, "%s.%d" % (r, region)))

    def testCreateResourceSucceeded(self):
        proc = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        proc.start()
        socket = zmqContext.socket(zmq.REQ)
        rm = PP.ResourceManagerProxy(socket)
        try:
            ticket = random.randrange(1000000)
            self.assert_(not os.path.exists(os.path.join(TEST_ROOT, "%s" % ticket)))
            rt = PP.makeResourceTuple(ticket, "SUMMARY_MAP")
            status, detailedStatus = rm.makeStarted(rt)
            self.assertEqual(status, PP.Resource.IN_PROGRESS)
            status, ds1 = rm.getStatus(rt)
            self.assertEqual(status, PP.Resource.IN_PROGRESS)
            self.assertEqual(detailedStatus, ds1)
            status, detailedStatus = rm.makeSucceeded(rt, doneMsg="completed")
            self.assertEqual(status, PP.Resource.MAKE_SUCCEEDED)
            self.assertDictContainsSubset(
                {"done": "completed"}, detailedStatus)
        finally:
            rm.shutDown()
            socket.close()
            proc.join()
        self.assert_(os.path.exists(os.path.join(TEST_ROOT, "%s" % ticket, "SUMMARY_MAP.ok")))

    def testCreateResourceFailed(self):
        proc = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        proc.start()
        socket = zmqContext.socket(zmq.REQ)
        rm = PP.ResourceManagerProxy(socket)
        try:
            ticket = random.randrange(1000000)
            self.assert_(not os.path.exists(os.path.join(TEST_ROOT, "%s" % ticket)))
            rt = PP.makeResourceTuple(ticket, "SUMMARY_MAP")
            status, detailedStatus = rm.makeStarted(rt)
            self.assertEqual(status, PP.Resource.IN_PROGRESS)
            status, detailedStatus = rm.makeFailed(rt, errorMsg="badly")
            self.assertEqual(status, PP.Resource.MAKE_FAILED)
            self.assertDictContainsSubset({"error": "badly"}, detailedStatus)
        finally:
            rm.shutDown()
            socket.close()
            proc.join()
        self.assert_(os.path.exists(os.path.join(TEST_ROOT, "%s" % ticket, "SUMMARY_MAP.err")))

    def testRecoverResources(self):
        proc = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        proc.start()
        socket = zmqContext.socket(zmq.REQ)
        rm = PP.ResourceManagerProxy(socket)

        try:
            ticket0 = 0
            rt0 = PP.makeResourceTuple(ticket0, "SUMMARY_MAP")
            status0, detailedStatus0 = rm.getStatus(rt0)
            self.assertEqual(status0, PP.Resource.NOT_STARTED)

            ticket1 = 1
            rt1 = PP.makeResourceTuple(ticket1, "SUMMARY_MAP")
            status1, detailedStatus1 = rm.makeStarted(rt1)
            self.assertEqual(status1, PP.Resource.IN_PROGRESS)

            ticket2 = 2
            rt2 = PP.makeResourceTuple(ticket2, "SUMMARY_MAP")
            status2, detailedStatus2 = rm.makeStarted(rt2)
            self.assertEqual(status2, PP.Resource.IN_PROGRESS)
            status2, detailedStatus2 = rm.makeSucceeded(rt2)
            self.assertEqual(status2, PP.Resource.MAKE_SUCCEEDED)

            ticket3 = 3
            rt3 = PP.makeResourceTuple(ticket3, "SUMMARY_MAP")
            status3, detailedStatus3 = rm.makeStarted(rt3)
            self.assertEqual(status3, PP.Resource.IN_PROGRESS)
            status3, detailedStatus3 = rm.makeFailed(rt3)
            self.assertEqual(status3, PP.Resource.MAKE_FAILED)
        finally:
            rm.shutDown()
            socket.close()
            proc.join()
        # At this point the old data manager has been destroyed, but the records
        #  should still be on disk. We now try to retreive the status from disk
        proc = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        proc.start()
        socket = zmqContext.socket(zmq.REQ)
        rm = PP.ResourceManagerProxy(socket)

        try:
            status0_, detailedStatus0_ = rm.getStatus(rt0)
            self.assertEqual(status0, status0_)
            self.assertEqual(detailedStatus0, detailedStatus0_)
            status1_, detailedStatus1_ = rm.getStatus(rt1)
            self.assertEqual(status1, status1_)
            self.assertEqual(detailedStatus1, detailedStatus1_)
            status2_, detailedStatus2_ = rm.getStatus(rt2)
            self.assertEqual(status2, status2_)
            self.assertEqual(detailedStatus2, detailedStatus2_)
            status3_, detailedStatus3_ = rm.getStatus(rt3)
            self.assertEqual(status3, status3_)
            self.assertEqual(detailedStatus3, detailedStatus3_)
        finally:
            rm.shutDown()
            socket.close()
            proc.join()

    def testUpdateDetailedStatus(self):
        proc = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        proc.start()
        socket = zmqContext.socket(zmq.REQ)
        rm = PP.ResourceManagerProxy(socket)
        try:
            ticket = random.randrange(1000000)
            rt = PP.makeResourceTuple(ticket, "SUMMARY_MAP")
            status, detailedStatus = rm.makeStarted(rt)
            self.assertEqual(status, PP.Resource.IN_PROGRESS)
            status, detailedStatus = rm.addDetail(rt, {"detail1": "one"})
            self.assertEqual(status, PP.Resource.IN_PROGRESS)
            status, detailedStatus = rm.addDetail(rt, {"detail2": "two"})
            self.assertEqual(status, PP.Resource.IN_PROGRESS)
            status, detailedStatus = rm.makeSucceeded(rt)
            self.assertEqual(status, PP.Resource.MAKE_SUCCEEDED)
        finally:
            rm.shutDown()
            socket.close()
            proc.join()
        self.assert_(os.path.exists(os.path.join(TEST_ROOT, "%s" % ticket, "SUMMARY_MAP.ok")))
        self.assertDictContainsSubset({"detail1": "one", "detail2": "two"}, detailedStatus)
        self.assertIn("start", detailedStatus)
        self.assertIn("end", detailedStatus)


class TestWorker(unittest.TestCase):
    """Test instantiation and initialization of workers"""
    def setUp(self):
        self.context = zmq.Context()
        self.srcPort = JOB_DISTRIBUTION_PORT
        self.source = self.context.socket(zmq.PUB)
        self.source.bind("tcp://127.0.0.1:%d" % self.srcPort)
        self.sinkPort = JOB_COMPLETE_PORT
        self.sink = self.context.socket(zmq.PULL)
        self.sink.bind("tcp://127.0.0.1:%d" % self.sinkPort)
        self.controllerPort = STOP_WORKERS_PORT
        self.controller = self.context.socket(zmq.PUB)
        self.controller.bind("tcp://127.0.0.1:%d" % self.controllerPort)

    def tearDown(self):
        self.source.close()
        self.sink.close()
        self.controller.close()
        self.context.term()

    def testCreateWorkerInThread(self):
        index = 1
        self.t1 = threading.Thread(target=PP.Worker(index, self.srcPort, self.sinkPort, self.controllerPort, os.getpid()).run)
        self.t1.start()
        # Wait for worker to start
        result = json.loads(self.sink.recv())
        self.assertEqual(result["msg"], "STARTING")
        self.assertEqual(result["workerIndex"], index)
        # Send message to kill worker
        self.controller.send("KILL")
        result = json.loads(self.sink.recv())
        # Check that worker has died
        self.assertEqual(result["msg"], "TERMINATING")
        self.assertEqual(result["workerIndex"], index)
        # Wait for thread to stop
        self.t1.join()

    def testCreateWorkersInThreads(self):
        nWorkers = 4
        threads = []
        for index in range(nWorkers):
            t = threading.Thread(target=PP.Worker(index, self.srcPort, self.sinkPort, self.controllerPort, os.getpid()).run)
            t.start()
            threads.append(t)
        # Check all workers start
        indices = []
        for index in range(nWorkers):
            result = json.loads(self.sink.recv())
            # print "T", result
            self.assertEqual(result["msg"], "STARTING")
            indices.append(result["workerIndex"])
        self.assertEqual(sorted(indices), range(nWorkers), "Not all workers started")
        # Send kill message
        self.controller.send("KILL")
        # Check all workers terminate
        indices = []
        for index in range(nWorkers):
            result = json.loads(self.sink.recv())
            # print "T", result
            self.assertEqual(result["msg"], "TERMINATING")
            indices.append(result["workerIndex"])
        self.assertEqual(sorted(indices), range(nWorkers), "Not all workers terminated")
        # Wait for threads to stop
        for t in threads:
            t.join()

    def testCreateWorkerInProcess(self):
        index = 7
        self.t1 = mp.Process(target=PP.Worker(index, self.srcPort, self.sinkPort, self.controllerPort, os.getpid()).run)
        self.t1.start()
        # Wait for worker to start
        result = json.loads(self.sink.recv())
        self.assertEqual(result["msg"], "STARTING")
        self.assertEqual(result["workerIndex"], index)
        # Send message to kill worker
        self.controller.send("KILL")
        result = json.loads(self.sink.recv())
        # Check that worker has died
        self.assertEqual(result["msg"], "TERMINATING")
        self.assertEqual(result["workerIndex"], index)
        # Wait for thread to stop
        self.t1.join()

    def testCreateWorkersInProcesses(self):
        nWorkers = 4
        threads = []
        for index in range(nWorkers):
            t = mp.Process(target=PP.Worker(index, self.srcPort, self.sinkPort, self.controllerPort, os.getpid()).run)
            t.start()
            threads.append(t)
        # Check all workers start
        indices = []
        for index in range(nWorkers):
            result = json.loads(self.sink.recv())
            # print "P", result
            self.assertEqual(result["msg"], "STARTING")
            indices.append(result["workerIndex"])
        self.assertEqual(sorted(indices), range(nWorkers), "Not all workers started")
        # Send kill message
        self.controller.send("KILL")
        # Check all workers terminate
        indices = []
        for index in range(nWorkers):
            result = json.loads(self.sink.recv())
            # print "P", result
            self.assertEqual(result["msg"], "TERMINATING")
            indices.append(result["workerIndex"])
        self.assertEqual(sorted(indices), range(nWorkers), "Not all workers terminated")
        # Wait for threads to stop
        for t in threads:
            t.join()

    def sendWork(self, workerIndex, paramDict):
        self.source.send(("%d\n" % workerIndex) + json.dumps(paramDict))

    def testSendJobToWorkerInProcess(self):
        index = 3
        self.t1 = mp.Process(target=PP.Worker(index, self.srcPort, self.sinkPort, self.controllerPort, os.getpid()).run)
        self.t1.start()
        # Wait for worker to start
        result = json.loads(self.sink.recv())
        self.assertEqual(result["msg"], "STARTING")
        self.assertEqual(result["workerIndex"], index)

        jobNum = random.randrange(1000)
        x = random.randrange(1000)
        self.sendWork(index, dict(msg="JOB", jobNum=jobNum, job="SQUARE", args=(x,)))
        result = json.loads(self.sink.recv())
        self.assertEqual(result["msg"], "SUCCESS")
        self.assertEqual(result["jobNum"], jobNum)
        self.assertEqual(result["result"], x * x)
        self.assertEqual(result["workerIndex"], index)

        self.sendWork(index, dict(msg="BAD"))
        result = json.loads(self.sink.recv())
        self.assertEqual(result["msg"], "FAILURE")
        self.assertEqual(result["error"], "Invalid command")
        self.assertEqual(result["workerIndex"], index)

        self.sendWork(index, dict(msg="JOB", jobNum=123, job="UNKNOWN"))
        result = json.loads(self.sink.recv())
        self.assertEqual(result["msg"], "FAILURE")
        self.assertEqual(result["error"], "No such job type")
        self.assertEqual(result["workerIndex"], index)

        self.sendWork(index, dict(msg="JOB", jobNum=456, job="SQUARE", args=("invalid",)))
        result = json.loads(self.sink.recv())
        self.assertEqual(result["msg"], "FAILURE")
        self.assertEqual(result["error"], "Exception in job")
        self.assertIn("TypeError", result["traceback"])
        self.assertEqual(result["workerIndex"], index)

        # Send message to kill worker
        self.controller.send("KILL")
        result = json.loads(self.sink.recv())
        # Check that worker has died
        self.assertEqual(result["msg"], "TERMINATING")
        self.assertEqual(result["workerIndex"], index)
        # Wait for thread to stop
        self.t1.join()

    def testSendJobsToWorkersInProcesses(self):
        nWorkers = 4
        threads = []
        workersAvailable = set()
        for index in range(nWorkers):
            t = mp.Process(target=PP.Worker(index, self.srcPort, self.sinkPort, self.controllerPort, os.getpid()).run)
            t.start()
            threads.append(t)
        # Check all workers start
        for index in range(nWorkers):
            result = json.loads(self.sink.recv())
            # print "P", result
            self.assertEqual(result["msg"], "STARTING")
            workersAvailable.add(result["workerIndex"])
        self.assertEqual(workersAvailable, set(range(nWorkers)), "Not all workers started")

        poller = zmq.Poller()
        poller.register(self.sink, zmq.POLLIN)
        jobNum = 0
        nJobs = 3 * nWorkers + 1

        jobsDone = []
        tStart = time.clock()
        # Send out nJobs jobs to the collection of workers
        while True:
            while workersAvailable and jobNum < nJobs:
                self.sendWork(workersAvailable.pop(), dict(msg="JOB",jobNum=jobNum,job="SLEEP",args=(1.0,)))
                jobNum += 1
            socks = dict(poller.poll())
            if socks.get(self.sink) == zmq.POLLIN:
                result = json.loads(self.sink.recv())
                self.assertEqual(result["msg"], "SUCCESS")
                jobsDone.append(result["jobNum"])
                workersAvailable.add(result["workerIndex"])
                if jobNum == nJobs and len(workersAvailable) == nWorkers:
                    break

        self.assertEqual(sorted(jobsDone), range(nJobs), "Not all jobs were done")
        timeTaken = time.clock() - tStart
        self.assertAlmostEqual(timeTaken, math.ceil(float(nJobs) / nWorkers), delta=0.5,
                               msg="Unexpected time used for computation")
        # Send kill message
        self.controller.send("KILL")
        # Check all workers terminate
        for index in range(nWorkers):
            result = json.loads(self.sink.recv())
            # print "P", result
            self.assertEqual(result["msg"], "TERMINATING")
            workersAvailable.remove(result["workerIndex"])
        self.assert_(len(workersAvailable) ==0, "Not all workers terminated")
        # Wait for threads to stop
        for t in threads:
            t.join()


class TestResourceManager(unittest.TestCase):
    global zmqContext

    def setUp(self):
        self.rmProc = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        self.rmProc.start()
        self.socket = zmqContext.socket(zmq.REQ)
        self.rm = PP.ResourceManagerProxy(self.socket)

    def tearDown(self):
        self.rm.shutDown()
        self.socket.close()
        self.rmProc.terminate()
        self.rmProc.join()

    def testBadCommand(self):
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(self.rm.invalid())
        self.assertIn("Remote error Unknown function: invalid", e.exception.__str__())


class TestReportWorker(unittest.TestCase):
    global reportApi, zmqContext
    # PROJECT_SUBMISSION_PORT
    # JOB_DISTRIBUTION_PORT
    # JOB_COMPLETE_PORT
    # STOP_WORKERS_PORT
    # RESOURCE_MANAGER_PORT

    def setUp(self):
        shutil.rmtree(TEST_ROOT, ignore_errors=True)
        self.rmProcess = mp.Process(target=PP.ResourceManager(TEST_ROOT, os.getpid()).run)
        self.rmProcess.start()

        pmi = PP.ProjectManagerInterface(TEST_ROOT, os.getpid())
        self.projectServer = mp.Process(target=pmi.run)
        self.projectServer.start()

        self.command = zmqContext.socket(zmq.REQ)
        self.command.connect("tcp://127.0.0.1:%d" % PROJECT_SUBMISSION_PORT)

    def tearDown(self):
        self.command.close()
        self.projectServer.terminate()
        self.rmProcess.terminate()
        self.projectServer.join()
        self.rmProcess.join()

    def testStartAndStopWorkers(self):
        # Start some workers
        nWorkers = 4
        workerProcs = []
        for w in range(nWorkers):
            t = mp.Process(target=PP.Worker(w, JOB_DISTRIBUTION_PORT, JOB_COMPLETE_PORT, STOP_WORKERS_PORT, os.getpid()).run)
            workerProcs.append(t)
            t.start()
        # Wait for workers to start
        time.sleep(2.0)
        self.command.send(json.dumps({"msg": "GET_WORKER_STATS"}))
        reply = json.loads(self.command.recv())
        self.assertEqual(sorted(reply["workers"]), range(nWorkers))
        self.command.send(json.dumps({"msg": "STOP_WORKERS"}))
        reply = json.loads(self.command.recv())
        time.sleep(2.0)
        self.command.send(json.dumps({"msg": "GET_WORKER_STATS"}))
        reply = json.loads(self.command.recv())
        self.assertEqual(reply["workers"], [])
        for p in workerProcs:
            p.terminate()
            p.join()

    def testJobAllocation(self):
        # Start some workers
        nWorkers = 8
        self.command.send(
            json.dumps({"msg": "SET_POOL_SIZE", "poolSize": nWorkers}))
        json.loads(self.command.recv())

        #self.command.send(json.dumps({"msg": "GET_WORKER_STATS"}))
        #json.loads(self.command.recv())

        with open("sampleInstructions1.json", "rb") as fp:
            contents = fp.read().splitlines()
            while contents[0].startswith("//"):
                contents.pop(0)
            contents = "\n".join(contents)
        qryparms = {'qry': 'submitProject', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(
            reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        ticket1 = result["ticket"]

        with open("sampleInstructions2.json", "rb") as fp:
            contents = fp.read().splitlines()
            while contents[0].startswith("//"):
                contents.pop(0)
            contents = "\n".join(contents)
        qryparms = {'qry': 'submitProject', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(
            reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        ticket2 = result["ticket"]

        while True:
            self.command.send(json.dumps({"msg": "GET_WORKER_STATS"}))
            reply = json.loads(self.command.recv())
            nWorkers = len(reply["workers"])
            nWorkersFree = reply["nWorkersFree"]
            self.command.send(json.dumps({"msg": "GET_STATISTICS"}))
            reply = json.loads(self.command.recv())
            # Calculate pending jobs
            jobs = Counter(reply["jobs"])
            jobsDispatched = Counter(reply["jobsDispatched"])
            jobsFailed = Counter(reply["jobsFailed"])
            jobsSuccessful = Counter(reply["jobsSuccessful"])
            jobsCrashed = Counter(reply["jobsCrashed"])
            jobsLeft = sum((jobs - jobsFailed - jobsSuccessful - jobsCrashed).values())
            # print sum(jobs.values()), sum(jobsDispatched.values()), sum(jobsSuccessful.values()), sum(jobsFailed.values()), sum(jobsCrashed.values()), jobsLeft, nWorkers, nWorkersFree
            if jobsLeft == 0 and nWorkers == nWorkersFree:
                break
            time.sleep(1.0)
        self.assertEqual(sum(jobs.values()), sum(jobsDispatched.values()))
        self.assertEqual(sum(jobs.values()), sum(jobsSuccessful.values()))
        self.assertEqual(sum(jobsFailed.values()), 0)
        self.assertEqual(sum(jobsCrashed.values()), 0)
        # print "Time taken", time.clock()-start
        self.command.send(json.dumps({"msg": "SET_POOL_SIZE", "poolSize": 0}))
        reply = json.loads(self.command.recv())
        time.sleep(1.0)
        self.command.send(json.dumps({"msg": "STOP_WORKERS"}))
        reply = json.loads(self.command.recv())
        while True:
            self.command.send(json.dumps({"msg": "GET_WORKER_STATS"}))
            reply = json.loads(self.command.recv())
            if len(reply["workers"]) == 0:
                break
            time.sleep(1.0)

        self.command.send(json.dumps({"msg": "GET_PROJECT_STATUS", "ticket": ticket1}))
        reply = json.loads(self.command.recv())
        self.assertEqual(reply["project"], "PROJECT_COMPLETE")
        for j in reply["jobs"]:
            self.assertEqual(j["status"], "JOB_SUCCEEDED")

        self.command.send(json.dumps({"msg": "GET_PROJECT_STATUS", "ticket": ticket2}))
        reply = json.loads(self.command.recv())
        self.assertEqual(reply["project"], "PROJECT_COMPLETE")
        for j in reply["jobs"]:
            self.assertEqual(j["status"], "JOB_SUCCEEDED")


def setup_module():
    global reportServer, reportApi, zmqContext

    reportServer = subprocess.Popen(["python.exe", r"..\..\ReportGeneration\reportServer.py", "-r", TEST_ROOT, "--no-pmstart"],
                                    stderr=file("NUL", "w"))
    reportApi = ReportApiService()
    reportApi.csp_url = "http://localhost:5200"
    # reportApi.ticket_url = P3Api.csp_url + "/rest/sec/dummy/1.0/Admin/"
    # reportApi.identity = "85490338d7412a6d31e99ef58bce5de6"
    # reportApi.psys = "APITEST"
    # reportApi.rprocs = '["ReportGen"]'
    reportApi.debug = False
    zmqContext = zmq.Context()


def teardown_module():
    global reportServer, reportApi, zmqContext
    reportServer.terminate()
    reportServer.wait()
    zmqContext.term()

if __name__ == '__main__':
    unittest.main()
