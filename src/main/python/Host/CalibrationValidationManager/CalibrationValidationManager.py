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
        self.setGeometry(50, 50, 500, 500)
        self.setWindowTitle("Picarro Calibration/Validation Tool")
        self.tm = None
        self._init_gui()
        self.tm = self.setUpTasks_()
        self.show()
        self._set_connections()
        return

    def _set_connections(self):
        self.btn.clicked.connect(self.start_running_tasks)
        self.ping_btn.clicked.connect(self.ping_running_tasks)
        self.next_btn.clicked.connect(self.tm.next_subtask_signal)
        self.tm.task_countdown_signal.connect(self.update_progressbar)

    def _init_gui(self):
        self.btn = QtGui.QPushButton("Run", self)
        self.ping_btn = QtGui.QPushButton("Ping", self)
        self.next_btn = QtGui.QPushButton("NEXT", self)
        self.task_label = QtGui.QLabel("Progress so far...")
        self.task_progressbar = QtGui.QProgressBar()
        self.task_progressbar.setValue(0)
        gl = QtGui.QGridLayout()
        gl.addWidget(self.btn,0,0)
        gl.addWidget(self.ping_btn,1,0)
        gl.addWidget(self.task_label,2,0)
        gl.addWidget(self.task_progressbar,3,0)
        gl.addWidget(self.next_btn,4,0)
        central_widget = QtGui.QWidget()
        central_widget.setLayout(gl)
        self.setCentralWidget(central_widget)
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

    def update_progressbar(self, countdown_sec, set_time_sec, description):
        self.task_progressbar.setValue((set_time_sec - countdown_sec)*100/set_time_sec)
        self.task_label.setText(QtCore.QString(description))
        return

def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())

run()