# TaskManager
#
# Need:
#   Instructions (what to do)
#   RefGas (if measuring a gas and comparing to a measurement in this object)
#   Data source (if measuring an unknown gas we need the data)
#   Timer (for time based evolution of the task or sub-tasks)
#   Signals (to indicate progress or completion)
#   Slots (to accept commands to start, pause, abort)
#
# Task is an object instantiated by the TaskManager and embedded in a QThread
# so the task doesn't block the main code due to the GIL.
#
# The task start execution with QThread.start() invoking work() below.
#
# Signals:
# task_finish_signal:       Alerts TaskManager that this task has finished. Use for normal exit.
# task_abort_signal:        Alerts TaskManager that the task quit early or failed.
# task_heartbead_signal:    A periodic signal that will tell TaskManager that the task is running.
#
# Slots:
# abort_slot:               Receives TaskManager command to abort this task.
# ping_slot:                Receives TaskManager command to send task_heartbeat_signal.

from PyQt4 import QtCore
import time

class Task(QtCore.QObject):
    task_finish_signal = QtCore.pyqtSignal(str)
    task_abort_signal = QtCore.pyqtSignal(str)
    task_heartbeat_signal = QtCore.pyqtSignal(str)

    def __init__(self, my_parent = None, settings = {}, refGas = None, my_id = None):
        super(Task, self).__init__()
        self.my_parent = my_parent
        self.referenceGas = refGas
        self.settings = settings
        self.my_id = my_id
        self._running = False
        self._mutex = QtCore.QMutex()
        self.set_connections()
        return

    # ----------------------------------------------------------------------------------
    # Task start/stop management methods
    #
    def set_connections(self):
        self.my_parent.ping_task_signal.connect(self.ping_slot)
        return

    def work(self):
        self._running = True
        aborted_work = False
        self.core_measurement()
        if aborted_work:
            self.task_abort_signal.emit(self.my_id)
        else:
            self.task_finish_signal.emit(self.my_id)
        self._running = False
        return

    def stop_slot(self):
        self._mutex.lock()
        self._running = False
        self._mutex.unlock()
        return

    def ping_slot(self):
        if self._running:
            self.task_heartbeat_signal.emit(self.my_id)
        return

    # ------------------------------------------------------------------------------------
    # Work to-do and helper methods
    #
    def core_measurement(self):
        for i in xrange(10):
            print("%s doing some mock work here: %s" %(self.my_id, i))
            time.sleep(1)
        return