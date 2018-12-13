# QTaskEditorWidget
#
# This is a Qt based widget to edit the TASKS section of the validation tool ini file.
# It is harded to handle a maximum of 4 gas sources and 4 measurement tasks.  This
# limit is also baked into the other widgets that comprise the validation tool.
#
# Note that the tool lets one assign gases to a task but this code doesn't validate
# the selection.  It is possible for a user to assign an undefined gas source to a
# task resulting in failure of the code.
#
from PyQt4 import QtCore, QtGui
from collections import OrderedDict
from Host.Common.configobj import ConfigObj

class MyGasSelectorComboBox(QtGui.QComboBox):
    def __init__(self, default_choice = "Skip", parent = None):
        super(MyGasSelectorComboBox,self).__init__()
        self.addItems(["Skip", "GAS0", "GAS1", "GAS2", "GAS3"])
        self.setCurrentIndex(self.findText(default_choice))
        return

    def wheelEvent(self, event):
        # Discard wheel input as requested
        return

class QTaskEditorWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.setLayout( self._init_gui() )
        self._set_connections()
        self._disable_undo_save()
        self.isEditing = False
        return

    def _init_gui(self):
        self._undoBtn = QtGui.QPushButton("Undo")
        self._saveBtn = QtGui.QPushButton("Save")
        self._undoBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._saveBtn.setFocusPolicy(QtCore.Qt.NoFocus)

        tgl = QtGui.QGridLayout()
        self.taskDictCB = OrderedDict()
        task_id = 0
        # col = 0
        for col in xrange(0,4,2):
            for row in xrange(2):
                cb = MyGasSelectorComboBox()
                cb.setFocusPolicy(QtCore.Qt.ClickFocus)
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
        self.linearRegressionValidationRB.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.spanValidationRB.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.onePointValidationRB.setFocusPolicy(QtCore.Qt.ClickFocus)
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
        mgl.setContentsMargins(10,0,10,0)
        mgl.addWidget(gb, 0, 0)
        return mgl

    def _set_connections(self):
        self._undoBtn.clicked.connect(self.display_task_settings)
        self._undoBtn.clicked.connect(self._disable_undo_save)
        self._saveBtn.clicked.connect(self.save_task_settings)
        self._saveBtn.clicked.connect(self._disable_undo_save)
        for cb in self.taskDictCB.values():
            cb.currentIndexChanged.connect(self._enable_undo_save)
        self.linearRegressionValidationRB.toggled.connect(self._enable_undo_save)
        self.spanValidationRB.toggled.connect(self._enable_undo_save)
        self.onePointValidationRB.toggled.connect(self._enable_undo_save)
        return

    def _block_all_signals(self, block):
        """
        Block the signals from the combobox and radiobutton widgets.
        These widgets emit change signals for both user changes and programatic
        changes to the settings.
        This is necessary when loading in the ini settings so that the UNDO/SAVE
        buttons are enabled while initializing the widgets.
        :param block:
        :return:
        """
        for cb in self.taskDictCB.values():
            cb.blockSignals(block)
        self.linearRegressionValidationRB.blockSignals(block)
        self.spanValidationRB.blockSignals(block)
        self.onePointValidationRB.blockSignals(block)

    def _disable_undo_save(self):
        self._undoBtn.setDisabled(True)
        self._saveBtn.setDisabled(True)
        self.isEditing = False

    def _enable_undo_save(self):
        self._undoBtn.setEnabled(True)
        self._saveBtn.setEnabled(True)
        self.isEditing = True
    # def _widget_changed(self):
    #     print("Something changed!")
    #     return

    def display_task_settings(self, task_configobj=None):
        self._block_all_signals(True)

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

        self._block_all_signals(False)
        return

    def save_task_settings(self):
        if self.pass_sanity_check():
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
        else:
            self.display_task_settings()
        return

    def pass_sanity_check(self):
        """
        Check the widget states before saving to make sure the user's choices make sense.
        :return:
        ok : True/False

        This code will return 3 states, PASS, WARNING, ERROR.

        PASS : ok = True, error_str = ""
        WARNING : ok = True, error_str = <warning messages about suspect choices like repeated gas choices>
        ERROR : ok = False, error_str = <error messages>

        If ERROR, do not save the results as the current settings can't be run.
        If WARNING, saving and running allowed but the user is advised to recheck the settings.
        """
        ok = True
        error_msg = ""
        task_choices = []
        for key, cb in self.taskDictCB.items():
            task_choices.append(cb.currentText())

        # Check to see if enough gases are measured for the analysis chosen.
        skip_count = task_choices.count("Skip")
        if self.linearRegressionValidationRB.isChecked() and skip_count > 1:
            ok = False
            error_msg += "Linear Regression requires at least 3 gas measurements."
        elif self.spanValidationRB.isChecked() and skip_count > 2:
            ok = False
            error_msg += "Span Validation requires at least 2 gas measurements."
        elif self.onePointValidationRB.isChecked() and skip_count == 4:
            ok = False
            error_msg += "One Point Validation requires at least 1 gas measurement."

        # If the user has selected enough gas measurements, now check that enough UNIQUE
        # measurements have been selected.
        gas_choices = [x for x in task_choices if 'GAS' in x]  # strip out 'Skip' steps
        uniq_gas_choices = set(gas_choices)
        if ok:
            # Linear regression check, make sure we measure at least 3 distinct gas sources.
            # We are looking for mistakes like measuring gas 0,0,3,3.  Note that we are only
            # checking for unique gas source labels and not that the concentrations are
            # spread out to get a good linear fit.
            #
            if self.linearRegressionValidationRB.isChecked() and len(uniq_gas_choices) < 3:
                ok = False
                error_msg += "You have repeated too many gas sources for a Linear Regression Analysis."

            # Span test should include at least two distinct gases sources.  The user may opt
            # for more for something like a step test.
            if self.spanValidationRB.isChecked() and len(uniq_gas_choices) < 2:
                ok = False
                error_msg += "Span Validation requires at least 2 unique gas measurements."

        # If we got this far the settings are usable but here we warn the user if they
        # may have not picked the best or recommended settings.
        if ok:
            if self.linearRegressionValidationRB.isChecked() and len(uniq_gas_choices) < len(gas_choices):
                error_msg += "You have repeated a gas measurement.\n\n"
                error_msg += "This is not recommended for the Linear Regression Analysis\n\n"
                error_msg += "Please confirm your choice."
            if self.spanValidationRB.isChecked() and len(uniq_gas_choices) > 2:
                error_msg += "You have picked more than two gas sources to measure.\n\n"
                error_msg += "For Span Validation it is recommended to only pick two."
            if self.onePointValidationRB.isChecked() and len(uniq_gas_choices) > 1:
                error_msg += "You have picked more than one gas source to measure.\n\n"
                error_msg += "For One Point Validation it is recommended to measure only one source."
            if self.onePointValidationRB.isChecked() and len(uniq_gas_choices) == 1:
                error_msg += "Be sure you have picked a gas with a reported accuracy.\n\n"
                error_msg += "If the reference gas accuracy is 'UNK' the % deviation test will not complete."

        if not ok:
            not_saved_str = "CHANGES NOT SAVED\n\n"
            dialog = QtGui.QMessageBox(self)
            dialog.setText(not_saved_str + error_msg)
            dialog.setIcon(QtGui.QMessageBox.Critical)
            dialog.setStandardButtons(QtGui.QMessageBox.Ok)
            dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.Dialog)
            dialog.exec_()
        if ok and len(error_msg):
            dialog = QtGui.QMessageBox(self)
            dialog.setText(error_msg)
            dialog.setIcon(QtGui.QMessageBox.Warning)
            dialog.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Cancel)
            dialog.setDefaultButton(QtGui.QMessageBox.Cancel)
            dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.Dialog)
            rtn = dialog.exec_()
            if rtn == QtGui.QMessageBox.Cancel:
                ok = False
        return ok