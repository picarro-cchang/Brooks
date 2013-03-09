# Need a ProjectManager which receives projects defined by instruction files

# Once a project is received, it is broken down into a series of tasks which have to be performed to complete the project
# Each task is submitted to a task manager which is responsible for submitting the task to a ready-to-run queue or if it cannot run because it is awaiting a resource
# Each task specifies a list of resources which need to be present before it can run. Note that more than one task can access the resource once it becomes available.
# A job is placed on the ready-to-run queue if all resources it needs are available. A job also specifies the resources it will produce on successful completion.
# When a job completes or encounters an error, it informs the task manager of the resources that have become available or are in an error state.

# Note that it is possible to determine if a resource is available or not by going to external storage and checking for its existence. This means that even if we do
#  not get notified by a task that the resource has become available, we can still find this out via a slow operation.

import cPickle
from collections import Counter, deque, OrderedDict
import json
import multiprocessing as mp
import os
import psutil
from Queue import Queue
import shutil
import sys
import threading
import time
import traceback
import zmq
from ReportCommon import PROJECT_SUBMISSION_PORT, JOB_DISTRIBUTION_PORT, JOB_COMPLETE_PORT
from ReportCommon import STOP_WORKERS_PORT, RESOURCE_MANAGER_PORT
from ReportCommon import getTicket, ResourceTuple, ResponseTuple
from ReportGenerator import ReportGenerator

if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(os.path.abspath(appPath))[0]

DEFAULT_ROOT = os.path.join(appDir, 'static', 'ReportGen')


def makeResourceTuple(ticket, type, region=None):
    byProject = ["INSTRUCTIONS", "SUMMARY_MAP", "PROJECT_REPORT"]
    byRegion = ["BASE_MAP", "PATH_MAP", "MARKER_MAP", "COMPOSITE_MAP",
                "REGIONAL_REPORT"]
    if region is None:
        if type not in byProject:
            raise ValueError("Invalid resource type with no region")
    else:
        if type not in byRegion:
            raise ValueError("Invalid resource type with a specified region")
    return ResourceTuple(ticket, type, region)


def merge_dictionary(dst, src):
    """Merge src dictionary into the destination, so that the destination finally contains
    all the key-value pairs in the source as well as all of its original contents which have
    not been replaced"""
    stack = [(dst, src)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) and isinstance(current_dst[key], dict):
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst


def mergeDictList(dictList):
    """Merge the dictionaries in dictList"""
    result = {}
    for s in dictList:
        result = merge_dictionary(result, s)
    return result


def resourceBaseName(resourceTuple):
    region = resourceTuple.region
    if region is not None:
        return os.path.join("%s" % resourceTuple.ticket, "%s.%d" % (resourceTuple.type, resourceTuple.region))
    else:
        return os.path.join("%s" % resourceTuple.ticket, "%s" % (resourceTuple.type,))


class Job(object):
    JOB_AWAITING_RESOURCE = 0
    JOB_READY_TO_RUN = 1
    JOB_RUNNING = 2
    JOB_SUCCEEDED = 3
    JOB_FAILED = -1
    statusText = {JOB_AWAITING_RESOURCE: "JOB_AWAITING_RESOURCE",
                  JOB_READY_TO_RUN: "JOB_READY_TO_RUN",
                  JOB_RUNNING: "JOB_RUNNING",
                  JOB_SUCCEEDED: "JOB_SUCCEEDED",
                  JOB_FAILED: "JOB_FAILED"}

    def __init__(self, resourceManager, name, paramDict, inputs=[], outputs=[], instructions=None):
        """Create a job specifying lists of input and output ResourceTuples"""
        self.rm = resourceManager
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.paramDict = paramDict
        self.instructions = instructions
        self.status = None
        ticket = None
        for rt in inputs + outputs:
            if ticket is None:
                ticket = rt.ticket
            elif ticket != rt.ticket:
                raise ValueError(
                    "All resources for a job must have same ticket.")
        self.ticket = ticket
        self.workerIndex = None

    def __repr__(self):
        return "Job: %s, Status: %s" % (self.name, self.statusText.get(self.status, None))

    __str__ = __repr__

    def asDict(self):
        "Return as a dictionary for JSON serialization"
        return dict(
            name=self.name, status=self.statusText.get(self.status, ""),
                    workerIndex=self.workerIndex)

    def logResult(self, results):
        "Copy results to the detailedStatus for all output resources"
        for o in self.outputs:
            self.rm.addDetail(o, results)

    def jobStarted(self):
        "Set all output resources to the IN_PROGRESS state"
        for o in self.outputs:
            self.rm.makeStarted(o)
        return self.updateAndGetStatus()

    def jobSucceeded(self, workerIndex=None):
        "Set all output resources to the MAKE_SUCCEEDED state"
        for o in self.outputs:
            self.rm.makeSucceeded(o)
        self.workerIndex = workerIndex
        return self.updateAndGetStatus()

    def jobFailed(self, workerIndex=None):
        "Set all output resources to the MAKE_FAILED state"
        for o in self.outputs:
            self.rm.makeFailed(o)
        self.workerIndex = workerIndex
        return self.updateAndGetStatus()

    def setStatus(self, status):
        self.status = status

    def propagate_failure(self, badResources):
        """Some input resource has not been made successfully. Propagate this failure to all outputs"""
        for rt in self.outputs:
            self.rm.makeStarted(rt)
            self.rm.makeFailed(
                rt, errorMsg="Input resource(s) not made successfully")

    def updateAndGetStatus(self, getResourceStatus=None, propagate_failure=None):
        """Determine the status of a job. i.e., check its input and output resources lists to see
        if the job is awaiting resources, is ready to run, is running, has successfully completed, or has
        failed. Update self.status appropriately.

        The code tries to limit the amount of work needed by making use of the current status, if available.
        If the current status is None, however, it will determine the status from scratch.

        If it determines that some input resource is in the MAKE_FAILED state, it propagates the failure to
        all the output resources and marks the job as having failed.
        """
        # The getResourceStatus and propagate_failure can be changed for testing purposes
        if getResourceStatus is None:
            getResourceStatus = self.rm.getStatus
        if propagate_failure is None:
            propagate_failure = self.propagate_failure

        if self.status in [self.JOB_SUCCEEDED, self.JOB_FAILED]:
            return self.status
        if self.status in [None, self.JOB_READY_TO_RUN, self.JOB_RUNNING]:
            allDone = True
            for rt in self.outputs:
                rs, deailedStatus = getResourceStatus(rt)
                if rs == Resource.MAKE_FAILED:
                    self.status = self.JOB_FAILED
                    return self.status
                if rs == Resource.IN_PROGRESS:
                    self.status = self.JOB_RUNNING
                    return self.status
                if rs != Resource.MAKE_SUCCEEDED:
                    allDone = False
            if allDone:
                self.status = self.JOB_SUCCEEDED
                return self.status
        if self.status in [None, self.JOB_AWAITING_RESOURCE]:
            ready = True
            failed = []
            for rt in self.inputs:
                rs, detailedStatus = getResourceStatus(rt)
                if rs == Resource.MAKE_FAILED:
                    failed.append(rt)
                elif rs in [Resource.NOT_STARTED, Resource.IN_PROGRESS]:
                    ready = False
                    break
            if failed:
                propagate_failure(failed)
                self.status = self.JOB_FAILED
            else:
                self.status = self.JOB_READY_TO_RUN if ready else self.JOB_AWAITING_RESOURCE
        return self.status


