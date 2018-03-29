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
from Host.Common.configobj import ConfigObj

class QReferenceGasEditorWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self._saveBtn = QtGui.QPushButton("Save")
        self._undoBtn = QtGui.QPushButton("Undo")
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
        return mgl

    def _set_connections(self):
        self._undoBtn.clicked.connect(self._table.display_reference_gas_data)
        self._saveBtn.clicked.connect(self._table.save_reference_gas_data)
        return

    def display_reference_gas_data(self, reference_gases_configobj):
        self._table.display_reference_gas_data(reference_gases_configobj)
        return

    def disable_edit(self, disable):
        self._undoBtn.setDisabled(disable)
        self._saveBtn.setDisabled(disable)
        self._table.disable_edit(disable)


class QReferenceGasEditor(QtGui.QTableWidget):
    def __init__(self, data=None, *args):
        QtGui.QTableWidget.__init__(self, *args)
        self.data = data
        self.co = None                  # Ini handle (configobj)
        self.rgco = None                # Ini handle (reference gas configobj)

    def display_reference_gas_data(self, reference_gases_configobj=None):
        """
        data is a dictionary of ReferenceGas objects
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
            # if "Desc" not in v:
            #     v["Desc"] = ""
            # if "Vendor" not in v:
            #     v["Vendor"] = ""
            if "Zero_Air" not in v:
                v["Zero_Air"] = "No"
            if "Uncertainty" not in v:
                if isinstance(v["Component"], list):
                    v["Uncertainty"] = ['-'] * len(v["Component"])
                else:
                    v["Uncertainty"] = '-'
            # labels.extend(["Name", "SN", "Desc", "Vendor", "Zero_Air"])
            # values.extend([v["Name"], v["SN"], v["Desc"], v["Vendor"], v["Zero_Air"]])
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
                self.setItem(j, idx, QtGui.QTableWidgetItem(values[j]))
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
        for col in range(self.columnCount()):
            col_key = str(self.horizontalHeaderItem(col).text())
            i = 0
            self.rgco[col_key]["Name"] = str(self.item(i,col).text())
            i += 1
            self.rgco[col_key]["SN"] = str(self.item(i, col).text())
            # i += 1
            # self.rgco[col_key]["Desc"] = str(self.item(i, col).text())
            # i += 1
            # self.rgco[col_key]["Vendor"] = str(self.item(i, col).text())
            i += 1
            self.rgco[col_key]["Zero_Air"] = str(self.item(i, col).text())
            i += 1
            concentration = []
            uncertainty = []
            for row in range(i, self.rowCount(), 2):
                concentration.append(str(self.item(row,col).text()))
                uncertainty.append(str(self.item(row+1,col).text()))
            if len(concentration) > 1:
                self.rgco[col_key]["Concentration"] = concentration
                self.rgco[col_key]["Uncertainty"] = uncertainty
            else:
                self.rgco[col_key]["Concentration"] = concentration[0]
                self.rgco[col_key]["Uncertainty"] = uncertainty[0]
        self.co["GASES"] = self.rgco
        self.co.write()
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
        if disable:
            self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        else:
            self.setEditTriggers(self.editTriggers() | ~QtGui.QAbstractItemView.NoEditTriggers)
        return


def main(args):
    data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    app = QtGui.QApplication(args)
    table = QReferenceGasEditor(data, 5, 3)
    table.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)