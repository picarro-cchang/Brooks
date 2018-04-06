# QReferenceGasEditor and QReferenceGasEditorWidget
#
# This is an editor class that is hard coded to read/write to the
# reference gas settings in the Calibration & Validation Tool.
#
# The ini format is like this:
"""
[GASES]
[[GAS0]]
Name = "Zero-air"
SN = Alpha003a
Component = CH4,CO2,H2O
Concentration = 0.02,338.0,10000
Uncertainty = 0.001, 0.2, -

[[GAS1]]
Name = "CH4, 2ppm"
SN = Alpha003b
Component = CH4,CO2,H2O
Concentration = 2.148, -, -

[[GAS2]]
Name = "CH4, 20ppm"
SN = AirGasSN4837
Component = CH4, CO2, H2O
Concentration = 20.53, -, -

[[GAS3]]
Name = "CH4, 100ppm"
SN = LAir_a09948
Component = CH4, CO2, H2O
Concentration = 105.5, -,
"""

from PyQt4 import QtCore, QtGui
import sys
from functools import partial
from Host.Common.configobj import ConfigObj

class MyDoubleValidator(QtGui.QDoubleValidator):
    """
    QDoubleValidator can be used to check the range of input but it is lacking in that
    it will allow out of range values if edit field focus is changed by the user clicking
    on another widget.  In the QDoubleValidator this is noted in the class documentation
    as the "Intermediate" state (i.e. it looks like the user is not finished entering in
    a number).

    This subclass overrides the validate method and continually checks the current
    value, preventing the user from typing any combination of numbers that exceeds the
    specified range.  It also blocks invalid characters and a blank.
    """
    def __init__(self, parent = None):
        super(MyDoubleValidator,self).__init__()
        return

    def validate(self, str, in_int):
        (state, input) = QtGui.QDoubleValidator.validate(self, str, in_int)
        try:
            if state == QtGui.QValidator.Intermediate and float(str) > self.top():
                state = QtGui.QValidator.Invalid
        except Exception as e:
            state = QtGui.QValidator.Invalid
        return state, input

class MyGasConcLineEdit(QtGui.QLineEdit):
    """
    This class is a gas concentration line edit that limits input in the
    range 0 - 1,000,000 ppm and is limited to 4 decimal places.
    """
    def __init__(self, min = 0, max = 1000000, decimal_places = 4, text = "", parent = None):
        super(MyGasConcLineEdit,self).__init__()
        validator = MyDoubleValidator()
        validator.setRange(min, max, decimal_places)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)
        self.setText(text)
        return

class MyZeroAirSelectorComboBox(QtGui.QComboBox):
    def __init__(self, default_choice = "", parent = None):
        super(MyZeroAirSelectorComboBox,self).__init__()
        self.addItems(["No", "Standard Zero < 1 ppm", "Ultra Zero < 0.1 ppm"])
        self.setCurrentIndex(self.findText(default_choice))
        return

    def wheelEvent(self, event):
        # Discard wheel input as requested
        return

class MyAccuracySelectorComboBox(QtGui.QComboBox):
    def __init__(self, default_choice = "", parent = None):
        super(MyAccuracySelectorComboBox,self).__init__()
        self.addItems(["Unk", "0.5 %", "1.0 %", "2.0 %", "5.0 %", "10.0 %"])
        self.setCurrentBestMatchIndex(default_choice)
        return

    def wheelEvent(self, event):
        # Discard wheel input as requested
        return

    def setCurrentBestMatchIndex(self, str):
        """
        Given an input string, try to find the selection index that best matches.
        :param str:
        :return:
        """
        # Try an exact string match.  If none found default to "unk" option
        if self.findText(str) > -1:
            self.setCurrentIndex(self.findText(str))
        else:
            self.setCurrentIndex(0)
        return


class QReferenceGasEditorWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self._saveBtn = QtGui.QPushButton("Save")
        self._undoBtn = QtGui.QPushButton("Undo")
        self._saveBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._undoBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._table = QReferenceGasEditor()
        self.setLayout( self._init_gui() )
        self._set_connections()
        return

    def _init_gui(self):
        # Sets up a groupbox frame with the table in the middle and UNDO and SAVE
        # buttons at the bottom right.
        hb = QtGui.QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(self._undoBtn)
        hb.addWidget(self._saveBtn)
        gl = QtGui.QGridLayout()
        gl.addWidget(self._table, 0, 0)
        gl.addLayout(hb, 1, 0)
        gb = QtGui.QGroupBox("Reference Gas Editor")
        gb.setLayout(gl)
        mgl = QtGui.QGridLayout()
        mgl.addWidget(gb,0,0)
        self._disable_undo_save()
        return mgl

    def _set_connections(self):
        self._undoBtn.clicked.connect(self._table.display_reference_gas_data)
        self._undoBtn.clicked.connect(self._disable_undo_save)
        self._saveBtn.clicked.connect(self._table.save_reference_gas_data)
        self._table.cellChanged.connect(self._enable_undo_save)
        self._table.save_success_signal.connect(self._disable_undo_save)
        self._table.save_failed_signal.connect(self._enable_undo_save)
        return

    def display_reference_gas_data(self, reference_gases_configobj):
        self._table.display_reference_gas_data(reference_gases_configobj)
        return

    def disable_edit(self, disable):
        self._undoBtn.setDisabled(disable)
        self._saveBtn.setDisabled(disable)
        self._table.disable_edit(disable)

    def _disable_undo_save(self):
        self._undoBtn.setDisabled(True)
        self._saveBtn.setDisabled(True)

    def _enable_undo_save(self):
        self._undoBtn.setEnabled(True)
        self._saveBtn.setEnabled(True)

