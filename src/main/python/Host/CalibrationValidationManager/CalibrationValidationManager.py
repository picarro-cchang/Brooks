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
        self._init_gui()
        self.tm = self.setUpTasks_()
        self.show()
        self._set_connections()
        # This lets the GUI show before the GIL hands over the CPU to the TaskManager
        # QtCore.QTimer.singleShot(1,self.start_running_tasks)

    def _set_connections(self):
        self.btn.clicked.connect(self.start_running_tasks)
        self.ping_btn.clicked.connect(self.ping_running_tasks)

    def _init_gui(self):
        self.btn = QtGui.QPushButton("Run", self)
        self.btn.resize(100, 100)
        self.btn.move(100, 100)
        self.ping_btn = QtGui.QPushButton("Ping", self)
        self.ping_btn.resize(100, 100)
        self.ping_btn.move(200, 100)
        return

    def setUpTasks_(self):
        tm = TaskManager("test")
        return tm

    def start_running_tasks(self):
        print("Run clicked")
        self.tm.start_work()
        return

    def ping_running_tasks(self):
        self.tm.is_task_alive_slot()
        return

def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())

run()