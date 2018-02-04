#
#

import sys
from PyQt4 import QtGui

from Host.CalibrationValidationManager.TaskManager import TaskManager
#import Host.CalibrationValidationManager.TaskManager as TaskManager

class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("Picarro Calibration/Validation Tool")
        #self.setWindowIcon(QtGui.QIcon("PicarroAMC.jpg"))
        self.setUpTasks_()
        self.show()

    def setUpTasks_(self):
        tm = TaskManager("test")
        tm.emit_test_signal()
        return

app = QtGui.QApplication(sys.argv)
GUI = Window()
sys.exit(app.exec_())