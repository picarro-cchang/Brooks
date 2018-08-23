import time
import os
import sys
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'
from traits.api import *
from traitsui.api import *
from traitsui.menu import *
from traitsui.message import message, error
from traitsui.qt4.editor import Editor
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.table_column import ObjectColumn
import threading
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import PyDAQmx as daq
import Queue
import threading
import win32gui
import webbrowser
from collections import deque

from Host.Common import CmdFIFO, WlmCalUtilities
from Host.Common.SharedTypes import RPC_PORT_DRIVER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.autogen.interface import LASER_CURRENT_CNTRL_DisabledState, LASER_CURRENT_CNTRL_ManualState, \
                                   SPECT_CNTRL_IdleState, TEMP_CNTRL_EnabledState, TEMP_CNTRL_SweepingState

APP_NAME = "WLMStation"
Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                   ClientName = APP_NAME)

class _QtGraphEditor(Editor):
    scrollable  = True

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self, parent):
        frame = QtGui.QWidget()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        canvas = pg.GraphicsLayoutWidget()
        canvas.addItem(self.object.figure)
       
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(canvas)
        frame.setLayout(vbox)
        return frame

class QtGraphEditor(BasicEditorFactory):
    klass = _QtGraphEditor

class Laser(HasTraits):
    laserIndex = Int
    maxSweepValue = Float
    minSweepValue = Float
    sweepSpeed = Float
    fullScanTime = Float
    fitDataNum = Int
    temperature = Float
    current = Float
    
class NewUnitSelector(HasTraits):
    unitList = ListStr
    selectedUnit = Str
    newUnitName = Str("WLM")
    action = Enum(0, 1)
    
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        self.traits_view = View(
                                VGroup(
                                    Item(label=' '),
                                    HGroup(
                                        Item(label=' '*5),
                                        Item('action', editor=EnumEditor(values={0:'Select existing unit', 1:'Create new unit'}), 
                                              show_label=False, style='custom', height=-47),
                                        VGroup(
                                            Item('newUnitName', enabled_when='action==1'),
                                            Item('selectedUnit', editor=EnumEditor(name='unitList'), enabled_when='action==0')
                                            ),
                                        Item(label=' '*5)
                                        ),
                                    Item(label=' ')
                                ),
                            buttons=OKCancelButtons, title="Create or Select a unit", kind="livemodal")
    
