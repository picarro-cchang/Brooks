from PyQt4 import QtCore, QtGui
from collections import OrderedDict

class QTaskEditorWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.setLayout( self._init_gui() )
        # self._startup_settings()
        self._set_connections()
        return

    def _init_gui(self):
        self._startRunBtn = QtGui.QPushButton("Start Run")
        self._nextBtn = QtGui.QPushButton("Next")

        tgl = QtGui.QGridLayout()
        # self.taskListCB = []
        # self.taskListLBL = []
        self.taskDictCB = OrderedDict()
        gases = ["None", "GAS0", "GAS1", "GAS2", "GAS3"]
        task_id = 0
        col = 0
        for row in xrange(4):
            cb = QtGui.QComboBox()
            cb.addItems(gases)
            str = "TASK {0} ".format(task_id)
            key = "TASK{0}".format(task_id)
            self.taskDictCB[key] = cb
            lbl = QtGui.QLabel(str)
            tgl.addWidget(lbl, row, col, QtCore.Qt.AlignRight)
            tgl.addWidget(cb, row, col+1, QtCore.Qt.AlignLeft)
            task_id = task_id + 1

        self.linearRegressionRB = QtGui.QRadioButton("3/4 Point Linear Regression")
        self.spanTestRB = QtGui.QRadioButton("2 Point Span Test")
        measTypeVB = QtGui.QVBoxLayout()
        measTypeVB.addWidget(QtGui.QLabel("Validation Type"))
        measTypeVB.addWidget(self.linearRegressionRB)
        measTypeVB.addWidget(self.spanTestRB)

        topHB = QtGui.QHBoxLayout()
        topHB.addLayout(tgl)
        topHB.addLayout(measTypeVB)

        bottomHB = QtGui.QHBoxLayout()
        bottomHB.addWidget(self._startRunBtn)
        bottomHB.addWidget(self._nextBtn)

        vb = QtGui.QVBoxLayout()
        vb.addLayout(topHB)
        vb.addLayout(bottomHB)

        gb = QtGui.QGroupBox("Task Editor")
        gb.setLayout(vb)

        mgl = QtGui.QGridLayout()
        mgl.addWidget(gb, 0, 0)
        return mgl

    def _set_connections(self):
        return

    def display_task_settings(self, task_configobj):
        print(task_configobj)
        self.tco = task_configobj["TASKS"]

        for i in xrange(4):
            taskKey = "TASK{0}".format(i)
            if taskKey in self.tco:
                if "Gas" in self.tco[taskKey]:
                    gas_in_configobj = self.tco[taskKey]["Gas"]
                    idx = self.taskDictCB[taskKey].findText(gas_in_configobj)
                    print("key {0} idx {1}".format(taskKey,idx))
                    self.taskDictCB[taskKey].setCurrentIndex(idx)

        return