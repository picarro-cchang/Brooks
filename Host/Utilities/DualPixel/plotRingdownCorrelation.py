from optparse import OptionParser
from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph.dockarea import *
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import sys
import time
import timestamp
from collections import deque
from numpy import *
from BinAverager import BinAverager
from RdResultsListener import RdResultsListener
from WeatherStationListener import WeatherStationListener

BROADCAST_PORT_RDRESULTS_ZMQ = 45030
BROADCAST_PORT_PERIPH_ZMQ = 45065

paramsTemplate = [
    {'name': 'Basic parameters', 'type': 'group', 'children': [
        {'name': 'Clear', 'type': 'action'},
        {'name': 'CorrPoints', 'type': 'int',
            'value': 500, 'limits': (10, 2000)},
        {'name': 'Aggregation', 'type': 'float', 'value': 100e-3, 'dec': True,
            'siPrefix': True, 'suffix': 's', 'step': 0.2, 'limits': (50.0e-3, 5.0)},
        {'name': 'PowerLaw', 'type': 'float', 'value': 0.5, 'step': 0.05, 'limits': (0.05, 1.0)},

        {'name': 'Channel 1', 'type': 'group', 'children': [
            {'name': 'IP Address', 'type': 'str',
                'value': '10.100.3.105', 'readonly': True},
            {'name': 'Delay', 'type': 'float', 'value': 0, 'siPrefix':
                True, 'suffix': 's', 'step': 1.0e-3, 'limits': (0.0, 60.0)},
        ]},
        {'name': 'Channel 2', 'type': 'group', 'children': [
            {'name': 'IP Address', 'type': 'str',
                'value': '10.100.3.105', 'readonly': True},
            {'name': 'Delay', 'type': 'float', 'value': 200e-3, 'siPrefix':
                True, 'suffix': 's', 'step': 1.0e-3, 'limits': (0.0, 60.0)},
        ]},
        {'name': 'Notes:', 'type': 'text', 'value': 'Some text...'},
        {'name': 'Save notes and parameters', 'type': 'action'},
    ]},
]


class DateAxis(pg.AxisItem):

    def tickStrings(self, values, scale, spacing):
        strns = []
        if len(values) == 0:
            return strns
        rng = max(values) - min(values)
        # if rng < 120:
        #    return pg.AxisItem.tickStrings(self, values, scale, spacing)
        if rng < 3600 * 24:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        elif rng >= 3600 * 24 and rng < 3600 * 24 * 30:
            string = '%d'
            label1 = '%b - '
            label2 = '%b, %Y'
        elif rng >= 3600 * 24 * 30 and rng < 3600 * 24 * 30 * 24:
            string = '%b'
            label1 = '%Y -'
            label2 = ' %Y'
        elif rng >= 3600 * 24 * 30 * 24:
            string = '%Y'
            label1 = ''
            label2 = ''
        for x in values:
            try:
                strns.append(time.strftime(string, time.localtime(x)))
            except ValueError:  # Windows can't handle dates before 1970
                strns.append('')
        try:
            label = time.strftime(label1, time.localtime(min(values))) + time.strftime(
                label2, time.localtime(max(values)))
        except ValueError:
            label = ''
        # self.setLabel(text=label)
        return strns