class WLMStationHandler(Handler):
    def getUnitList(self, info):
        folders = []
        for f in os.listdir(info.object.fileDir):
            path = os.path.join(info.object.fileDir, f)
            if os.path.isdir(path) and f.startswith("WLM"):
                folders.append(f)
        return folders
        
    def onNewUnit(self, info):
        obj = info.object
        ns = NewUnitSelector(unitList=self.getUnitList(info))
        ns.configure_traits(view=ns.traits_view)
        if ns.action == 0 and len(ns.selectedUnit) > 0:
            obj.unitName = ns.selectedUnit
        elif ns.action == 1 and len(ns.newUnitName) > 3:
            if not ns.newUnitName.startswith("WLM"):
                error(message = "  Unit name should start with 'WLM'! ", title = 'Error', buttons = ['OK'])
                return
            obj.unitName = ns.newUnitName
            path = os.path.join(obj.fileDir, obj.unitName)
            if not os.path.isdir(path):
                os.makedirs(path)
        else:
            return
        obj.figure.setLabels(title=obj.unitName)
            
    def onSetConfig(self, info):
        obj = info.object
        obj.configure_traits(view=obj.edit_view)
        obj.WLM_channels = "Dev1/ai%d,Dev1/ai%d,Dev1/ai%d,Dev1/ai%d" % (obj.channelForReference1, obj.channelForReference2, \
                                obj.channelForEtalon1, obj.channelForEtalon2)
        
    def onLoadOffset(self, info):
        obj = info.object
        file = pg.FileDialog.getOpenFileName(None, 'Select dark current config file', os.getcwd(), "Config files (*.ini)")
        if os.path.exists(file):
            config = CustomConfigObj(file)
            obj.etalon1Offset = config.getfloat('Main', 'etalon1Offset')
            obj.reference1Offset = config.getfloat('Main', 'reference1Offset')
            obj.etalon2Offset = config.getfloat('Main', 'etalon2Offset')
            obj.reference2Offset = config.getfloat('Main', 'reference2Offset')
            obj.enableMeasure = True
    
    def onMeasureOffset(self, info):
        obj = info.object
        dc = getDarkCurrent(obj.WLM_channels, obj.laserNum)
        optRun = threading.Thread(target = dc.run)
        optRun.setDaemon(True)
        optRun.start()
        pb = ProgressBar(title="Measuring Offset...", object=dc)
        pb.configure_traits(view=pb.traits_view)
        margin = ' '*5
        msg = "\n" + margin + "Reference1 Offset = %.4f \n" % dc.reference1_offset + \
              margin + "Reference2 Offset = %.4f \n" % dc.reference2_offset + \
              margin + "Etalon1 Offset = %.4f \n" % dc.etalon1_offset + \
              margin + "Etalon2 Offset = %.4f \n\n" % dc.etalon2_offset + \
              margin + "Update dark current setting and save as config file?   \n"
        if message(message=msg, title='Dark Current', buttons=OKCancelButtons):
            obj.etalon1Offset = dc.etalon1_offset
            obj.reference1Offset = dc.reference1_offset
            obj.etalon2Offset = dc.etalon2_offset
            obj.reference2Offset = dc.reference2_offset
       
            # defaultPath = os.getcwd() + r'\DarkCurrent_' + time.strftime('%Y-%m-%d_%H-%M-%S') + '.ini'
            # file = pg.FileDialog.getSaveFileName(None, 'Select dark current config file', defaultPath, "Config files (*.ini)")
            # if file:
                # with open(file, 'w') as f:
                    # f.write('[Main]\n')
                    # f.write('etalon1Offset = %s\n' % dc.etalon1_offset)
                    # f.write('reference1Offset = %s\n' % dc.reference1_offset)
                    # f.write('etalon2Offset = %s\n' % dc.etalon2_offset)
                    # f.write('reference2Offset = %s' % dc.reference2_offset)
                
    def onTakeScreenshot(self, info):
        obj = info.object
        if obj.unitName is None:
            self.onNewUnit(info)
        if obj.unitName:
            dirPath = os.path.join(obj.fileDir, obj.unitName, "Screen Captures")
            if not os.path.isdir(dirPath):
                os.makedirs(dirPath)
            file = os.path.join(dirPath, time.strftime('Screenshot_%Y-%m-%d_%H-%M-%S.jpg'))
            hwnd = win32gui.FindWindow(None, 'Picarro WLMStation')
            QtGui.QPixmap.grabWindow(hwnd).save(file, 'jpg')
            message(message="Screenshot is saved at: %s" % file, title = 'Screenshot', buttons = ['OK'])
                
    def onSaveConfig(self, info):
        obj = info.object
        with open(obj.configPath, 'w') as f:
            f.write('[Main]\n')
            f.write('FileDir = %s\n' % obj.fileDir)
            f.write('Laser_Num = %d\n' % obj.totalLaserNum)
            f.write('Laser_Coarse_Current_Convertor = %s\n' % obj.coarseCurrentConvertor)
            f.write('Laser_Fine_Current_Convertor = %s\n' % obj.fineCurrentConvertor)
            f.write( 'Laser_Current_Offset = %s\n' % obj.laserCurrentOffset)
            f.write('[Acquisition]\n')
            f.write('Channel_Etalon1 = %d\n' % obj.channelForEtalon1)
            f.write('Channel_Etalon2 = %d\n' % obj.channelForEtalon2)
            f.write('Channel_Reference1 = %d\n' % obj.channelForReference1)
            f.write('Channel_Reference2 = %d\n' % obj.channelForReference2)
            f.write('Channel_PowerMeter = %d\n' % obj.channelForPowerMeter)
            f.write('Etalon1_Gain = %s\n' % obj.etalon1Gain)
            f.write('Etalon2_Gain = %s\n' % obj.etalon2Gain)
            f.write('Reference1_Gain = %s\n' % obj.reference1Gain)
            f.write('Reference2_Gain = %s\n' % obj.reference2Gain)
            f.write('[Sampling]\n')
            f.write('Sample_Rate = %d\n' % obj.sampleRate)
            f.write('Sample_Time = %s\n' % obj.sampleTime)
            f.write('Monitor_Rate = %d\n' % obj.monitorRate)
            f.write('Monitor_Time_Span = %d\n' % obj.monitorTimeSpan)
            for i in range(obj.totalLaserNum):
                f.write('[Laser%d]\n' % (i + 1))
                f.write('Laser_Index = %d\n' % obj.lasers[i].laserIndex)
                f.write('Max_Sweep_Value = %s\n' % obj.lasers[i].maxSweepValue)
                f.write('Min_Sweep_Value = %s\n' % obj.lasers[i].minSweepValue)
                f.write('Sweep_Speed = %s\n' % obj.lasers[i].sweepSpeed)
                f.write('Full_Scan_Time = %s\n' % obj.lasers[i].fullScanTime)
                f.write('Fit_DataSet_Num = %d\n' % obj.lasers[i].fitDataNum)
                f.write('Temperature = %s\n' % obj.lasers[i].temperature)
                f.write('Current = %s\n' % obj.lasers[i].current)
    
    def onHelp(self, info):
        webbrowser.open(r'file:///' + os.path.split(sys.argv[0])[0]+ r'/Manual/index.html')
                
    def onSwitchLaser1(self, info):
        info.object.switchLaser(1)
        
    def onSwitchLaser2(self, info):
        info.object.switchLaser(2)
        
    def onSwitchLaser3(self, info):
        info.object.switchLaser(3)
    
