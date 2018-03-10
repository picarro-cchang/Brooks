from PyQt4 import QtCore, QtGui
import sys
from Host.Common.configobj import ConfigObj
import pprint
from ReferenceGas import ReferenceGas

data = {'col1': ['1', '2', '3'], 'col2': ['4', '5', '6'], 'col3': ['7', '8', '9']}

class QReferenceGasEditorWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        # super(QReferenceGasEditorWidget, self)._init__(parent)
        QtGui.QWidget.__init__(self)
        self._saveBtn = QtGui.QPushButton("Save")
        self._undoBtn = QtGui.QPushButton("Undo")
        self.table = QReferenceGasEditor()
        self.setLayout( self._init_gui() )
        self._set_connections()
        return

    def _init_gui(self):
        hb = QtGui.QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(self._undoBtn)
        hb.addWidget(self._saveBtn)
        gl = QtGui.QGridLayout()
        gl.addWidget(self.table, 0, 0)
        gl.addLayout(hb, 1, 0)
        return gl

    def _set_connections(self):
        self._undoBtn.clicked.connect(self.table.display_reference_gas_data)
        self._saveBtn.clicked.connect(self.table.save_reference_gas_data)
        return

    def display_referenece_gas_data(self, reference_gases_configobj):
        self.table.display_reference_gas_data(reference_gases_configobj)
        return

class QReferenceGasEditor(QtGui.QTableWidget):
    def __init__(self, data=None, *args):
        QtGui.QTableWidget.__init__(self, *args)
        self.data = data
        self.co = None                  # Ini handle (configobj)
        self.rgco = None                # Ini handle (reference gas configobj)
        # self.setmydata()
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def display_reference_gas_data(self, reference_gases_configobj=None):
        # print("undo data",reference_gases_configobj)
        # return
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
            if "Desc" not in v:
                v["Desc"] = ""
            if "Vendor" not in v:
                v["Vendor"] = ""
            if "Uncertainty" not in v:
                v["Uncertainty"] = ['-'] * len(v["Component"])
            labels = ["Name", "SN", "Desc", "Vendor"]
            values = [v["Name"], v["SN"], v["Desc"], v["Vendor"]]
            for i, name in enumerate(v["Component"]):
                labels.append(name + " ppm")
                labels.append(name + " acc")
                values.append(v["Concentration"][i])
                values.append(v["Uncertainty"][i])

            self.setVerticalHeaderLabels(labels)
            self.setRowCount(len(values))
            for j, value in enumerate(values):
                self.setItem(j, idx, QtGui.QTableWidgetItem(values[j]))
            idx = idx + 1
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        return

    def save_reference_gas_data(self):
        for col in range(self.columnCount()):
            col_key = str(self.horizontalHeaderItem(col).text())
            self.rgco[col_key]["Name"] = str(self.item(0,col).text())
            self.rgco[col_key]["SN"] = str(self.item(1, col).text())
            self.rgco[col_key]["Desc"] = str(self.item(2, col).text())
            self.rgco[col_key]["Vendor"] = str(self.item(3, col).text())
            # component = []
            concentration = []
            uncertainty = []
            for row in range(4,self.rowCount(),2):
                concentration.append(str(self.item(row,col).text()))
                uncertainty.append(str(self.item(row+1,col).text()))
            self.rgco[col_key]["Concentration"] = concentration
            self.rgco[col_key]["Uncertainty"] = uncertainty
        self.co["GASES"] = self.rgco
        self.co.write()
        return

    def setmydata(self):
        horHeaders = []
        for n, key in enumerate(sorted(self.data.keys())):
            horHeaders.append(key)
            for m, item in enumerate(self.data[key]):
                newitem = QtGui.QTableWidgetItem(item)
                self.setItem(m, n, newitem)
        self.setHorizontalHeaderLabels(horHeaders)


def main(args):
    app = QtGui.QApplication(args)
    table = QReferenceGasEditor(data, 5, 3)
    table.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)