class ProjectManagerInterface(object):
    """Handles the zmq sockets for communicating with the ProjectManager.
    The project manager receives submissions and job completion notifications
    through the input zmq sockets and returns a list of responses which involve
    sending information out of the various output zmq sockets"""
    def __init__(self, root, ppid):
        self.root = root
        self.ppid = ppid

    def responseHandler(self, responseList):
        """Send responses in responseList to the appropriate output socket, according
        to the response type"""
        sockDict = dict(REPLY=self.submit, SEND_JOB=self.source,
                        STOP_WORKERS=self.controller)
        for r in responseList:
            sockDict[r.type].send(json.dumps(r.data))

    def dispatch(self, workerIndex, job, jobNum):
        paramDict = dict(msg="JOB", jobNum=jobNum, job="REPORT",
            args=(self.root, job.name, job.paramDict, job.instructions, job.ticket, job.inputs, job.outputs))
        self.source.send(("%d\n" % workerIndex) + json.dumps(paramDict))

    def run(self):
        self.context = zmq.Context()
        self.submit = self.context.socket(zmq.REP)
        self.submit.bind("tcp://127.0.0.1:%d" % PROJECT_SUBMISSION_PORT)
        self.source = self.context.socket(zmq.PUB)
        self.source.bind("tcp://127.0.0.1:%d" % JOB_DISTRIBUTION_PORT)
        self.sink = self.context.socket(zmq.PULL)
        self.sink.bind("tcp://127.0.0.1:%d" % JOB_COMPLETE_PORT)
        self.controller = self.context.socket(zmq.PUB)
        self.controller.bind("tcp://127.0.0.1:%d" % STOP_WORKERS_PORT)
        self.pm = ProjectManager(self.root, self)
        self.terminate = False
        poller = zmq.Poller()
        poller.register(self.submit, zmq.POLLIN)
        poller.register(self.sink, zmq.POLLIN)
        while not self.terminate:
            socks = dict(poller.poll(timeout=1000))
            if socks.get(self.submit) == zmq.POLLIN:
                cmd = json.loads(self.submit.recv())
                responseList = self.pm.handleSubmission(cmd)
                self.responseHandler(responseList)
            elif socks.get(self.sink) == zmq.POLLIN:
                result = json.loads(self.sink.recv())
                self.pm.handleJobCompletion(result)
            if not psutil.pid_exists(self.ppid):
                self.terminate = True
                break
            self.pm.allocateWork()
        self.pm.close()
        self.controller.close()
        self.sink.close()
        self.source.close()
        self.submit.close()
        self.context.term()


