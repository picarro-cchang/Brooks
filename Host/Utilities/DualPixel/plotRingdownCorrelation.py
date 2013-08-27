
from optparse import OptionParser
from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import sys
import time
import timestamp
from collections import deque
from numpy import *
from BinAverager import BinAverager
from RdResultsListener import RdResultsListener

BROADCAST_PORT_RDRESULTS_ZMQ = 45030

paramsTemplate = [
    {'name':'Basic parameters', 'type':'group', 'children':[
        {'name':'Clear', 'type': 'action'},
        {'name':'CorrPoints', 'type':'int', 'value':500, 'limits':(10,500)},
        {'name':'Aggregation', 'type':'float', 'value':100e-3, 'dec': True, 'siPrefix':True, 'suffix':'s', 'step':0.2, 'limits':(50.0e-3,5.0)},
        {'name':'Channel 1', 'type':'group', 'children': [
            {'name':'IP Address', 'type':'str', 'value': '10.100.3.105', 'readonly': True},
            {'name':'Delay', 'type':'float', 'value': 0, 'siPrefix':True, 'suffix':'s', 'step':1.0e-3, 'limits':(0.0,60.0) },
        ]},
        {'name':'Channel 2', 'type':'group', 'children': [
            {'name':'IP Address', 'type':'str', 'value': '10.100.3.105', 'readonly': True},
            {'name':'Delay', 'type':'float', 'value': 200e-3, 'siPrefix':True, 'suffix':'s', 'step':1.0e-3, 'limits':(0.0,60.0) },
        ]},
        {'name': 'Notes:', 'type': 'text', 'value': 'Some text...'},
        {'name':'Save notes and parameters', 'type': 'action'},
    ]},
]

class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strns = []
        if len(values) == 0: return strns
        rng = max(values)-min(values)
        #if rng < 120:
        #    return pg.AxisItem.tickStrings(self, values, scale, spacing)
        if rng < 3600*24:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        elif rng >= 3600*24 and rng < 3600*24*30:
            string = '%d'
            label1 = '%b - '
            label2 = '%b, %Y'
        elif rng >= 3600*24*30 and rng < 3600*24*30*24:
            string = '%b'
            label1 = '%Y -'
            label2 = ' %Y'
        elif rng >=3600*24*30*24:
            string = '%Y'
            label1 = ''
            label2 = ''
        for x in values:
            try:
                strns.append(time.strftime(string, time.localtime(x)))
            except ValueError:  ## Windows can't handle dates before 1970
                strns.append('')
        try:
            label = time.strftime(label1, time.localtime(min(values)))+time.strftime(label2, time.localtime(max(values)))
        except ValueError:
            label = ''
        #self.setLabel(text=label)
        return strns
    