class Form(QtGui.QMainWindow):

    def __init__(self, parent=None, options={}):
        super(Form, self).__init__(parent)
        self.corrWidget = pg.PlotWidget(title="Ringdown Listener")
        axis = DateAxis(orientation='bottom')
        self.seriesWidget = pg.PlotWidget(
            title="Time Series", axisItems={'bottom': axis})
        ipAddr1 = options.ipAddr1
        self.rdData1 = RdResultsListener(ipAddr1, BROADCAST_PORT_RDRESULTS_ZMQ)
        self.wsData1 = WeatherStationListener(ipAddr1, BROADCAST_PORT_PERIPH_ZMQ)
        ipAddr2 = options.ipAddr2
        self.rdData2 = RdResultsListener(ipAddr2, BROADCAST_PORT_RDRESULTS_ZMQ)
        self.wsData2 = WeatherStationListener(ipAddr2, BROADCAST_PORT_PERIPH_ZMQ)
        # Define deques for temporary storage of weather station data
        self.wsDeque1 = deque()
        self.wsDeque2 = deque()
        # Need to be able to save the ringdown data
        self.ba = BinAverager(avgInterval=100, nStreams=2, maxPoints=4000)
        self.scatter = self.corrWidget.plot(
            symbolSize=5, pen=None, symbolBrush=(255, 0, 0))
        self.corrWidget.enableAutoRange('xy', False)
        self.series1 = self.seriesWidget.plot(pen='y')
        self.series2 = self.seriesWidget.plot(pen='m')
        self.params = Parameter.create(
            name='Top Level', type='group', children=paramsTemplate)
        self.params.sigTreeStateChanged.connect(self.paramChangeHandler)
        self.params.param(
            'Basic parameters', 'Channel 1', 'IP Address').setValue(ipAddr1)
        self.params.param(
            'Basic parameters', 'Channel 2', 'IP Address').setValue(ipAddr2)

        self.corrCoeff = QtGui.QLabel("<font color=blue size=36><b></b></font>")
        self.slope = QtGui.QLabel("<font color=blue size=36><b></b></font>")
        self.activePoints = QtGui.QLabel("<font color=blue size=36><b></b></font>")
        self.asymm = QtGui.QLabel("<font color=red size=36><b></b></font>")
        self.rmsDev = QtGui.QLabel("<font color=green size=36><b></b></font>")

        self.paramTree = ParameterTree()
        self.paramTree.setParameters(self.params, showTop=False)
        # Get a reference to the edit box used for notes
        self.notesBox = self.params.param(
            'Basic parameters', 'Notes:').items.keyrefs()[0]().textBox
        self.notesBox.selectAll()

        self.paramTree.resize(400, 800)
        area = DockArea()

        self.setCentralWidget(area)
        self.setWindowTitle('Two pixel methane camera')
        self.resize(1024,768)

        d1 = Dock("Dock1", size=(3,4))
        d1.hideTitleBar()
        area.addDock(d1,"left")
        d1.addWidget(self.paramTree)
        d3 = Dock("Dock3")
        d3.hideTitleBar()
        area.addDock(d3,"right")
        d3.addWidget(self.corrWidget)
        d4 = Dock("Dock4")
        d4.hideTitleBar()
        area.addDock(d4,"bottom", d3)
        d4.addWidget(self.seriesWidget)
        d2 = Dock("Dock2", size=(1,1))
        d2.hideTitleBar()
        area.addDock(d2,"bottom",d1)
        w1 = pg.LayoutWidget()
        w1.addWidget(QtGui.QLabel('Correlation'),row=0,col=0)
        w1.addWidget(self.corrCoeff,row=0,col=1)
        w1.addWidget(QtGui.QLabel('Slope'),row=1,col=0)
        w1.addWidget(self.slope, row=1, col=1)
        w1.addWidget(QtGui.QLabel('Asymmetry'),row=2,col=0)
        w1.addWidget(self.asymm, row=2, col=1)
        w1.addWidget(QtGui.QLabel('RMS angle dev'),row=3,col=0)
        w1.addWidget(self.rmsDev, row=3, col=1)
        w1.addWidget(QtGui.QLabel('Active Points'),row=4,col=0)
        w1.addWidget(self.activePoints, row=4, col=1)
        d2.addWidget(w1)


        # This assigns parents to the widgets in the layout
        # self.setLayout(layout)
        self.notesBox.setFocus()
        self.noteIndex = 1

        # Open the files to save the raw ringdown data and weather station data
        now = time.time()
        fname1 = "loss_%.0f_ch1.h5" % now
        self.rdData1.setSaveFile(fname1)
        fname2 = "loss_%.0f_ch2.h5" % now
        self.rdData2.setSaveFile(fname2)

        fname1 = "ws_%.0f_ch1.h5" % now
        self.wsData1.setSaveFile(fname1)
        fname2 = "ws_%.0f_ch2.h5" % now
        self.wsData2.setSaveFile(fname2)

        self.notesFp = None
        self.notesFp = file("notes_%.0f.txt" % now, "w", 0)
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update)
        self.timer.start(200)

    def saveNotes(self):
        msg = []
        msg.append("[Note_%d]" % self.noteIndex)
        msg.append("Local_time = %s" % time.strftime("%d %b %Y %H:%M:%S"))
        msg.append("Chan_1_timestamp = %d" % self.rdData1.latestTimestamp)
        msg.append("Chan_2_timestamp = %d" % self.rdData2.latestTimestamp)
        msg.append("Points = %d" %
                   self.params.param('Basic parameters').getValues()['CorrPoints'][0])
        msg.append("Aggregation_interval = %.3f" %
                   self.params.param('Basic parameters').getValues()['Aggregation'][0])
        msg.append("Power_law = %.2f" %
                   self.params.param('Basic parameters').getValues()['PowerLaw'][0])
        msg.append("Chan_1_IP_address = %s" %
                   self.params.param('Basic parameters', 'Channel 1').getValues()['IP Address'][0])
        msg.append("Chan_1_delay = %.3f" %
                   self.params.param('Basic parameters', 'Channel 1').getValues()['Delay'][0])
        msg.append("Chan_2_IP_address = %s" %
                   self.params.param('Basic parameters', 'Channel 2').getValues()['IP Address'][0])
        msg.append("Chan_2_delay = %.3f" %
                   self.params.param('Basic parameters', 'Channel 2').getValues()['Delay'][0])
        msg.append("Notes = %r" %
                   self.params.param('Basic parameters').getValues()['Notes:'][0])
        print "\n".join(msg)
        print>>self.notesFp, "\n".join(msg) + "\n"
        self.noteIndex += 1

    def paramChangeHandler(self, param, changes):
        for which, change, data in changes:
            if which == self.params.param('Basic parameters', 'Clear') and change == 'activated':
                self.ba.clear()
            elif which == self.params.param('Basic parameters', 'Save notes and parameters') and change == 'activated':
                self.notesBox.selectAll()
                self.notesBox.setFocus()
                self.saveNotes()
            elif which == self.params.param('Basic parameters', 'Aggregation') and change == 'value':
                agg = self.params.param(
                    'Basic parameters').getValues()['Aggregation'][0]
                self.ba.setAvgInterval(int(round(1000 * agg)))
            # print "Parameter change", changes

    def getCorrPoints(self):
        return self.params.param('Basic parameters').getValues()['CorrPoints'][0]

    def getDelay1(self):
        return self.params.param('Basic parameters', 'Channel 1').getValues()['Delay'][0]

    def getDelay2(self):
        return self.params.param('Basic parameters', 'Channel 2').getValues()['Delay'][0]

    def getPowerLaw(self):
        return self.params.param('Basic parameters').getValues()['PowerLaw'][0]

    def update(self):
        kPower = self.getPowerLaw()
        self.rdData1.binAvailableData(
            int(round(1000.0 * self.getDelay1())), self.ba, 0)
        self.rdData2.binAvailableData(
            int(round(1000.0 * self.getDelay2())), self.ba, 1)
        self.wsData1.getAvailableData(self.wsDeque1, 200)
        self.wsData2.getAvailableData(self.wsDeque2, 200)

        ts = min(self.ba.streamLatest[0], self.ba.streamLatest[1])
        tx, x = self.ba.getRecentStreamData(0, ts, self.getCorrPoints())
        ty, y = self.ba.getRecentStreamData(1, ts, self.getCorrPoints())
        tx = asarray([timestamp.unixTime(t) for t in tx])
        ty = asarray([timestamp.unixTime(t) for t in ty])
        if len(x) == len(y) and len(x) > 1 and not isnan(x).all():
            # Calculate correlation coefficient
            ok = ~(isnan(x) | isnan(y))
            n = sum(ok)
            if n >= 2:
                self.scatter.setData(x, y)
                self.series1.setData(tx, x)
                self.series2.setData(ty, y)
                c1 = x[ok] - x[ok].min()
                c2 = y[ok] - y[ok].min()
                r1 = sqrt(c1*c2)
                r2 = sqrt(c1*c1 + c2*c2)
                theta = arctan2(c2,c1) - pi/4

                asym1 = sum(theta * r1**kPower)/sum(r1**kPower)
                asym2 = sum(theta * r2**kPower)/sum(r2**kPower)

                rmsDev1 = sqrt(sum(theta**2 * r1**kPower)/sum(r1**kPower))
                rmsDev2 = sqrt(sum(theta**2 * r2**kPower)/sum(r2**kPower))

                xdev = x[ok] - x[ok].mean()
                ydev = y[ok] - y[ok].mean()
                sumx = sum(x[ok])
                sumx2 = sum(x[ok] * x[ok])
                sumy = sum(y[ok])
                sumxy = sum(x[ok] * y[ok])
                slope = (-sumx * sumy + n * sumxy) / (n * sumx2 - sumx * sumx)
                corrCoeff = sum(xdev * ydev) / sqrt(
                    sum(xdev * xdev)) / sqrt(sum(ydev * ydev))
                self.corrCoeff.setText(
                    "<font color=blue size=36><b>%6.1f %%</b></font>" % (100 * corrCoeff,))
                self.slope.setText(
                    "<font color=blue size=36><b>%6.2f</b></font>" % (slope,))
                self.activePoints.setText(
                    "<font color=blue size=36><b>%d</b></font>" % (n,))
                self.asymm.setText(
                    "<font color=red size=36><b>%6.2f</b></font>" % (asym1,))
                self.rmsDev.setText(
                    "<font color=green size=36><b>%6.2f</b></font>" % (rmsDev1,))
                xmin = min(x[ok].min(), y[ok].min())
                xmax = max(x[ok].max(), y[ok].max())
                self.corrWidget.setXRange(xmin, xmax)
                self.corrWidget.setYRange(xmin, xmax)

    def closeEvent(self, event):
        self.rdData1.closeSaveFile()
        self.rdData2.closeSaveFile()
        self.wsData1.closeSaveFile()
        self.wsData2.closeSaveFile()
        self.notesFp.close()
        event.accept()  # let the window close


parser = OptionParser()
parser.add_option("-a", dest="ipAddr1", default="127.0.0.1",
                  help="IP address of first analyzer (def: 127.0.0.1)")
parser.add_option("-b", dest="ipAddr2", default="127.0.0.1",
                  help="IP address of second analyzer (def: 127.0.0.1)")
(options, args) = parser.parse_args()
app = QtGui.QApplication(sys.argv)
form = Form(options=options)
form.show()
app.exec_()