class ProjectManager(object):
    """The ProjectManager keeps track of the active projects (which are ones which
        have outstanding jobs) and decides which job to send out to the pool of workers.
        When a worker is available, the manager looks at the head of the deque
        of active projects and looks for next job which can be done for that project
        because all its input resources are available. It moves the project to the tail
        of the deque and continues with a job from the next project until all workers
        are busy or until no job from any project is ready to run.
        """
    def __init__(self, root, interface):
        self.root = root
        self.interface = interface
        # Sockets to talk to resource manager
        self.rmSocket = self.interface.context.socket(zmq.REQ)
        self.rm = ResourceManagerProxy(self.rmSocket)
        if not os.path.isdir(root):
            os.makedirs(root)
        self.projectSubmissions = {}
        self.jobsByProject = {}
        self.responseList = []
        self.activeProjects = deque()
        self.workers = set()
        self.workersAvailable = set()
        self.jobNum = 0
        self.jobsByWorker = {}
        self.poolSize = 0
        self.workerIndex = 0
        self.poolProcesses = {}
        self.workerStartPending = False
        self.jobs = Counter()
        self.jobsCrashed = Counter()
        self.jobsDispatched = Counter()
        self.jobsFailed = Counter()
        self.jobsSuccessful = Counter()
        self.jobsToRetry = []

    def close(self):
        self.rmSocket.close()

    def addWorker(self, workerIndex):
        if workerIndex not in self.workers:
            self.workers.add(workerIndex)
            self.workersAvailable.add(workerIndex)
        else:
            raise ValueError('Worker %d is already in pool' % workerIndex)

    def removeWorker(self, workerIndex):
        if workerIndex in self.workersAvailable:
            self.workersAvailable.remove(workerIndex)
        try:
            self.workers.remove(workerIndex)
        except KeyError:
            raise ValueError('Worker %d is not in pool' % workerIndex)

    def allocateWork(self):
        # Check that the expected worker processes are alive. If not, we mark the job as having
        #  failed and count this as a crash
        deadWorkers = []
        for workerIndex in self.workers:
            if workerIndex in self.poolProcesses:
                if not self.poolProcesses[workerIndex].is_alive():
                    if workerIndex in self.jobsByWorker:
                        job = self.jobsByWorker[workerIndex]
                        del self.jobsByWorker[workerIndex]
                        # Set all outputs to be completed unsuccessfully
                        self.jobsCrashed[job.name] += 1
                        job.jobFailed(workerIndex)
                        job.updateAndGetStatus()
                    self.poolProcesses[workerIndex].join()
                    del self.poolProcesses[workerIndex]
                    deadWorkers.append(workerIndex)
        for workerIndex in deadWorkers:
            self.workers.remove(workerIndex)
            if workerIndex in self.workersAvailable:
                self.workersAvailable.remove(workerIndex)

        # Start up a new Worker in a process if we do not have enough in the pool
        if (not self.workerStartPending) and (len(self.workers) < self.poolSize):
            self.workerStartPending = True
            p = mp.Process(target=Worker(self.workerIndex, JOB_DISTRIBUTION_PORT, JOB_COMPLETE_PORT, STOP_WORKERS_PORT, os.getpid()).run)
            p.start()
            self.poolProcesses[self.workerIndex] = p
            self.workerIndex += 1
        if self.workersAvailable:
            job = self.findNextJob()
            if job is not None:
                self.jobNum += 1
                # Set all outputs to be "IN PROGRESS"
                job.jobStarted()
                self.jobsDispatched[job.name] += 1
                workerIndex = self.workersAvailable.pop()
                self.jobsByWorker[workerIndex] = job
                self.interface.dispatch(workerIndex, job, self.jobNum)

    def handleJobCompletion(self, result):
        if result["msg"] == "SUCCESS":
            workerIndex = result["workerIndex"]
            job = self.jobsByWorker[workerIndex]
            del self.jobsByWorker[workerIndex]
            # Write the job result to all outputs
            job.logResult(result)
            # Set all outputs to be completed successfully
            self.jobsSuccessful[job.name] += 1
            job.jobSucceeded(workerIndex)
            job.updateAndGetStatus()
            if result["available"]:
                self.workersAvailable.add(workerIndex)
        elif result["msg"] == "FAILURE":
            workerIndex = result["workerIndex"]
            job = self.jobsByWorker[workerIndex]
            del self.jobsByWorker[workerIndex]
            # Write the job result to all outputs
            job.logResult(result)
            # Set all outputs to be completed unsuccessfully
            self.jobsFailed[job.name] += 1
            job.jobFailed(workerIndex)
            job.updateAndGetStatus()
            if result["available"]:
                self.workersAvailable.add(workerIndex)
        elif result["msg"] == "STARTING":
            self.addWorker(result["workerIndex"])
            self.workerStartPending = False
        elif result["msg"] == "TERMINATING":
            workerIndex = result["workerIndex"]
            if workerIndex in self.jobsByWorker:
                # The worker was terminated before completing a job, we need to
                #  resubmit the job to another worker
                self.jobsToRetry.append(self.jobsByWorker[workerIndex])
                del self.jobsByWorker[workerIndex]
            if workerIndex in self.workers:
                self.removeWorker(workerIndex)
            if workerIndex in self.poolProcesses:
                self.poolProcesses[workerIndex].join()
                del self.poolProcesses[workerIndex]

    def handleSubmission(self, cmd):
        self.responseList = []
        try:
            if cmd["msg"] == "PROJECT":
                contents = cmd["contents"]
                ps = ProjectSubmission(cmd["reportRoot"], contents, self.rm)
                reply = {"contents": contents, "ticket": ps.ticket}
                # Get the list of jobs that need to be done for this project
                ps = self.registerProject(ps)

                ps.analyzeSubmission()
                if ps.projectComplete() == ProjectSubmission.PROJECT_COMPLETE:
                    self.setJobs(ps.ticket, [])
                else:
                    if ps.ticket not in self.jobsByProject:
                        self.setJobs(ps.ticket, ps.jobList)
                        for j in ps.jobList:
                            self.jobs[j.name] += 1
                    if ps.ticket not in self.activeProjects:
                        self.activeProjects.appendleft(ps.ticket)
                response = ResponseTuple("REPLY", reply)
            elif cmd["msg"] == "ADD_WORKER":
                self.addWorker(cmd["workerIndex"])
                response = ResponseTuple(
                    "REPLY", {"nWorkers": len(self.workers)})
            elif cmd["msg"] == "DELETE_PROJECT":
                ticket = cmd["ticket"]
                status = self.deleteProject(ticket)
                response = ResponseTuple(
                    "REPLY", {"ticket": ticket, "status": status})
            elif cmd["msg"] == "GET_PROJECT_STATUS":
                ticket = cmd["ticket"]
                if ticket not in self.projectSubmissions:
                    response = ResponseTuple(
                        "REPLY", {"error": "Project not found"})
                else:
                    ps = self.projectSubmissions[ticket]
                    jobs = self.jobsByProject[ticket]
                    response = ResponseTuple("REPLY", {"project": ps.getStatus(
                        ), "jobs": [j.asDict() for j in jobs]})
            elif cmd["msg"] == "GET_ROOT":
                response = ResponseTuple("REPLY", {"root": self.root})
            elif cmd["msg"] == "GET_STATISTICS":
                response = ResponseTuple("REPLY", {"jobs": dict(self.jobs),
                                                  "jobsCrashed": dict(self.jobsCrashed),
                                                  "jobsDispatched": dict(self.jobsDispatched),
                                                  "jobsFailed": dict(self.jobsFailed),
                                                  "jobsSuccessful": dict(self.jobsSuccessful)})
            elif cmd["msg"] == "GET_WORKER_STATS":
                response = ResponseTuple("REPLY", {"workers": list(self.workers), "nWorkersFree": len(self.workersAvailable)})
            elif cmd["msg"] == "REMOVE_WORKER":
                self.removeWorker(cmd["workerIndex"])
                response = ResponseTuple(
                    "REPLY", {"nWorkers": len(self.workers)})
            elif cmd["msg"] == "SET_POOL_SIZE":
                self.poolSize = cmd["poolSize"]
                response = ResponseTuple("REPLY", {"poolSize": self.poolSize})
            elif cmd["msg"] == "STOP_WORKERS":
                if "workers" in cmd:
                    self.interface.controller.send(
                        "KILL\n" + json.dumps({"workers": cmd["workers"]}))
                else:
                    self.interface.controller.send("KILL")
                response = ResponseTuple("REPLY", {})
        except:
            response = ResponseTuple("REPLY", {'error': "Project Manager Exception\n%s" % traceback.format_exc()})

        response.data["msg"] = cmd["msg"]
        self.responseList.append(response)
        return self.responseList

    def registerProject(self, projectSubmission):
        """Check to see if the project is already on disk. If so, verify that there is
        no hash collision by comparing the contents with the instructions file.
        Otherwise save the contents as the file named "json" in the project directory.

        Returns projectSubmission if the submission has NOT previously been registered,
        Otherwise returns the previously registered submission having the same ticket.
        """
        ps = projectSubmission
        rt = makeResourceTuple(ps.ticket, "INSTRUCTIONS")
        instrFilename = os.path.join(ps.reportDir, ps.ticket, "json")
        status, detailedStatus = self.rm.getStatus(rt)
        if status != Resource.NOT_STARTED:
            # An instructions file for this hash already exists
            with file(instrFilename, "rb") as fp:
                oldContents = fp.read()
            if ps.contents != oldContents:
                raise ValueError("Secure hash collision - should never happen")
        else:
            # No instructions file, so make one in the directory
            self.rm.makeStarted(rt)
            with file(instrFilename, "wb") as fp:
                fp.write(ps.contents)
            self.rm.makeSucceeded(rt)

        if ps.ticket not in self.projectSubmissions:
            self.projectSubmissions[ps.ticket] = ps
        return self.projectSubmissions[ps.ticket]

    def deleteProject(self, ticket):
        """Deletes project files from disk and project from cached dictionaries"""
        # TODO: Stop any running jobs for this project before deletion
        # This may involve terminating processes and restarting them
        if ticket in self.jobsByProject:
            del self.jobsByProject[ticket]
        if ticket in self.activeProjects:
            self.activeProjects.remove(ticket)
        if ticket in self.projectSubmissions:
            del self.projectSubmissions[ticket]
        return self.rm.deleteProjectDir(ticket)

    def findNextJob(self):
        """Returns the next job that can be run, or None if no job is ready.
        Note that once the project as a whole has failed because generation of any
        output resource has failed, that project is no longer egilible for having
        any of its jobs run.
        """
        if self.jobsToRetry:
            return self.jobsToRetry.pop(0)
        projectsToRemove = []
        for ticket in self.activeProjects:
            ps = self.projectSubmissions[ticket]
            # Update all job status before checking for ready-to-run so that we can
            # propagate failure quickly if we need to
            for j in self.jobsByProject[ticket]:
                j.updateAndGetStatus()
            if ps.projectComplete():    # Complete means either successful or failed
                projectsToRemove.append(ticket)
            else:
                for j in self.jobsByProject[ticket]:
                    if j.status in [Job.JOB_READY_TO_RUN]:
                        # Found an eligible job, move this project to end
                        # of the dequeue for next time
                        # N.B. This changes self.activeProjects, but this is
                        #  OK since we are breaking out of the iteration
                        while len(self.activeProjects) > 0:
                            t = self.activeProjects.popleft()
                            if t in projectsToRemove:
                                continue
                            self.activeProjects.append(t)
                            if t == ticket:
                                break
                        return j
        # Get here if no job is ready to run
        for ticket in projectsToRemove:
            self.activeProjects.remove(ticket)
        return None

    def setJobs(self, ticket, jobs):
        self.jobsByProject[ticket] = jobs


