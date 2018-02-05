#
#

import sys
import time
from PyQt4 import QtGui
from PyQt4 import QtCore

from Host.CalibrationValidationManager.TaskManager import TaskManager
#import Host.CalibrationValidationManager.TaskManager as TaskManager

class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("Picarro Calibration/Validation Tool")
        self.tm = self.setUpTasks_()
        self.show()
        # This lets the GUI show before the GIL hands over the CPU to the TaskManager
        QtCore.QTimer.singleShot(1,self.start_running_tasks)

    def setUpTasks_(self):
        tm = TaskManager("test")
        return tm

    def start_running_tasks(self):
        self.tm.emit_test_signal()

app = QtGui.QApplication(sys.argv)
GUI = Window()
sys.exit(app.exec_())