class WLMStation(HasTraits):
    figure = Instance(pg.PlotItem, ())
    configPath = Str
    startScan = Button
    stopScan = Button
    startMeasureRT = Button
    stopMeasureRT = Button
    setLaser = Button
    readLaser = Button
    center1 = Float
    center2 = Float
    scale1 = Float
    scale2 = Float
    phase = Float
    etalon1Offset = Float(0.0)
    reference1Offset = Float(0.0)
    etalon2Offset = Float(0.0)
    reference2Offset = Float(0.0)
    onMeasurement = Int(0)  # 1: measure power; 2: measure RT; 3: scan ratio
    scanRatio1 = Bool(True)
    scanRatio2 = Bool(True)
    displayRT = Enum(0, 1)
    ratio1Max = Float
    ratio1Min = Float
    ratio2Max = Float
    ratio2Min = Float
    reflectance1 = Float
    reflectance2 = Float
    transmittance1 = Float
    transmittance2 = Float
    reflectance2 = Float
    transmittance1 = Float
    transmittance2 = Float
    laserTemperature = Float
    laserCurrent = Float
    laserOn = Bool(False)
    measurementNote = Str
    # parameters
    lasers = List(Laser)
    channelForEtalon1 = Int
    channelForReference1 = Int
    channelForEtalon2 = Int
    channelForReference2 = Int
    etalon1Gain = Float
    etalon2Gain = Float
    reference1Gain = Float
    reference2Gain = Float
    sampleRate = Int
    sampleTime = Float
    monitorRate = Int
    monitorTimeSpan = Int
    
    def __init__(self, *a, **k):
        super(WLMStation, self).__init__(*a, **k)
        self.allChannel = [i for i in range(8)]
        if os.path.exists(self.configPath):
            self.config = CustomConfigObj(self.configPath)
            self.fileDir = self.config.get('Main', 'FileDir')
            self.totalLaserNum = self.config.getint('Main', 'Laser_Num')
            self.coarseCurrentConvertor = self.config.getfloat('Main', 'Laser_Coarse_Current_Convertor')
            self.fineCurrentConvertor = self.config.getfloat('Main', 'Laser_Fine_Current_Convertor')
            self.laserCurrentOffset = self.config.getfloat('Main', 'Laser_Current_Offset')
            self.channelForEtalon1 = self.config.getint('Acquisition', 'Channel_Etalon1')
            self.channelForEtalon2 = self.config.getint('Acquisition', 'Channel_Etalon2')
            self.channelForReference1 = self.config.getint('Acquisition', 'Channel_Reference1')
            self.channelForReference2 = self.config.getint('Acquisition', 'Channel_Reference2')
            self.channelForPowerMeter= self.config.getint('Acquisition', 'Channel_PowerMeter')
            self.etalon1Gain = self.config.getfloat('Acquisition', 'Etalon1_Gain')
            self.etalon2Gain = self.config.getfloat('Acquisition', 'Etalon2_Gain')
            self.reference1Gain = self.config.getfloat('Acquisition', 'Reference1_Gain')
            self.reference2Gain = self.config.getfloat('Acquisition', 'Reference2_Gain')
            self.WLM_channels = "Dev1/ai%d,Dev1/ai%d,Dev1/ai%d,Dev1/ai%d" % (self.channelForReference1, self.channelForReference2, \
                                self.channelForEtalon1, self.channelForEtalon2)
            self.sampleRate = self.config.getint('Sampling', 'Sample_Rate')
            self.sampleTime = self.config.getfloat('Sampling', 'Sample_Time')
            self.monitorRate = self.config.getint('Sampling', 'Monitor_Rate')
            self.monitorTimeSpan = self.config.getint('Sampling', 'Monitor_Time_Span')
            for i in range(1, self.totalLaserNum+1):
                laserIndex = self.config.getint('Laser%d' % i, 'Laser_Index')
                maxSweepValue = self.config.getfloat('Laser%d' % i, 'Max_Sweep_Value')
                minSweepValue = self.config.getfloat('Laser%d' % i, 'Min_Sweep_Value')
                sweepSpeed = self.config.getfloat('Laser%d' % i, 'Sweep_Speed')
                fullScanTime = self.config.getfloat('Laser%d' % i, 'Full_Scan_Time')
                fitDataNum = self.config.getint('Laser%d' % i, 'Fit_DataSet_Num')
                temperature = self.config.getfloat('Laser%d' % i, 'Temperature')
                current = self.config.getint('Laser%d' % i, 'Current')
                self.lasers.append(Laser(laserIndex=laserIndex, maxSweepValue=maxSweepValue, minSweepValue=minSweepValue,
                                         sweepSpeed=sweepSpeed, fullScanTime=fullScanTime, fitDataNum=fitDataNum, 
                                         temperature=temperature, current=current))
        # Menu
        newUnit = Action(name="New WLM unit\tCtrl+N", accelerator='Ctrl+N', action="onNewUnit")
        setConfig = Action(name="Configuration", action="onSetConfig", enabled_when='not onMeasurement')
        saveConfig = Action(name="Save configuration", action="onSaveConfig", enabled_when='not onMeasurement')
        measureOffset = Action(name="Measure dark currents", action="onMeasureOffset", enabled_when='not onMeasurement')
        loadOffset = Action(name="Load dark current settings", action="onLoadOffset")
        takeScreenshot = Action(name="Take screenshot\tF6", accelerator='F6', action="onTakeScreenshot")
        help = Action(name="Help\tF1", accelerator='F1', action="onHelp")
        switchLaser = []
        for i in range(1, self.totalLaserNum+1): 
            switchLaser.append( Action(name="Laser %d" % i, action="onSwitchLaser%d" % i, style="radio", \
                                       enabled_when='not onMeasurement', checked=True if i==1 else False) )
        
        self.view = View(VGroup(Item(label=' '),
                       HGroup(Item(label=' '*3),
                              Item('figure', editor=QtGraphEditor(), show_label=False),
                              Item(label=' '*3)),
                       Item(label=' '),
                       HGroup(
                            Item(label=' '*3),
                            HGroup(
                                Group(
                                    HGroup(Item(label=' '*5),
                                        HGroup(
                                            Item('startMeasureRT', label='Start', show_label=False, enabled_when='not onMeasurement'),
                                            Item('stopMeasureRT', label='Stop', show_label=False, enabled_when='onMeasurement==2'),
                                            label='Measurement', show_border=True),
                                        Item(label=' '*5),
                                        VGroup(
                                            Item('displayRT', editor=EnumEditor(values={0:'T1 (blue) R1 (red)', 1:'T2 (blue) R2 (red)'}), 
                                                show_label=False, style='custom', enabled_when='not onMeasurement'),
                                            label='Display', show_border=True)
                                        ),
                                    HGroup(Item(label=' '*5),
                                        Group(Item('reflectance1', label='R1', width=-60, format_str='%.3f'),
                                            Item('transmittance1', label='T1', width=-60, format_str='%.3f'),
                                            Item('reflectance2', label='R2', width=-60, format_str='%.3f'),
                                            Item('transmittance2', label='T2', width=-60, format_str='%.3f'),
                                            columns=2, show_border=True, label=u'Reflectance and transmittance signals (\u03bcA)'
                                            ),
                                        Item(label=' '*5)),
                                    HGroup(Item(label=' '*5),
                                        VGroup(
                                            HGroup(Item('laserTemperature', label=u'Temperature (C)', width=-60, format_str='%.3f'),
                                            Item('laserCurrent', label='Current (mA)', width=-60, format_str='%.3f')),
                                            HGroup(Item('setLaser', label='Set', show_label=False),
                                            Item('readLaser', label='Read', show_label=False),
                                            Item('laserOn')),
                                            show_border=True, label='Laser settings'
                                            ),
                                        Item(label=' '*5)),
                                    label='Monitor', show_border=True, enabled_when='onMeasurement==2 or onMeasurement==0'),
                                Group(
                                    HGroup(Item(label=' '*5),
                                        HGroup(
                                            Item('startScan', label='Start', show_label=False, enabled_when='not onMeasurement'),
                                            Item('stopScan', label='Stop', show_label=False, enabled_when='onMeasurement==3'),
                                            label='Scan', show_border=True),
                                        Item(label=' '*2),
                                        Group(Item('scanRatio1', label='Ratio 1 (blue)', enabled_when='not onMeasurement'),
                                            Item('scanRatio2', label='Ratio 2 (red)', enabled_when='not onMeasurement'),
                                            show_border=True, label='Display')
                                        ),
                                    HGroup(Item(label=' '*5),
                                        Group(Item('center1', label='Center 1', width=-60, format_str='%.3f'),
                                            Item('center2', label='Center 2', width=-60, format_str='%.3f'),
                                            Item('scale1', label='Scale 1', width=-60, format_str='%.3f'),
                                            Item('scale2', label='Scale 2', width=-60, format_str='%.3f'),
                                            Item('phase', emphasized=True, width=-60, format_str='%.1f'),
                                            columns=2, show_border=True, label='Ellipse'
                                                ),
                                        Item(label=' '*5)),
                                    HGroup(Item(label=' '*5),
                                        Group(Item('ratio1Min', label='Ratio1 Min', width=-60, format_str='%.3f'),
                                            Item('ratio1Max', label='Ratio1 Max', width=-60, format_str='%.3f'),
                                            Item('ratio2Min', label='Ratio2 Min', width=-60, format_str='%.3f'),
                                            Item('ratio2Max', label='Ratio2 Max', width=-60, format_str='%.3f'),
                                            columns=2, show_border=True, label='Ratio'),
                                        Item(label=' '*5)),
                                    label='Scan', show_border=True, enabled_when='onMeasurement==3 or onMeasurement==0'),
                                ),
                            Item(label=' '*3)
                            ),
                       HGroup(Item(label=' '*5),
                            Item('measurementNote', label='Note', style='custom', width=600, height=-25),
                            Item(label=' '*5)),
                       Item(label=' ')    
                       ),
                menubar=MenuBar(Menu(newUnit, loadOffset, takeScreenshot, saveConfig, name='&File'),
                                Menu(setConfig, measureOffset, Separator(), *switchLaser, name='&Action'),
                                Menu(help, name='&Help')),
                resizable=True, handler=WLMStationHandler(), title='Picarro WLMStation')
        self.edit_view = View(
                            VGroup(
                                Item(label=' '),
                                HGroup( Item(label=' '*5),
                                        Group(Item('channelForReference1', editor=EnumEditor(name="allChannel")),
                                             Item('channelForReference2', editor=EnumEditor(name="allChannel")),
                                             Item('channelForEtalon1', editor=EnumEditor(name="allChannel")),
                                             Item('channelForEtalon2', editor=EnumEditor(name="allChannel")),
                                             Item('channelForPowerMeter', editor=EnumEditor(name="allChannel")),
                                             columns=2, show_border=True, label='ADC Channels'),
                                        Item(label=' '*5)),
                                Item(label=' '),
                                HGroup( Item(label=' '*5),
                                        Group(Item('sampleRate', tooltip='samples taken per second in scan'),
                                             Item('sampleTime', tooltip='time for a sampling period'),
                                             Item('monitorRate', tooltip='samples taken per second in monitoring'),
                                             Item('monitorTimeSpan', tooltip='time span of monitor window'),
                                             columns=2, show_border=True, label='Sampling'),
                                        Item(label=' '*5)),
                                Item(label=' '),
                                HGroup( Item(label=' '*5),
                                        Group(
                                            Item('lasers', show_label=False, editor=TableEditor(
                                                columns = [ ObjectColumn(name = 'laserIndex' ),
                                                            ObjectColumn(name = 'maxSweepValue' ),
                                                            ObjectColumn(name = 'minSweepValue' ),
                                                            ObjectColumn(name = 'sweepSpeed' ),
                                                            ObjectColumn(name = 'fullScanTime' ),
                                                            ObjectColumn(name = 'fitDataNum' )],
                                                orientation = 'vertical',
                                                row_factory = Laser )),
                                            show_border=True, label='Lasers'),
                                        Item(label=' '*5)),
                                Item(label=' ')        
                                ),
                            buttons=OKCancelButtons, resizable=False, kind="livemodal", title="Configuration")

        self.niInput = None
        self.unitName = None
        self.laserNum = None
        self.switchLaser(1)
        self.dataQueue = Queue.Queue()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
                        
        self.plot1 = self.figure.plot(pen=pg.mkPen(color=(0, 0, 255), width=3))
        self.plot2 = self.figure.plot(pen=pg.mkPen(color=(255, 0, 0), width=3))
        self.figure.showGrid(x=True, y=True)
        self.figure.setRange(xRange=[0,self.fullScanTime])
        self.figure.setLabels(title="WLM Station",left="Ratio")
        self.figure.getAxis("bottom").setLabel('Time', units='second')
        
        if not os.path.isdir(self.fileDir):
            os.makedirs(self.fileDir)
    
    def emptyDataQueue(self):
        while True:
            try:
                self.dataQueue.get(block=False)
            except Queue.Empty:
                break
                
    def switchLaser(self, laserIndex):
        if self.laserNum is not None:
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % self.laserNum, TEMP_CNTRL_EnabledState)
        laser = self.lasers[laserIndex - 1]
        index = laser.laserIndex
        maxSweepValue = laser.maxSweepValue
        minSweepValue = laser.minSweepValue
        sweepSpeed = laser.sweepSpeed
        self.fullScanTime = laser.fullScanTime
        self.fitDataNum = laser.fitDataNum
        self.laserTemperature = laser.temperature
        self.laserCurrent = laser.current
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_MIN_REGISTER" % index, minSweepValue)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_MAX_REGISTER" % index, maxSweepValue)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_H_REGISTER" % index, 0.2)   # sample interval 0.2 sec
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_INCR_REGISTER" % index, sweepSpeed*0.2)
        self.laserNum = index
        self._setLaser_fired()
    
    def _laserOn_changed(self):
        if self.laserNum is not None:
            if self.laserOn:
                turnOnLaser(self.laserNum)
            else:
                turnOffLaser(self.laserNum)
    
    def readLaserCurrent(self):
        coarse = Driver.rdDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.laserNum)
        fine = Driver.rdDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.laserNum)
        return coarse * self.coarseCurrentConvertor / 1e4 + fine * self.fineCurrentConvertor / 1e4 + self.laserCurrentOffset
        
    def _setLaser_fired(self):
        self.laserOn = True
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % self.laserNum, TEMP_CNTRL_EnabledState)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum, self.laserTemperature)
        if self.laserCurrent < self.laserCurrentOffset:
            error(message = "Laser current is set too low!", title = 'Error', buttons = ['OK'])
            self.laserCurrent = self.readLaserCurrent()
        elif self.laserCurrent > 170:
            error(message = "Laser current is set too high!", title = 'Error', buttons = ['OK'])
            self.laserCurrent = self.readLaserCurrent()
        else:
            coarse = (self.laserCurrent - self.laserCurrentOffset) / self.coarseCurrentConvertor * 1e4
            fine = (coarse % 1) * self.coarseCurrentConvertor / self.fineCurrentConvertor
            Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.laserNum, int(coarse))
            Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.laserNum, fine)
        
    def _readLaser_fired(self):
        self.laserTemperature = Driver.rdDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum)
        self.laserCurrent = self.readLaserCurrent()
        
    def _startMeasureRT_fired(self):
        if not self.etalon1Offset and not self.etalon2Offset \
           and not self.reference1Offset and not self.reference2Offset:
            msg = '\n'+' '*5+'Please measure dark current before scanning ratio!'+' '*5+'\n'
            error(message = msg, title = 'Error', buttons = ['OK'])
            return 
        self.laserOn = True
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % self.laserNum, TEMP_CNTRL_EnabledState)
        self.dataNum = 1
        self.totalDataNum = int(self.monitorTimeSpan * self.monitorRate)
        self.time_array = np.array([float(x)/self.monitorRate for x in range(self.totalDataNum)])
        self.data1_array = np.empty(self.totalDataNum)
        self.data1_array[:] = np.NAN
        self.data2_array = np.empty(self.totalDataNum)
        self.data2_array[:] = np.NAN
        self.time_index = 0
        self.emptyDataQueue()
        self.plot1.setData(self.time_array, self.data1_array)
        self.plot2.setData(self.time_array, self.data2_array)
        self.figure.setRange(xRange=[0,self.monitorTimeSpan])
        self.figure.setLabels(left="Signal (V)")
        self.niInput = daq.Task()
        self.niInput.CreateAIVoltageChan(self.WLM_channels, "", daq.DAQmx_Val_Cfg_Default, -10.0, 10.0, daq.DAQmx_Val_Volts, None)
        self.niInput.CfgSampClkTiming("", self.monitorRate, daq.DAQmx_Val_Rising, daq.DAQmx_Val_ContSamps, 1)  
        self.onMeasurement = 2
        d = threading.Thread(target = self.getNiData)
        d.setDaemon(True)
        d.start()
        self.timer.start(20)    # interval = 20 ms
        
    def _stopMeasureRT_fired(self):
        self.onMeasurement = 0
        self.timer.stop()
                
    def _startScan_fired(self):
        if not self.etalon1Offset and not self.etalon2Offset \
           and not self.reference1Offset and not self.reference2Offset:
            msg = '\n'+' '*5+'Please measure dark current before scanning ratio!'+' '*5+'\n'
            error(message = msg, title = 'Error', buttons = ['OK'])
            return 
        self.laserOn = True
        self.center1, self.center2 = 0, 0
        self.scale1, self.scale2 = 0, 0
        self.phase = -9999
        self.ratio1Max, self.ratio1Min = 0, 0
        self.ratio2Max, self.ratio2Min = 0, 0
        self.vector = None
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % self.laserNum, TEMP_CNTRL_SweepingState)
        self.dataNum = int(self.sampleRate * self.sampleTime)
        self.totalDataNum = int(self.sampleRate * self.fullScanTime)
        self.ratio1_deque = deque(maxlen=self.dataNum * self.fitDataNum)
        self.ratio2_deque = deque(maxlen=self.dataNum * self.fitDataNum)
        self.time_index = 0
        self.time_array = np.array([float(x)/self.sampleRate for x in range(self.totalDataNum)])
        self.data1_array = np.empty(self.totalDataNum)
        self.data1_array[:] = np.NAN
        self.data2_array = np.empty(self.totalDataNum)
        self.data2_array[:] = np.NAN
        self.emptyDataQueue()
        self.niInput = daq.Task()
        self.niInput.CreateAIVoltageChan(self.WLM_channels, "", daq.DAQmx_Val_Cfg_Default, -10.0, 10.0, daq.DAQmx_Val_Volts, None)
        self.niInput.CfgSampClkTiming("", self.sampleRate, daq.DAQmx_Val_Rising, daq.DAQmx_Val_ContSamps, self.dataNum)
        self.onMeasurement = 3
        self.plot1.setData(self.time_array, self.data1_array)
        self.plot2.setData(self.time_array, self.data2_array)
        self.figure.setRange(xRange=[0, self.fullScanTime])
        self.figure.setLabels(left="Ratio")
        d = threading.Thread(target = self.getNiData)
        d.setDaemon(True)
        d.start()
        self.timer.start(20)    # interval = 20 ms
        
    def _stopScan_fired(self):
        self.onMeasurement = 0
        self.timer.stop()
    
    def update(self):
        try:
            while True:
                data = self.dataQueue.get(block=False)
                if self.onMeasurement == 3:
                    startP = self.time_index * self.dataNum
                    endP = startP + self.dataNum
                    if self.scanRatio1:
                        ref1 = data[:self.dataNum] - self.reference1Offset
                        eta1 = data[2*self.dataNum : 3*self.dataNum] - self.etalon1Offset
                        r1 = ref1/eta1
                        self.data1_array[startP : endP] = r1
                        self.ratio1Max = np.max(self.data1_array)
                        self.ratio1Min = np.min(self.data1_array)
                    if self.scanRatio2:    
                        ref2 = data[self.dataNum : 2*self.dataNum] - self.reference2Offset
                        eta2 = data[3*self.dataNum : 4*self.dataNum] - self.etalon2Offset
                        r2 = ref2/eta2
                        self.data2_array[startP : endP] = r2
                        self.ratio2Max = np.max(self.data2_array)
                        self.ratio2Min = np.min(self.data2_array)
                    self.time_index += 1
                    if self.time_index >= self.fullScanTime / self.sampleTime:
                        self.time_index = 0
                    if self.scanRatio1 and self.scanRatio2:
                        for i in range(self.dataNum):
                            self.ratio1_deque.append(r1[i])
                            self.ratio2_deque.append(r2[i])
                        self.center1, self.center2, self.scale1, self.scale2, phi = \
                                WlmCalUtilities.parametricEllipse(self.ratio1_deque, self.ratio2_deque)
                        # scale = 1.05 / min(self.scale1, self.scale2)
                        # self.scale1norm = scale * self.scale1
                        # self.scale2norm = scale * self.scale2
                        self.phase = phi * 180 / np.pi
                        newVector = [np.mean(r1)-self.center1, np.mean(r2)-self.center2]
                        if self.vector is not None:
                            if (self.vector[0]*newVector[1] - self.vector[1]*newVector[0]) < 0:
                                self.phase = 180 - self.phase if self.phase>=0 else -180-self.phase
                        self.vector = newVector
                            
                elif self.onMeasurement == 2:
                    self.transmittance1 = (data[2] - self.etalon1Offset) / self.etalon1Gain * 1e6   # Etalon1
                    self.transmittance2 = (data[3] - self.etalon2Offset) / self.etalon2Gain * 1e6   # Etalon2
                    self.reflectance1 = (data[0] - self.reference1Offset) / self.reference1Gain * 1e6    # Reference1
                    self.reflectance2 = (data[1] - self.reference2Offset) / self.reference2Gain * 1e6    # Reference2
                    displayValue = (self.transmittance2, self.reflectance2) if self.displayRT else (self.transmittance1, self.reflectance1)
                    if self.time_index < self.totalDataNum - 1:
                        self.data1_array[self.time_index] = displayValue[0]
                        self.data2_array[self.time_index] = displayValue[1]
                        self.time_index += 1
                    else:
                        self.data1_array = np.roll(self.data1_array, -1)
                        self.data2_array = np.roll(self.data2_array, -1)
                        self.data1_array[self.time_index] = displayValue[0]
                        self.data2_array[self.time_index] = displayValue[1]
                self.plot1.setData(self.time_array, self.data1_array)
                self.plot2.setData(self.time_array, self.data2_array)
        except Queue.Empty:
            pass
        
    def getNiData(self):
        read = daq.int32()
        bufferSize = len(self.WLM_channels.split(",")) * self.dataNum
        data = np.zeros(bufferSize, dtype=np.float64)
        self.niInput.StartTask()
        while self.onMeasurement:
            self.niInput.ReadAnalogF64(self.dataNum, 2, daq.DAQmx_Val_GroupByChannel, # timeout is set to 2 seconds
                                       data, bufferSize, daq.byref(read), None)
            self.dataQueue.put(data)
        self.niInput.StopTask()
        self.niInput = None
            