class QReferenceGasEditor(QtGui.QTableWidget):
    save_failed_signal = QtCore.pyqtSignal()
    save_success_signal = QtCore.pyqtSignal()

    def __init__(self, data=None, *args):
        QtGui.QTableWidget.__init__(self, *args)
        self.data = data
        self.co = None                  # Ini handle (configobj)
        self.rgco = None                # Ini handle (reference gas configobj)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def display_reference_gas_data(self, reference_gases_configobj=None):
        """
        Build the table using the data from the validation ini file.
        After the UNDO or SAVE button for this table is clicked, the ini
        file is re-read and this method invoked so that the table is always
        faithful to the ini file.  In this process all cell widgets are
        destroyed and have to be reinstantiated.

        Cells are filled with QLineEdits or QComboBoxes or subclasses of
        these.  When changes are made to these widgets, their change
        signals are propogated through the QTableWidget cellChanged
        signal. This signal is then used to enable/disable the UNDO/SAVE
        buttons when the cell contents are dirty.
        :param data:
        :return:
        """

        # If we are passed a ConfigObj use that to set the table otherwise
        # use the exiting ConfigObj to reset the entries.
        if isinstance(reference_gases_configobj, ConfigObj):
            self.co = reference_gases_configobj
            self.rgco = self.co["GASES"]

        # If we are doing a reset, make sure we even have a valid
        # ConfigObj to read
        if not isinstance(self.co, ConfigObj):
            print("Table widget never connected to the ini file")
            return

        self.clear()
        self.setColumnCount(len(self.rgco))
        self.setHorizontalHeaderLabels(sorted(self.rgco.keys()))
        idx = 0
        for k,v in self.rgco.items():
            labels = []
            values = []
            if "Zero_Air" not in v:
                v["Zero_Air"] = "No"
            if "Uncertainty" not in v:
                if isinstance(v["Component"], list):
                    v["Uncertainty"] = ['-'] * len(v["Component"])
                else:
                    v["Uncertainty"] = '-'
            labels.extend(["Name", "SN", "Zero_Air"])
            values.extend([v["Name"], v["SN"], v["Zero_Air"]])
            if isinstance(v["Component"], list):
                # Handle multiple gases in the component list
                for i, name in enumerate(v["Component"]):
                    labels.append(name + " ppm")
                    labels.append(name + " acc")
                    values.append(v["Concentration"][i])
                    values.append(v["Uncertainty"][i])
            else:
                # If there is only one gas, the values are strings and not lists
                name = v["Component"]
                labels.append(name + " ppm")
                labels.append(name + " acc")
                values.append(v["Concentration"])
                values.append(v["Uncertainty"])

            self.setVerticalHeaderLabels(labels)
            self.setRowCount(len(values))
            for j, value in enumerate(values):
                if j == 2:
                    cb = MyZeroAirSelectorComboBox(values[j])
                    cb.currentIndexChanged.connect(partial(self.cellChanged.emit, j, idx))
                    self.setCellWidget(j, idx, cb)
                elif j == 3:
                    le = MyGasConcLineEdit(text = values[j])
                    le.textChanged.connect(partial(self.cellChanged.emit, j, idx))
                    self.setCellWidget(j, idx, le)
                elif j == 4:
                    cb = MyAccuracySelectorComboBox(values[j])
                    cb.currentIndexChanged.connect(partial(self.cellChanged.emit, j, idx))
                    self.setCellWidget(j, idx, cb)
                else:
                    le = QtGui.QLineEdit(text = values[j])
                    le.textChanged.connect(partial(self.cellChanged.emit, j, idx))
                    self.setCellWidget(j, idx, le)
                self.cellWidget(j, idx).setFocusPolicy(QtCore.Qt.ClickFocus)
            idx = idx + 1
        # Expand the column widths so that the table fills the space given
        # by the parent window.
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        return

    def save_reference_gas_data(self):
        """
        Reverse operation of display_reference_gas_data() to get the table data
        back into the ConfigObj format and write back out to the original
        ini file.
        :return:
        """
        if self.pass_sanity_check():
            for col in range(self.columnCount()):
                col_key = str(self.horizontalHeaderItem(col).text())
                i = 0
                self.rgco[col_key]["Name"] = str(self.cellWidget(i,col).text())
                i += 1
                self.rgco[col_key]["SN"] = str(self.cellWidget(i, col).text())
                i += 1
                self.rgco[col_key]["Zero_Air"] = str(self.cellWidget(i, col).currentText())
                i += 1
                concentration = []
                uncertainty = []
                for row in range(i, self.rowCount(), 2):
                    concentration.append(str(self.cellWidget(row,col).text()))
                    uncertainty.append(str(self.cellWidget(row+1,col).currentText()))
                if len(concentration) > 1:
                    self.rgco[col_key]["Concentration"] = concentration
                    self.rgco[col_key]["Uncertainty"] = uncertainty
                else:
                    self.rgco[col_key]["Concentration"] = concentration[0]
                    self.rgco[col_key]["Uncertainty"] = uncertainty[0]
            self.co["GASES"] = self.rgco
            self.co.write()
            self.save_success_signal.emit()
        else:
            self.save_failed_signal.emit()
        return

    def disable_edit(self, disable):
        """
        Enable/disable editing individual table cells.
        This is preferred over disabling the entire table widget because when you do
        that the scroll bars don't work and the font becomes light gray and hard
        to read.
        :param disable:
        :return:
        """
        # Note: This doesn't work if the cell contains widgets. The widgets still work.
        if disable:
            self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        else:
            self.setEditTriggers(self.editTriggers() | ~QtGui.QAbstractItemView.NoEditTriggers)
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

        # Check to make sure there are no non zero-air gases with a concentration of 0.0.
        # If this happens we will have a division by 0 when we compute % deviation.
        #
        # zero_air_error_columns tabulates the columns with problems. "col+1" makes
        # the column number user friendly.
        zero_air_error_columns = []
        for col in range(self.columnCount()):
            i = 2 # Zero-Air
            zero_air_choice = str(self.cellWidget(i, col).currentText())
            i = 3 # gas conc
            user_gas_conc = float(self.cellWidget(i, col).text())
            if "No" in zero_air_choice and user_gas_conc < 0.0001:
                ok = False
                zero_air_error_columns.append(col+1)
        if len(zero_air_error_columns) == 1:
            error_msg += "Error in column {0}.\n\n".format(', '.join(str(x) for x in zero_air_error_columns))
            error_msg += "For non-zero-air gases, set the gas concentration to more than 0.0001 ppm.\n\n"
        if len(zero_air_error_columns) > 1:
            error_msg += "Error in columns {0}.\n\n".format(', '.join(str(x) for x in zero_air_error_columns))
            error_msg += "For non-zero-air gases, set all gas concentrations to more than 0.0001 ppm.\n\n"

        # Give non-critical warnings or recommendations
        blank_field_found = False
        if ok:
            for col in range(self.columnCount()):
                i = 0
                name = str(self.cellWidget(i,col).text())
                i += 1
                sn = str(self.cellWidget(i, col).text())
                if not name or not sn:
                    blank_field_found = True
        if blank_field_found:
            error_msg += "One or more gas sources is missing a name or serial number.\n\n"
            error_msg += "Please fill out the gas information according to\n"
            error_msg += "your company's standard procedures."


        if not ok:
            not_saved_str = "CHANGES NOT SAVED\n\n"
            QtGui.QMessageBox.critical(self,
                                       'Critical',
                                       not_saved_str + error_msg,
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)
        if ok and len(error_msg):
            QtGui.QMessageBox.warning(self,
                                      'Warning',
                                      error_msg,
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
        return ok

    def wheelEvent(self, event):
        # Disable wheel input as requested
        return

def main(args):
    data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    app = QtGui.QApplication(args)
    table = QReferenceGasEditor(data, 5, 3)
    table.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)