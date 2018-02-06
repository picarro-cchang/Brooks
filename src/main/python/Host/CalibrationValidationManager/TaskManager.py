# TaskManager


# from PyQt4.QtCore import QObject, pyqtSignal
import functools
import time
from PyQt4 import QtCore
from Host.Common.configobj import ConfigObj
from ReferenceGas import ReferenceGas
from Task import Task

class TaskManager(QtCore.QObject):
    # start_signal = QtCore.pyqtSignal()
    stop_signal = QtCore.pyqtSignal()       # Tell current task to stop, aborts the queue
    ping_task_signal = QtCore.pyqtSignal()

    def __init__(self, iniFile):
        super(TaskManager, self).__init__()
        self.referenceGases = []
        self.tasks = []
        self.threads = []
        self.running_task_idx = None    # Running task idx, None if no jobs running
        self.loadConfig()
        self.set_connections()
        return

    def loadConfig(self, iniFile = "task_manager.ini"):
        co = ConfigObj(iniFile)

        for key, gasConfObj in co["GASES"].items():
            self.referenceGases.append(ReferenceGas(gasConfObj))

        for key, taskConfObj in co["TASKS"].items():
            # The [TASKS] section is a collection of individual tasks
            # and global key-value pairs that apply to all tasks.
            # Individual tasks are in sub-sections like [[TASK0]].
            # The sub-section settings are used to instantiate a Task
            # object.
            #
            # In the dict representation of the configobj, the key is
            # just a string and you can't tell if the key represents a
            # sub-section or something else.  So what we do is given
            # a key, if the value associated with it is a dict, we
            # treat this as a configobj sub-section.  Anything else we
            # treat as a TASKS global key-value pair.  Valid values
            # in this case are floats, ints, strings, booleans, and lists.
            #
            if isinstance(taskConfObj,dict):
                task_thread = QtCore.QThread()
                task = Task(my_parent=self, my_id=key)
                task.moveToThread(task_thread)
                task_thread.started.connect(task.work)
                self.tasks.append(task)
                self.threads.append(task_thread)
        return

    def set_connections(self):
        for task in self.tasks:
            task.task_finish_signal.connect(self.task_finished_ack_slot)
            task.task_heartbeat_signal.connect(self.task_heartbeat_slot)
        return

    def start_work(self):
        """
        Kick off the first task in the task list
        :return:
        """
        self.running_task_idx = 0
        self.threads[self.running_task_idx].start()
        self.running_task_idx += 1

    def move_to_next_task(self):
        """
        If there are more tasks to do, start the next one
        :return:
        """
        if self.running_task_idx < len(self.threads):
            self.threads[self.running_task_idx].start()
            self.running_task_idx += 1
        else:
            print("All jobs done")
            self.running_task_idx = None
        return

    def task_finished_ack_slot(self, task_id):
        print("Recieved finished ack from %s, starting next job" %task_id)
        self.move_to_next_task()
        return

    def task_heartbeat_slot(self, task_id):
        """
        Get heartbeat signal from a running thread to update a progress bar
        :return:
        """
        print("Got heartbeat signal from %s" %task_id)
        return

    def is_task_alive_slot(self):
        print("TM sending ping")
        self.ping_task_signal.emit()
        return