class progressBarHandler(Handler):
    def init(self, info):
        Handler.init(self, info)
        thread = threading.Thread(target = self.run, args=[info])
        thread.setDaemon(True)
        thread.start()

    def object_status_changed(self, info):
        if info.object.status == 100:
            info.ui.dispose()   # close ui in the main GUI thread otherwise program will crash randomly
    
    def run(self, info):
        obj = info.object
        while obj.object.progress < 100:
            obj.status = obj.object.progress
            obj.message = obj.object.message
            time.sleep(0.3)
        obj.status = 100            
            
class ProgressBar(HasTraits):
    title = CStr("")
    message = CStr("This is the program to measure dark current.")
    status = Int(0)
    traits_view = Instance(View)
    
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        self.traits_view = View(VGroup(Item(label=' '),
                                       HGroup(Item(label=' '), 
                                              Item('message', show_label=False, style="readonly"),
                                              Item(label=' ')),
                                       HGroup(Item(label=' '),       
                                              Item('status', show_label=False, 
                                                    editor=ProgressEditor(min=0, max=100, show_percent=True)),
                                              Item(label=' ')),
                                       Item(label=' ')
                                       ),
                               resizable=False, title=self.title, kind="livemodal", handler=progressBarHandler())
            
class Averager(object):
    # Averages non-None values added to it
    def __init__(self):
        self.total = 0
        self.count = 0
    def addValue(self,value):
        if value is not None:
            self.total += value
            self.count += 1
    def getAverage(self):
        if self.count != 0:
            return self.total/self.count
        else:
            raise ValueError,"No values to average"            
            
