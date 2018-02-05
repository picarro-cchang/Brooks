# TaskManager
#
# Need:
#   Instructions (what to do)
#   RefGas (if measuring a gas and comparing to a measurement in this object)
#   Data source (if measuring an unknown gas we need the data)
#   Timer (for time based evolution of the task or sub-tasks)
#   Signals (to indicate progress or completion)
#   Slots (to accept commands to start, pause, abort)


from PyQt4 import QtCore
import time

class Task(QtCore.QObject):
    task_started_signal = QtCore.pyqtSignal()
    task_finish_signal = QtCore.pyqtSignal()
    task_aborted_signal = QtCore.pyqtSignal()
    task_paused_signal = QtCore.pyqtSignal()
    task_heartbeat_signal = QtCore.pyqtSignal()

    def __init__(self, my_parent = None, settings = {}, refGas = None, my_id = None):
        super(Task, self).__init__()
        self.my_parent = my_parent
        self.referenceGas = refGas
        self.settings = settings
        self.my_id = my_id
        self.set_connections()
        return

    def set_connections(self):
        self.my_parent.start_signal.connect(self.start_slot)
        return

    # Qt Slots
    def start_slot(self):
        self.task_started_signal.emit()
        self.mock_work()
        self.task_finish_signal.emit()
        return

    def stop_slot(self):
        print("Task %s received stop command" %self.my_id)
        return

    def mock_work(self):
        for i in xrange(3):
            print("Task %s is working on section %s" %(self.my_id, i))
            time.sleep(1)
        return

    def print_im_here(self):
        print("here i am", self.my_id)
        return