class Form(QtGui.QDialog):
    def __init__(self, parent=None, options={}):
        super(Form, self).__init__(parent)
        self.corrWidget = pg.PlotWidget(title="Ringdown Listener")
        axis = DateAxis(orientation='bottom')
        self.seriesWidget = pg.PlotWidget(title="Time Series",axisItems={'bottom': axis})
        ipAddr1 = options.ipAddr1
        self.rdData1 = RdResultsListener(ipAddr1, BROADCAST_PORT_RDRESULTS_ZMQ)
        ipAddr2 = options.ipAddr2
        self.rdData2 = RdResultsListener(ipAddr2, BROADCAST_PORT_RDRESULTS_ZMQ)
        # Need to be able to save the ringdown data
        self.ba = BinAverager(avgInterval=100, nStreams=2, maxPoints=1000)
        self.scatter = self.corrWidget.plot(symbolSize=5, pen=None, symbolBrush=(255,0,0))
        self.corrWidget.enableAutoRange('xy', False)
        self.series1 = self.seriesWidget.plot(pen='y')
        self.series2 = self.seriesWidget.plot(pen='m')
        self.params = Parameter.create(name='Top Level', type='group', children=paramsTemplate)
        self.params.sigTreeStateChanged.connect(self.paramChangeHandler)
        self.params.param('Basic parameters','Channel 1','IP Address').setValue(ipAddr1)
        self.params.param('Basic parameters','Channel 2','IP Address').setValue(ipAddr2)

        self.corrCoeff = QtGui.QLabel("<font color=blue size=36><b></b></font>")
        self.slope = QtGui.QLabel("<font color=blue size=36><b></b></font>")
        self.activePoints = QtGui.QLabel("<font color=blue size=36><b></b></font>")

        self.paramTree = ParameterTree()
        self.paramTree.setParameters(self.params, showTop=False)
        # Get a reference to the edit box used for notes
        self.notesBox = self.params.param('Basic parameters','Notes:').items.keyrefs()[0]().textBox
        self.notesBox.selectAll()
        
        self.paramTree.resize(400,800)
        layout = QtGui.QHBoxLayout()
        layoutL = QtGui.QVBoxLayout()
        layoutR = QtGui.QVBoxLayout()
        layoutResults = QtGui.QFormLayout()
        layoutResults.addRow('Correlation',self.corrCoeff)
        layoutResults.addRow('Slope',self.slope)
        layoutResults.addRow('Active Points',self.activePoints)
        
        layoutL.addWidget(self.paramTree)
        layoutL.addLayout(layoutResults)
        layoutR.addWidget(self.corrWidget)
        layoutR.addWidget(self.seriesWidget)
        layout.addLayout(layoutL)
        layout.addLayout(layoutR)
        self.setLayout(layout) # This assigns parents to the widgets in the layout
        self.notesBox.setFocus()
        self.noteIndex = 1

        # Open the files to save the raw ringdown data
        now = time.time()
        fname1 = "loss_%.0f_ch1.h5" % now
        self.rdData1.setSaveFile(fname1)
        fname2 = "loss_%.0f_ch2.h5" % now
        self.rdData2.setSaveFile(fname2)
        self.notesFp = None
        self.notesFp = file("notes_%.0f.txt" % now,"w",0)        
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update)
        self.timer.start(200)
        
    def saveNotes(self):
        msg = []
        msg.append("[Note_%d]" % self.noteIndex)
        msg.append("Local_time = %s" % time.strftime("%d %b %Y %H:%M:%S"))
        msg.append("Chan_1_timestamp = %d" % self.rdData1.latestTimestamp)
        msg.append("Chan_2_timestamp = %d" % self.rdData2.latestTimestamp)
        msg.append("Points = %d" % self.params.param('Basic parameters').getValues()['CorrPoints'][0])
        msg.append("Aggregation_interval = %.3f" % self.params.param('Basic parameters').getValues()['Aggregation'][0])
        msg.append("Chan_1_delay = %.3f" % self.params.param('Basic parameters','Channel 1').getValues()['Delay'][0])
        msg.append("Chan_2_delay = %.3f" % self.params.param('Basic parameters','Channel 2').getValues()['Delay'][0])
        msg.append("Notes = %r" % self.params.param('Basic parameters').getValues()['Notes:'][0])
        print "\n".join(msg)
        print>>self.notesFp, "\n".join(msg) + "\n"
        self.noteIndex += 1

    def paramChangeHandler(self, param, changes):
        for which,change,data in changes:
            if which == self.params.param('Basic parameters','Clear') and change == 'activated':
                self.ba.clear()
            elif which == self.params.param('Basic parameters','Save notes and parameters') and change == 'activated':
                self.notesBox.selectAll()
                self.notesBox.setFocus()
                self.saveNotes()
            elif which == self.params.param('Basic parameters','Aggregation') and change == 'value':
                agg = self.params.param('Basic parameters').getValues()['Aggregation'][0]
                self.ba.setAvgInterval(int(round(1000*agg)))
            # print "Parameter change", changes
    
    def getCorrPoints(self):
        return self.params.param('Basic parameters').getValues()['CorrPoints'][0]
    
    def getDelay1(self):
        return self.params.param('Basic parameters','Channel 1').getValues()['Delay'][0]
    
    def getDelay2(self):
        return self.params.param('Basic parameters','Channel 2').getValues()['Delay'][0]
    
    def update(self):
        self.rdData1.binAvailableData(int(round(1000.0*self.getDelay1())),self.ba,0)
        self.rdData2.binAvailableData(int(round(1000.0*self.getDelay2())),self.ba,1)
        ts = min(self.ba.streamLatest[0],self.ba.streamLatest[1])
        tx, x = self.ba.getRecentStreamData(0,ts,self.getCorrPoints())
        ty, y = self.ba.getRecentStreamData(1,ts,self.getCorrPoints())
        tx = asarray([timestamp.unixTime(t) for t in tx])
        ty = asarray([timestamp.unixTime(t) for t in ty])
        if len(x) == len(y) and len(x)>1 and not isnan(x).all():
            # Calculate correlation coefficient
            ok = ~(isnan(x) | isnan(y))
            n = sum(ok)
            if n>=2:
                self.scatter.setData(x,y)
                self.series1.setData(tx,x)
                self.series2.setData(ty,y)
                xdev = x[ok]-x[ok].mean()
                ydev = y[ok]-y[ok].mean()
                sumx = sum(x[ok])
                sumx2 = sum(x[ok]*x[ok])
                sumy = sum(y[ok])
                sumxy = sum(x[ok]*y[ok])
                slope = (-sumx*sumy + n*sumxy)/(n*sumx2 - sumx*sumx)
                corrCoeff = sum(xdev*ydev)/sqrt(sum(xdev*xdev))/sqrt(sum(ydev*ydev))
                self.corrCoeff.setText("<font color=blue size=36><b>%6.1f %%</b></font>" % (100*corrCoeff,))
                self.slope.setText("<font color=blue size=36><b>%6.2f</b></font>" % (slope,))
                self.activePoints.setText("<font color=blue size=36><b>%d</b></font>" % (n,))
                xmin = min(x[ok].min(),y[ok].min())
                xmax = max(x[ok].max(),y[ok].max())
                self.corrWidget.setXRange(xmin, xmax)
                self.corrWidget.setYRange(xmin, xmax)
            
    def closeEvent(self, event):
        self.rdData1.closeSaveFile()
        self.rdData2.closeSaveFile()
        self.notesFp.close()
        event.accept() # let the window close
            
            
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