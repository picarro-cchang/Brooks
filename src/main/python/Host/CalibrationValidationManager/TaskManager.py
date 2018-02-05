# TaskManager


# from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4 import QtCore
from Host.Common.configobj import ConfigObj
from ReferenceGas import ReferenceGas
from Task import Task

class TaskManager(QtCore.QObject):
    start_signal = QtCore.pyqtSignal()
    stop_signal = QtCore.pyqtSignal()

    def __init__(self, iniFile):
        print("initializing task manager", iniFile)
        super(TaskManager, self).__init__()
        self.referenceGases = []
        self.tasks = []
        self.loadConfig()
        self.set_connections()
        return

    def loadConfig(self, iniFile = "task_manager.ini"):
        print("Reading file:", iniFile)
        # co = CustomConfigObj(iniFile)
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
                self.tasks.append(Task(my_parent=self, my_id=key))

        return

    def set_connections(self):
        for task in self.tasks:
            task.task_started_signal.connect(self.task_started_ack_slot)
            task.task_finish_signal.connect(self.task_finished_ack_slot)
        return

    def emit_test_signal(self):
        print("Emitting start signal")
        self.start_signal.emit()
        return

    def task_started_ack_slot(self):
        print("Recieved start ack")
        return

    def task_finished_ack_slot(self):
        print("Recieved finished ack")
        return