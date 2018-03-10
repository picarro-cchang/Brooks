from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
from DateAxisItem import DateAxisItem

class QPlotWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self._saveBtn = QtGui.QPushButton("Save")
        self._undoBtn = QtGui.QPushButton("Undo")
        self._plot_widget = self._init_plot()
        self._plot_str_data = QtGui.QLabel("the label")
        self.setLayout( self._init_gui() )
        # self._set_connections()
        return

    def _init_gui(self):
        gl = QtGui.QGridLayout()
        gl.addWidget(self._plot_widget, 0, 0)
        gl.addWidget(self._plot_str_data, 1, 0, QtCore.Qt.AlignHCenter)
        return gl

    def _init_plot(self):
        time_axis = DateAxisItem("bottom")
        self._time_series_plot = pg.PlotWidget(axisItems={'bottom':time_axis})
        self._time_series_plot.setMouseEnabled(x=False,y=False)
        self._time_series_plot.setMenuEnabled(False)
        self._time_series_plot.showGrid(x=True, y=True)
        self._time_series_plot.setLabels(left="CH4 (ppm)")

        # Seems to keep time stamp labels from overlapping with eachother and over
        # the y-axis label.
        self._time_series_plot.getAxis("bottom").setStyle(autoExpandTextSpace=False)

        # Add top and right axes without labels to create a box around the plot.
        self._time_series_plot.showAxis("top",show=True)
        self._time_series_plot.getAxis("top").setStyle(showValues=False)
        self._time_series_plot.showAxis("right",show=True)
        self._time_series_plot.getAxis("right").setStyle(showValues=False)

        self._the_plot = self._time_series_plot.plot(width=1, symbol='o')
        return self._time_series_plot

    def setData(self,x,y,d={}):
        self._the_plot.setData(x,y)
        str = ""
        for k,v in d.items():
            str += " {0} = {1:.3f} ".format(k,v)
        self._plot_str_data.setText(QtCore.QString(str))
        return