class getDarkCurrent():
    def __init__(self, WLM_channels, laserNum):
        self.WLM_channels = WLM_channels
        self.laserNum = laserNum
        self.niInput = daq.Task()
        self.niInput.CreateAIVoltageChan(self.WLM_channels, "", daq.DAQmx_Val_Cfg_Default, -10.0, 10.0, daq.DAQmx_Val_Volts, None)
        #self.niInput.CfgSampClkTiming("", SAMPLE_RATE, daq.DAQmx_Val_Rising, daq.DAQmx_Val_FiniteSamps, 1)
        self.progress = 0
        self.message = ""
        self.etalon1_offset = 0
        self.reference1_offset = 0
        self.etalon2_offset = 0
        self.reference2_offset = 0
        
    def run(self):
        self.message = "Turning off laser..."
        if not turnOffLaser(self.laserNum):
            return
        time.sleep(2)
        self.progress = 10
        
        tDuration = 5
        self.message = "Measuring WLM offsets for %.1f seconds" % tDuration 
        etalon1Avg = Averager()
        reference1Avg = Averager()
        etalon2Avg = Averager()
        reference2Avg = Averager()
        
        read = daq.int32()
        bufferSize = len(self.WLM_channels.split(","))
        data = np.zeros(bufferSize, dtype=np.float64)
        tStart = time.time()
        t = tStart
        while t < tStart + tDuration:
            self.niInput.StartTask()
            self.niInput.ReadAnalogF64(1, 1.0, daq.DAQmx_Val_GroupByChannel,
                                       data, bufferSize, daq.byref(read), None)
            self.niInput.StopTask()
            reference1Avg.addValue(data[0])
            reference2Avg.addValue(data[1])
            etalon1Avg.addValue(data[2])
            etalon2Avg.addValue(data[3])
            t = time.time()
            self.progress = int((t - tStart) * 80 / tDuration + 10)
        self.message = "Turning laser back on..."
        turnOnLaser(self.laserNum)
        
        self.etalon1_offset = etalon1Avg.getAverage()
        self.reference1_offset = reference1Avg.getAverage()
        self.etalon2_offset = etalon2Avg.getAverage()
        self.reference2_offset = reference2Avg.getAverage()
        self.progress = 100
        
def turnOffLaser(laserNum):
    Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",SPECT_CNTRL_IdleState)
    i = 0
    while True:
        Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % laserNum, LASER_CURRENT_CNTRL_DisabledState)
        time.sleep(0.5)
        if Driver.rdDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % laserNum) != LASER_CURRENT_CNTRL_DisabledState:
            if i > 10:
                error(message="Analyzer error: fail to turn off laser!", title = 'Error', buttons = ['OK'])
                return False
            i += 1
        else:
            return True
            
def turnOnLaser(laserNum):
    Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % laserNum, LASER_CURRENT_CNTRL_ManualState)
    time.sleep(0.5)

if __name__ == "__main__": 
    config = "WLMStation.ini"
    ws = WLMStation(configPath=config)
    ws.configure_traits(view=ws.view)