class ProjectSubmission(object):
    """On receiving a project:
        Validate instructions file
        Assign a ticket
        Create a directory for the project if it does not yet exist
            If directory already exists, check instructions file for secure hash collision
        Copy instructions file to project directory in json format
        Return ticket to sender
    """
    PROJECT_INCOMPLETE = 0
    PROJECT_COMPLETE = 1
    PROJECT_FAILED = -1
    statusText = {PROJECT_INCOMPLETE: "PROJECT_INCOMPLETE",
                  PROJECT_COMPLETE: "PROJECT_COMPLETE",
                  PROJECT_FAILED: "PROJECT_FAILED"}

    def __init__(self, reportDir, contents, resourceManager):
        self.reportDir = reportDir
        self.contents = contents
        self.instructions = None
        self.ticket = getTicket(self.contents)
        self.deliverableResources = None
        self.jobList = None
        self.rm = resourceManager

    def getStatus(self):
        return self.statusText[self.projectComplete()]

    def projectComplete(self):
        """Check to see if the project deliverables have all been made.
        Returns:
            1 if all deliverables are in MAKE_SUCCEEDED states
            -1 if some deliverable is in MAKE_FAILED state
            0 otherwise (indicating project is in progress)
        """
        if self.deliverableResources is None:
            self.analyzeSubmission()

        for rt in self.deliverableResources:
            status, detailedStatus = self.rm.getStatus(rt)
            if status == Resource.MAKE_FAILED:
                return self.PROJECT_FAILED
            elif status != Resource.MAKE_SUCCEEDED:
                return self.PROJECT_INCOMPLETE
        return self.PROJECT_COMPLETE

    def analyzeSubmission(self):
        """Divide the project up into a collection of jobs which require input resources and produce output resources.
            Also determine the list of resources which, when made successfully, will indicate that the project is complete.

            Each resource is registered with the ResourceManager so that their make status can be discovered.
        """
        def RT(type, regionIndex=None):
            """Convenience function to generate resource tickets for this project"""
            return makeResourceTuple(self.ticket, type, regionIndex)

        if self.jobList is None:
            self.deliverableResources = []
            self.jobList = []
            self.instructions = json.loads(self.contents)
            regionalReports = []
            regionalMarkerDep = []
            regionalPathDep = []
            if "summary" in self.instructions:
                summaryMap = RT("SUMMARY_MAP")
                baseMap = RT("BASE_MAP", 0)
                pathMap = RT("PATH_MAP", 0)
                markerMap = RT("MARKER_MAP", 0)
                compositeMap = RT("COMPOSITE_MAP", 0)
                self.jobList.append(Job(self.rm, "Make Summary Key", {"task": "key"}, [], [summaryMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Summary Base", {"task": "base", "region": 0}, [], [baseMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Summary Marker", {"task": "marker", "region": 0}, [], [markerMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Summary Path", {"task": "path", "region": 0}, [], [pathMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Summary Composite", {"task": "composite", "region": 0}, [baseMap, pathMap, markerMap], [compositeMap], self.instructions))
                self.deliverableResources.append(summaryMap)
                regionalMarkerDep.append(markerMap)
                regionalPathDep.append(pathMap)
            for i, region in enumerate(self.instructions["regions"]):
                baseMap = RT("BASE_MAP", i + 1)
                pathMap = RT("PATH_MAP", i + 1)
                markerMap = RT("MARKER_MAP", i + 1)
                compositeMap = RT("COMPOSITE_MAP", i + 1)
                regionalReport = RT("REGIONAL_REPORT", i + 1)
                self.jobList.append(Job(self.rm, "Make Base, region %d" % (i + 1,), {"task": "base", "region": i + 1}, [], [baseMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Marker, region %d" % (i + 1,), {"task": "marker", "region": i + 1}, regionalMarkerDep, [markerMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Path, region %d" % (i + 1,), {"task": "path", "region": i + 1}, regionalPathDep, [pathMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Composite, region %d" % (i + 1,), {"task": "composite", "region": i + 1}, [baseMap, pathMap, markerMap], [compositeMap], self.instructions))
                self.jobList.append(Job(self.rm, "Make Regional Report, region %d" % (i + 1,), {"task": "regionalReport", "region": i + 1}, [pathMap, markerMap, compositeMap], [regionalReport], self.instructions))
                regionalReports.append(regionalReport)
                self.deliverableResources.append(compositeMap)
                self.deliverableResources.append(regionalReport)
            projectReport = RT("PROJECT_REPORT")
            self.jobList.append(Job(self.rm, "Make Project Report", {"task": "projectReport"}, regionalReports, [projectReport], self.instructions))
            self.deliverableResources.append(projectReport)


class Resource(object):
    """A Resource object is a wrapper for the files which indicate the status of a resource. These filename consists of a
    path followed by an extension indicating whether making of the resource is in progress, has succeeded or has failed.
    If none of the status files exist, making of the resource has not started.

    Resource status files consist of concatenated pickled dictionaries which give
    detailed status information about the build process for the resource.
    """
    extList = ["", ".wip", ".ok", ".err"]
    NOT_STARTED = 0
    IN_PROGRESS = 1
    MAKE_SUCCEEDED = 2
    MAKE_FAILED = 3
    statusDict = {NOT_STARTED: "NOT_STARTED", IN_PROGRESS: "IN_PROGRESS",
                   MAKE_SUCCEEDED: "MAKE_SUCCEEDED", MAKE_FAILED: "MAKE_FAILED"}

    def __init__(self, root, name):
        self.root = root
        self.name = name
        self.path = os.path.join(self.root, self.name)
        self.baseDir, _ = os.path.split(self.path)
        if not os.path.exists(self.baseDir):
            os.makedirs(self.baseDir)
        self._getStatus()

    def __repr__(self):
        return "Resource: %s, status: %s" % (self.name, self.statusDict[self.status])

    __str__ = __repr__

    def _getStatus(self):
        succ_path = self.path + self.extList[self.MAKE_SUCCEEDED]
        fail_path = self.path + self.extList[self.MAKE_FAILED]
        wip_path = self.path + self.extList[self.IN_PROGRESS]
        if os.path.exists(succ_path):
            self.status = self.MAKE_SUCCEEDED
            self._readDetailedStatus(succ_path)
        elif os.path.exists(fail_path):
            self.status = self.MAKE_FAILED
            self._readDetailedStatus(fail_path)
        elif os.path.exists(wip_path):
            self.status = self.IN_PROGRESS
            self._readDetailedStatus(wip_path)
        else:
            self.status = self.NOT_STARTED
            self.detailedStatus = {}

    def _readDetailedStatus(self, filename):
        """Read detailed status from the appropriate file"""
        self.detailedStatus = {}
        with file(filename, "rb") as fp:
            while True:
                try:
                    self.detailedStatus = merge_dictionary(
                        self.detailedStatus, cPickle.load(fp))
                except EOFError:
                    break

    def updateStatus(self, newStatus, newDetailedStatus):
        self.status = newStatus
        self.detailedStatus = merge_dictionary(
            self.detailedStatus, newDetailedStatus)


class ResourceManagerProxy(object):
    def __init__(self, zmqSocket):
        self.socket = zmqSocket
        zmqSocket.connect("tcp://127.0.0.1:%d" % RESOURCE_MANAGER_PORT)

    def __getattr__(self, attr):
        def dispatcher(*args, **kwargs):
            data = {"func": attr, "args": args, "kwargs": kwargs}
            self.socket.send(cPickle.dumps(data))
            reply = cPickle.loads(self.socket.recv())
            if "error" in reply:
                errmsg = ["Error in RPC %s" % attr]
                errmsg.append("Remote error %s" % reply["error"])
                if "traceback" in reply:
                    errmsg.append("Remote traceback: %s" % reply["traceback"])
                raise RuntimeError("\n".join(errmsg))
            else:
                return reply["result"]
        return dispatcher


class ResourceManager(object):
    """ResourceManager maintains the collection of most recently used Resources in an
    OrderedDict. The OrderedDict is keyed by resourceTuple. Normally, an OrderedDict
    maintains the order in which keys were first inserted into it, but if we pop the key
    and re-insert it when the key is referenced, the ordered dictionary will maintain the
    order in which entries were last used, with  the oldest at the beginning. The popitem
    method (with last=False) can be used to remove the LRU item.

    The resource manager also takes care of updating the cache and disk with resource
    status information. Writes to disk and defered to a background thread."""

    funcList = ["addDetail", "deleteProjectDir", "getStatistics", "getStatus",
                "makeFailed", "makeStarted", "makeSucceeded", "shutDown"]

    def __init__(self, root, ppid, maxResources=512):
        self.root = root
        self.ppid = ppid
        self.maxResources = maxResources

    def tidyCache(self):
        if len(self.resources) > self.maxResources:
            self.resources.popitem(False)
            self.cacheDeletes += 1

    def deleteProjectDir(self, ticket):
        """Deletes all resources corresponding to a particular project (as defined
            by the ticket) from the cache and remove the project directory from disk
        """
        rtToDel = [rt for rt in self.resources if rt.ticket == ticket]
        for rt in rtToDel:
            self.resources.pop(rt)
            self.cacheDeletes += 1
        rp = os.path.join(self.root, "%s" % ticket)
        exists = os.path.isdir(rp)
        if exists:
            shutil.rmtree(rp)
        return {"found": exists}

    def _getResource(self, rt):
        """Get the Resource object associated with the resource tuple rt and move it to
        the end of the cache. If the object is not in the cache, it will be constructed
        from the information on disk"""
        try:
            resource = self.resources.pop(rt)
            self.cacheHits += 1
        except KeyError:
            resource = Resource(self.root, resourceBaseName(rt))
            self.cacheMisses += 1
        # (Re-)insert the resource at the end of the cache
        self.resources[rt] = resource
        return resource

    def getStatistics(self):
        return dict(cacheHits=self.cacheHits,
                    cacheMisses=self.cacheMisses,
                    cacheDeletes=self.cacheDeletes,
                    writes=self.writes,
                    resourcesStarted=self.resourcesStarted,
                    resourcesMadeSuccessfully=self.resourcesMadeSuccessfully,
                    resourcesMadeUnsuccessfully=self.resourcesMadeUnsuccessfully)

    def shutDown(self):
        self.terminate = True

    def getStatus(self, rt):
        resource = self._getResource(rt)
        return resource.status, resource.detailedStatus

    def makeStarted(self, rt):
        # Make sure no status files exist
        resource = self._getResource(rt)
        assert resource.status == resource.NOT_STARTED
        for e in resource.extList:
            if e:
                assert not os.path.exists(resource.path + e)
        newStatus = resource.IN_PROGRESS
        newDetailedStatus = {"start": time.strftime("%Y%m%dT%H%M%S")}
        resource.updateStatus(newStatus, newDetailedStatus)
        self.writeQueue.put({"cmd": "CREATE",
                             "name": resource.path + resource.extList[newStatus],
                             "data": newDetailedStatus})
        self.writes += 1
        self.resourcesStarted[rt.type] += 1
        return self.getStatus(rt)

    def makeSucceeded(self, rt, doneMsg="done"):
        resource = self._getResource(rt)
        assert resource.status == resource.IN_PROGRESS
        newStatus = resource.MAKE_SUCCEEDED
        newDetailedStatus = {"end": time.strftime("%Y%m%dT%H%M%S"),
                                                  "done": doneMsg}
        resource.updateStatus(newStatus, newDetailedStatus)
        self.writeQueue.put({"cmd": "RENAME",
                             "oldName": resource.path + resource.extList[resource.IN_PROGRESS],
                             "newName": resource.path + resource.extList[newStatus],
                             "data": newDetailedStatus})
        self.writes += 1
        self.resourcesMadeSuccessfully[rt.type] += 1
        return self.getStatus(rt)

    def makeFailed(self, rt, errorMsg="error"):
        resource = self._getResource(rt)
        assert resource.status == resource.IN_PROGRESS
        newStatus = resource.MAKE_FAILED
        newDetailedStatus = {"end": time.strftime("%Y%m%dT%H%M%S"),
                                                  "error": errorMsg}
        resource.updateStatus(newStatus, newDetailedStatus)
        self.writeQueue.put({"cmd": "RENAME",
                             "oldName": resource.path + resource.extList[resource.IN_PROGRESS],
                             "newName": resource.path + resource.extList[newStatus],
                             "data": newDetailedStatus})
        self.writes += 1
        self.resourcesMadeUnsuccessfully[rt.type] += 1
        return self.getStatus(rt)

    def addDetail(self, rt, detailedStatus):
        resource = self._getResource(rt)
        assert resource.status == resource.IN_PROGRESS
        resource.updateStatus(resource.status, detailedStatus)
        self.writeQueue.put({"cmd": "APPEND",
                             "name": resource.path + resource.extList[resource.IN_PROGRESS],
                             "data": detailedStatus})
        self.writes += 1
        return self.getStatus(rt)

    def handleRequest(self, request):
        """Call an RPC function and wrap results and exceptions as necessary"""
        data = cPickle.loads(request)
        funcName = data["func"]
        args = data["args"]
        kwargs = data["kwargs"]
        if funcName in self.funcList:
            try:
                result = getattr(self, funcName)(*args, **kwargs)
                reply = {"result": result}
            except Exception, e:
                reply = {"error": "%s" % e, "traceback":
                    traceback.format_exc()}
        else:
            reply = {"error": "Unknown function: %s" % funcName}
        return reply

    def run(self):
        self.resources = OrderedDict()
        self.cacheHits = 0
        self.cacheMisses = 0
        self.cacheDeletes = 0
        self.writes = 0
        self.resourcesStarted = Counter()
        self.resourcesMadeSuccessfully = Counter()
        self.resourcesMadeUnsuccessfully = Counter()
        self.writeQueue = Queue(0)
        # Start disk writer thread in here
        self.writeThread = threading.Thread(target=self.writeHandler)
        self.writeThread.setDaemon(True)
        self.writeThread.start()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://127.0.0.1:%d" % RESOURCE_MANAGER_PORT)
        try:
            self.terminate = False
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)
            while not self.terminate:
                socks = dict(poller.poll(timeout=1000))
                if socks.get(self.socket) == zmq.POLLIN:
                    result = self.handleRequest(self.socket.recv())
                    self.socket.send(cPickle.dumps(result))
                if not psutil.pid_exists(self.ppid):
                    self.terminate = True
                    break
                self.tidyCache()    # Enforce the LRU discipline
        finally:
            self.socket.close()
            self.context.term()
            self.writeQueue.join()

    def writeHandler(self):
        while True:
            item = self.writeQueue.get()
            try:
                cmd = item["cmd"]
                if cmd == "CREATE":
                    with file(item["name"], "wb") as fp:
                        cPickle.dump(item["data"], fp)
                elif cmd == "APPEND":
                    with file(item["name"], "ab") as fp:
                        cPickle.dump(item["data"], fp)
                elif cmd == "RENAME":
                    with file(item["oldName"], "ab") as fp:
                        cPickle.dump(item["data"], fp)
                    if os.path.exists(item["newName"]):
                        os.remove(item["newName"])
                    os.rename(item["oldName"], item["newName"])
            finally:
                self.writeQueue.task_done()


class Worker(object):
    """Represents a worker which can be started, given jobs and stopped
        Constructing an object of this class automatically starts it running, so the constructor can be
         used as the target of a Thread or Process.
        A worker has a PULL socket (rPort) for receiving jobs and a PUSH socket (sPort) for sending back results.
         It also has a SUBSCRIBE (cPort) port for receiving broadcast commands.
        When a worker starts it sends a message "STARTING" together with its index via sPort
        To stop the worker, broadcast the KILL command to cPort. Following the KILL is a JSON encoded
         dictionary with a list specifying the workers to kill. If no list is present, all workers are killed.
        When a worker terminates it sends a message "TERMINATING" together with its index via sPort
        The attribute maxJobs can be used to limit the number of jobs a worker can perform before it is
         automatically terminated. This is useful for freeing resources that might otherwise be held by the
         worker.
    """
    def __init__(self, index, rPort, sPort, cPort, ppid):
        self.index = index
        self.rPort = rPort
        self.sPort = sPort
        self.cPort = cPort
        self.ppid = ppid
        self.jobsDone = 0
        self.maxJobs = 10

    def report(self, root, name, paramDict, instructions, ticket, inputs, outputs):
        inputs = [ResourceTuple(*x) for x in inputs]
        outputs = [ResourceTuple(*x) for x in outputs]
        if "test" in instructions:
            time.sleep(1.0)
            return
        else:
            rg = ReportGenerator(root, self.rm, name, paramDict,
                                 instructions, ticket, inputs, outputs)
            return rg.process()

    def square(self, x):
        return x * x

    def sleep(self, x):
        time.sleep(x)

    def doJob(self, cmd):
        jobMap = {"REPORT": self.report, "SQUARE": self.square,
            "SLEEP": self.sleep}
        reply = {"workerIndex": self.index}
        if cmd["msg"] == "JOB":
            job = cmd.get("job", "")
            jobNum = cmd.get("jobNum")
            args = cmd.get("args", ())
            kwargs = cmd.get("kwargs", {})
            try:
                func = jobMap[job]
                try:
                    result = func(*args, **kwargs)
                    reply["msg"] = "SUCCESS"
                    reply["result"] = result
                except:
                    reply["msg"] = "FAILURE"
                    reply["error"] = "Exception in job"
                    reply["traceback"] = traceback.format_exc()
            except KeyError:
                reply["msg"] = "FAILURE"
                reply["error"] = "No such job type"
            reply["jobNum"] = jobNum
        else:
            reply["msg"] = "FAILURE"
            reply["error"] = "Invalid command"
        print "Job reply:", reply
        return reply

    def run(self):
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.SUB)
        self.receiver.connect("tcp://127.0.0.1:%d" % self.rPort)
        self.receiver.setsockopt(zmq.SUBSCRIBE, "%d\n" % self.index)
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.connect("tcp://127.0.0.1:%d" % self.sPort)
        # We must subscribe to all messages coming down the controller socket
        self.controller = self.context.socket(zmq.SUB)
        self.controller.connect("tcp://127.0.0.1:%d" % self.cPort)
        self.controller.setsockopt(zmq.SUBSCRIBE, "KILL")
        self.rmSocket = self.context.socket(zmq.REQ)
        self.rm = ResourceManagerProxy(self.rmSocket)
        time.sleep(0.1)
        # Set up a poller to handle messages
        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)
        poller.register(self.controller, zmq.POLLIN)
        self.sender.send(
            json.dumps(dict(msg="STARTING", workerIndex=self.index)))

        try:
            while True:
                socks = dict(poller.poll(timeout=1000))
                # A message to the controller stops the worker. We need to test for this
                # BEFORE checking if there is more work availale, so that it is possible
                # to stop cleanly
                if socks.get(self.controller) == zmq.POLLIN:
                    cmd = self.controller.recv()
                    killWorker = True
                    pos = cmd.find("\n")
                    if pos >= 0:
                        args = json.loads(cmd[pos + 1:])
                        if "workers" in args:
                            killWorker = self.index in args["workers"]
                    if killWorker:
                        break
                if socks.get(self.receiver) == zmq.POLLIN:
                    cmd = self.receiver.recv()
                    pos = cmd.find("\n")
                    if pos >= 0:
                        args = json.loads(cmd[pos + 1:])
                    result = self.doJob(args)
                    self.jobsDone += 1
                    result["available"] = self.jobsDone < self.maxJobs
                    self.sender.send(json.dumps(result))
                    if not result["available"]:
                        break
                # Check if parent is alive, and if not, terminate this process
                if not psutil.pid_exists(self.ppid):
                    break
        finally:
            self.sender.send(
                json.dumps(dict(msg="TERMINATING", workerIndex=self.index)))

        time.sleep(0.1)  # Allow termination ack to be sent
        self.rmSocket.close()
        self.sender.close()
        self.receiver.close()
        self.controller.close()
        self.context.term()

if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    pm = ProjectManagerInterface(root)
    pm.run()


"""
Maintain a dictionary keyed by resource tuples. The key values indicate the status of the resource.

0 -> does not exist            No file
1 -> generation in progress    baseName.stat
2 -> generated successfully    baseName.ok
3 -> generation failed         baseName.err

We rename baseName.stat into baseName.ok or baseName.err

We need functions to create and delete the sentinel files indicating that
    a) A resource is in process of being constructed
    b) A resource has been successfully made
    c) A resource could not be successfully made

We should be able to go through a directory and update the dictionary of resources

Breaking up a project into jobs:
    If needed:
        Produce a summary map
            (inputs: None, outputs: *.summaryMap.png)
    For each region, we have the following jobs:
        Produce base map(s) depending on the map type selected
            (inputs: None, outputs: *.streetMap.png, *.satMap.png)
        Produce path map and swath map for collection of all runs
            (inputs: None, outputs: *.pathMap.png, *.pathMap.html,
                                    *.swathMap.png)
        Produce marker map and wedges map for collection of all runs
            (
                inputs: None, outputs: *.peaksMap.png,  *.peaksMap.html, *.peaksMap.xml,
                                    *.markerMap.png, *.wedgesMap.png)
        Produce composite maps
            (
                inputs: *.streetMap.png, *.satMap.png,    *.pathMap.png,   *.swathMap.png,
                     *.peaksMap.png,  *.markerMap.png, *.wedgesMap.png
             outputs: *.compositeMap.png)
             There are several flavors of composite map.
             Either a single map with the selected layers or three maps:
                 1. Street map with swaths
                 2. Street map with peaks, wedges and markers
                 3. Satellite map with path, peaks, wedges and markers
        Produce final reports by region
            (inputs: *.compositeMap.png, *.pathMap.html, *.peaksMap.html, *.peaksMap.xml
             outputs: report.html, report.pdf, report.xml)
    After all regions are complete, we need to assemble the individual reports into project reports
            (inputs: *.summaryMap.png, *.pdf, *.xml)


    Define a set of resource types which serve as inputs and outputs for these jobs
    By project:
        SUMMARY_MAP
        PROJECT_REPORT
    By region:
        BASE_MAP (set of base maps required)
        PATH_MAP (path and swath maps, as required)
        MARKER_MAP (peaks, wedges and marker maps)
        COMPOSITE_MAP
        REGIONAL_REPORT

    For each resource type, we place a file in the directory to indicate that
        a) Generation of resource has started
        b) Generation of resource succeeded
        c) Generation of resource produced an error
    These are used to indicate progress and to allow recovery after power failures etc. Status requests
    look at these files.

    We need to be able to check if all the output resources for a project have already been made successfully.
        If so, we can give the option to just use these and not submit the jobs.


    class Project(object):
        def __init__(self):
            self.jobList = ...

    class Job(object):
        def __init__(self,inputs,outputs,sequence):
            self.inputs = inputs
            self.outputs = outputs
            self.sequence = sequence

    # class Resource(object):
    #     pass
    #
    # class BaseMap(Resource):
    #     def __init__(self,region):
    #         self.region = region
    #         self.inprogressFilename = "baseMap.%d.status" % region
    #         self.successFilename = "baseMap.%d.ok" % region
    #         self.errorFilename = "baseMap.%d.error" % region
    # This seems unnecessarily complicated. Try using tuples which are immutable and can be compared
    #  directly

    seq = 0
    Job([],[SUMMARY_MAP],seq); seq+=1
    for i in range(nRegions):
        Job([],[BASE_MAP(i)],seq); seq+=1
        Job([],[PATH_MAP(i)],seq); seq+=1
        Job([],[MARKER_MAP(i)],seq); seq+=1
        Job([BASE_MAP(
            i),PATH_MAP(i),MARKER_MAP(i)],[COMPOSITE_MAP(i)],seq); seq+=1
        Job([PATH_MAP(i),MARKER_MAP(i),COMPOSITE_MAP(i)],[
            REGIONAL_REPORT(i)],seq); seq+=1
    Job([REGIONAL_REPORT(
        i) for i in range(nRegions)],[PROJECT_REPORT],seq); seq+=1


    A worker is given a job and is responsible for updating the status of its output resources.
        Before it starts, it should check that its input resources are all successfully present.


    We need a job table which lists all the jobs for each project and whether each:
        a) Is waiting on resources
        b) Is in progress
        c) Is complete

    We need a list of resources defined for each project and their status
        a) Absent
        b) Successfully created
        c) Not created because of an error

    I want a resource to be a tuple so that it is immutable and can be compared directly
        e.g., (ticket,type,region) Note that a ticket defines a project


    We have a dispatcher which has the following input 0MQ sockets:
        a) New projects. This is a REP socket which replies with the ticket number.
        b) Resource available. This is a PULL socket which gets messages from the workers indicating
            when resources are available and their states
        c) A REP socket which handles requests for status about projects
    It has the following output 0MQ socket:
        a) Job to be done. This is a PUSH socket which tells a worker that it has some work to do

    We poll the inputs:
        If we receive a new project:
            Calculate the secure hash (ticket)

            we check to see if the project is on the file system
                Verify secure hash has not been accidentally duplicated, if so return an error condition.

            we check to see if the project is in the list of active projects, if so just return the
            hash code and the contents

            If this is not an active project
                Create the subdirectory for the project, and write the instructions file
                Add it to the front of the deque of active projects
                Reply with the hash code and contents
                Break the project up into jobs, updating the job table and the resource table. This may
                 involve multiple reads of the disk.
                Mark jobs which have all inputs available as being ready-to-run

        Maintain count of number of ready-to-run jobs

        If we receive notification of a resource, update the resource table
            If resource successfully made:
                Go through the jobs for this project and mark as being ready-to-run those which have their
                inputs satisified
            If resource creation gave an error:
                Mark jobs which depend on the resource as being blocked because of the error
            Increment the number of available workers

        While there are workers who are available for work and there are ready-to-run jobs:
            Pop off the active project at the front of the deque and find the first ready-to-run job for
                that project. Submit the job. Push the active project to the back of the queue.
"""
