from PyQt4 import QtCore, QtGui
from collections import OrderedDict
from Host.Common.configobj import ConfigObj

class QTaskEditorWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.setLayout( self._init_gui() )
        # self._startup_settings()
        self._set_connections()
        return

    def _init_gui(self):
        self._undoBtn = QtGui.QPushButton("Undo")
        self._saveBtn = QtGui.QPushButton("Save")

        tgl = QtGui.QGridLayout()
        # self.taskListCB = []
        # self.taskListLBL = []
        self.taskDictCB = OrderedDict()
        gases = ["Skip", "GAS0", "GAS1", "GAS2", "GAS3"]
        task_id = 0
        # col = 0
        for col in xrange(0,4,2):
            for row in xrange(2):
                cb = QtGui.QComboBox()
                cb.addItems(gases)
                str = "  TASK {0} ".format(task_id)
                key = "TASK{0}".format(task_id)
                self.taskDictCB[key] = cb
                lbl = QtGui.QLabel(str)
                tgl.addWidget(lbl, row, col, QtCore.Qt.AlignRight)
                tgl.addWidget(cb, row, col+1, QtCore.Qt.AlignLeft)
                task_id = task_id + 1

        self.linearRegressionValidationRB = QtGui.QRadioButton("3 or 4 Gas Linear Regression Validation")
        self.spanValidationRB = QtGui.QRadioButton("2 Gas Span Validation")
        self.onePointValidationRB = QtGui.QRadioButton("1 Gas Validation")
        mhbl = QtGui.QVBoxLayout()
        mhbl.addWidget(QtGui.QLabel("Validation Type"))
        mhbl.addWidget(self.onePointValidationRB)
        mhbl.addWidget(self.spanValidationRB)
        mhbl.addWidget(self.linearRegressionValidationRB)

        bottomHB = QtGui.QHBoxLayout()
        bottomHB.addWidget(self._undoBtn)
        bottomHB.addWidget(self._saveBtn)

        hb = QtGui.QHBoxLayout()
        hb.addLayout(mhbl)
        hb.addStretch(1)
        hb.addLayout(tgl)
        hb.addStretch(1)
        hb.addLayout(bottomHB)

        gb = QtGui.QGroupBox("Task Editor")
        gb.setLayout(hb)

        mgl = QtGui.QGridLayout()
        mgl.addWidget(gb, 0, 0)
        return mgl

    def _set_connections(self):
        self._undoBtn.clicked.connect(self.display_task_settings)
        self._saveBtn.clicked.connect(self.save_task_settings)
        return

    def display_task_settings(self, task_configobj=None):
        # If we are passed a ConfigObj use that to set the task editor otherwise
        # use the exiting ConfigObj to reset the entries.
        if isinstance(task_configobj, ConfigObj):
            self.co = task_configobj
            self.tco = self.co["TASKS"]

        # If we are doing a reset, make sure we even have a valid
        # ConfigObj to read
        if not isinstance(self.co, ConfigObj):
            print("Task editor widget never connected to the ini file")
            return

        for i in xrange(4):
            taskKey = "TASK{0}".format(i)
            if taskKey in self.tco:
                if "Gas" in self.tco[taskKey]:
                    gas_in_configobj = self.tco[taskKey]["Gas"]
                    idx = self.taskDictCB[taskKey].findText(gas_in_configobj)
                    self.taskDictCB[taskKey].setCurrentIndex(idx)
        if "Linear_Regression" in self.tco["TASK4"]["Analysis"]:
            self.linearRegressionValidationRB.setChecked(True)
        elif "Span" in self.tco["TASK4"]["Analysis"]:
            self.spanValidationRB.setChecked(True)
        else:
            self.onePointValidationRB.setChecked(True)
        return

    def save_task_settings(self):
        for key, cb in self.taskDictCB.items():
            self.tco[key]["Gas"] = cb.currentText()
        if self.linearRegressionValidationRB.isChecked():
            self.tco["TASK4"]["Analysis"] = "Linear_Regression_Validation"
        elif self.spanValidationRB.isChecked():
            self.tco["TASK4"]["Analysis"] = "Span_Validation"
        else:
            self.tco["TASK4"]["Analysis"] = "One_Point_Validation"
        self.co["TASKS"] = self.tco
        self.co.write()
        return