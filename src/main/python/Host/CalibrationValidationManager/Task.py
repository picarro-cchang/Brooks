# TaskManager
#
# Need:
#   Instructions (what to do)
#   RefGas (if measuring a gas and comparing to a measurement in this object)
#   Data source (if measuring an unknown gas we need the data)
#   Timer (for time based evolution of the task or sub-tasks)
#   Signals (to indicate progress or completion)
#   Slots (to accept commands to start, pause, abort)

from PyQt4 import QtGui, QtCore

class Task(object):
    def __init__(self, settings = {}, refGas = None):
        print("initializing task:", dict)
        self.referenceGas = refGas
        self.settings = settings
        return

    def set_connections(self):
        return

    def stop_slot(self):
        print("Task received stop command")
        return
