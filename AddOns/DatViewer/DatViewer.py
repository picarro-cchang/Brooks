#!/usr/bin/python
#
# File Name: DatViewer.py
# Purpose: DatViewer is a standalone program to import and display Picarro data files,
#          and to also concatenate and convert their formats.
#
# Notes:
#
# File History:
# 2013-09-04 tw  Added file to repository, PEP-8 formatting.
# 2013-09-10 tw  Added open .zip archive to menu, rearranged File menu, final PEP-8 formatting.
# 2013-09-16 tw  UI cleanup: added menu shortcuts and accelerators, flattened time series cascade menu,
#                select folder dialog requires dir to exist.
# 2013-10-25 sze Used scaled x-axis for calculation of line of best fit in correlation plot to avoid roundoff
#                errors giving incorrect fits when the number of data points is large
# 2013-10-27 sze Fixes for matplotlib-1.3. Correct handling of double-click for Windows 7
# 2013-12-18 tw  Added spectrum ID dropdown to Allan std. dev. window (empty first choice=no filtering),
#                display appname and version in main window frame title
# 2013-12-20 tw  v2.0.2: Removed prefs file code (unneeded experimental code, crashed WinXP)
# 2013-12-23 tw  v2.0.3: Fixed bugs in spectrum ID filtering for Allan std. dev.
# 2014-02-13 tw  v2.0.4: Concatenate Folder to H5 menu option uses new function (asks user for folder first then filename).
# 2015-12-01 yuan v3.0.0: Rewrote large portion of the program. Added many new features.
# 2016-01-13 yuan v3.0.1: Plot multiple Allan std. dev. data in one figure; Add screenshot menu to XYPlot

import wx
import gettext
import sys
import os
import time
from datetime import datetime
import dateutil 
import pytz
import tzlocal
import threading
import traceback
import tables
import zipfile
import tempfile
import webbrowser
from numpy import *
from scipy.signal import lfilter
from scipy.optimize import curve_fit
import matplotlib as mpl
mpl.use('WXAgg')
mpl.rc('font', family='Arial')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from pandas import DataFrame

# HasTraits, Float, Bool, Int, Long, Str
from traits.api import *
from traitsui.api import *
from traitsui.wx.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.menu import *

from CustomConfigObj import CustomConfigObj
from timestamp import unixTime, datenumToUnixTime, datetimeTzToUnixTime, unixTimeToTimestamp
from DateRangeSelectorFrame import DateRangeSelectorFrame
from FileOperations import *
from Analysis import *

FULLAPPNAME = "Picarro Data File Viewer"
APPNAME = "DatViewer"
APPVERSION = "3.0.2"

Program_Path = os.path.split(sys.argv[0])[0]
# cursors
class Cursors:  # namespace
    HAND, POINTER, SELECT_REGION, MOVE, MAGNIFIER = range(5)
cursors = Cursors()
# Dictionary for mapping cursor names to wx cursor names
cursord = {
    cursors.MOVE: wx.CURSOR_HAND,
    cursors.HAND: wx.CURSOR_HAND,
    cursors.POINTER: wx.CURSOR_ARROW,
    cursors.SELECT_REGION: wx.CURSOR_CROSS,
    cursors.MAGNIFIER: wx.CURSOR_MAGNIFIER}

linestyle2Command = {'Solid': '-',
                     'Dashed': '--',
                     'Dash dot': '-.',
                     'Dotted': ':',
                     'None': 'None'}                         

marker2Command = {'None': 'None',
                 'Point': '.',
                 'Pixel': ',',
                 'Circle': 'o',
                 'Star': '*',
                 'Square': 's'}
                     
def DisplayMode2Multiplier(displayMode):
    if displayMode == 'Minute':
        return 1440.0
    elif displayMode == 'Hour':
        return 24.0                    

def SaveFigureProperty(figureHandle, axesHandle):
    fig, ax = figureHandle, axesHandle
    line = ax.get_lines()[0]
    displayMode = fig.displayMode
    if displayMode != "XY":
        tz, offset = fig.tz, fig.offset
    else:
        tz, offset = None, None
    return Bunch(displayMode=displayMode, tz=tz, offset=offset,
                 xlim=ax.get_xlim(), ylim=ax.get_ylim(), title=ax.get_title(),
                 xlabel=ax.get_xlabel(), ylabel=ax.get_ylabel(),
                 marker=line.get_marker(), linestyle=line.get_linestyle())
                 
def SetFigureProperty(figureHandle, axesHandle, properties):
    fig, ax, b = figureHandle, axesHandle, properties
    fig.displayMode = b.displayMode
    if b.displayMode == "DateTime":
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%H:%M:%S\n%Y/%m/%d', b.tz))
    if b.displayMode != "XY":
        fig.tz = b.tz
        fig.offset = b.offset
    ax.set_title(b.title)
    ax.set_xlabel(b.xlabel)
    ax.set_ylabel(b.ylabel)
    if b.xlim is not None:
        ax.set_xlim(b.xlim)
    if b.ylim is not None:
        ax.set_ylim(b.ylim)
    line = ax.get_lines()[0]
    line.set_linestyle(b.linestyle)
    line.set_marker(b.marker)
    fig.canvas.draw()
        
def SaveConfigFile(obj, XYPlot=False):
    def saveFigureConfig(figureHandle, axesHandle, fileHandle, featureCapture):
        b = SaveFigureProperty(figureHandle, axesHandle)
        f, fc = fileHandle, featureCapture
        f.write("displayMode = %s\n" % b.displayMode)
        if b.displayMode != "XY":
            f.write("tz = %s\n" % b.tz)
            f.write("offset = %s\n" % str(b.offset))
        f.write("title = %s\n" % b.title)
        if fc.xRange:
            f.write("xlim = %f, %f\n" % b.xlim)
        if fc.yRange:
            f.write("yLim = %f, %f\n" % b.ylim) 
        f.write("xlabel = %s\n" % b.xlabel)
        f.write("ylabel = %s\n" % b.ylabel)
        f.write("linestyle = %s\n" % b.linestyle)
        f.write("marker = %s\n" % b.marker)
        
    fc = FeatureCapturePanel()
    fc.configure_traits()
    fd = wx.FileDialog(None, "Configuration filename",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR,
                       defaultFile="UnNamed.ini",
                       defaultDir="",
                       wildcard="Config files (*.ini)|*.ini")
    if fd.ShowModal() == wx.ID_OK:
        fname = fd.GetPath()
    else:
        fd.Destroy()
        return
    fd.Destroy()
    with open(fname, "w") as f:
        f.write("[Main]\n")
        window = obj.parent if XYPlot else obj
        viewers = window.viewers
        if fc.dataFile:
            f.write("Data = %s\n" % window.dataFile)
        if len(window.filter) > 0 and fc.filter:
                f.write("Filter = %s\n" % window.filter)
        f.write("Viewer = %d\n" % len(viewers))
        for i, fr in enumerate(viewers):
            f.write("[Viewer%d]\n" % i)
            if fr.dataSetName:
                f.write("dataSetName = %s\n" % fr.dataSetName)
            if fr.varName:
                f.write("varName = %s\n" % fr.varName)
            f.write("Expression = %s\n" % (fr.expression if fc.expression else "y"))
            
            f.write("[Figure%d]\n" % i)
            saveFigureConfig(fr.plot.plot2dFigure, fr.plot.axes, f, fc)
            
        if XYPlot:
            f.write("[XYPlot]\n")
            variables = obj.dataInfo.split(';')
            f.write("x_Variable = %d\n" % int(variables[0]))
            f.write("y_Variable = %d\n" % int(variables[1]))
            f.write("[Figure_XYPlot]\n")
            saveFigureConfig(obj.plot.plot2dFigure, obj.plot.axes, f, fc)

# Decorator to protect access to matplotlib figure from several threads
#  self.lock should be a recursive lock
def checkLock(func):
    def wrapper(self, *a, **k):
        try:
            self.lock.acquire()
            return func(self, *a, **k)
        finally:
            self.lock.release()
    return wrapper            
            
class FeatureCapturePanelHandler(Handler):
    def show_help(self, info, control=None):
        webbrowser.open(r'file:///' + Program_Path + r'/Manual/time_series_plot_menu.html#save-configuration')  
            
class FeatureCapturePanel(HasTraits):
    Information = CStr("Select features that will be captured in the configuration file.")
    dataFile = Bool(True)
    filter = Bool(True)
    expression = Bool(True)
    xRange = Bool(True)
    yRange = Bool(True)
    traits_view = View(VGroup(Item("Information", show_label=False, style="readonly", padding=5),
                              HGroup(Item("dataFile"), Item("filter"), Item("expression")),
                              HGroup(Item("xRange"), Item("yRange"), show_border=True, label="Figure Property"),
                              ), buttons=[OKButton, HelpButton], kind="modal", title="Feature Capture", handler=FeatureCapturePanelHandler())
            
class DateRangeSelector(DateRangeSelectorFrame):                        
    def __init__(self, *args, **kwds):
        DateRangeSelectorFrame.__init__(self, *args, **kwds)
        self.StartTimeCtrl.BindSpinButton(self.spin_start)
        self.EndTimeCtrl.BindSpinButton(self.spin_end)
        self.choiceTimeZone.AppendItems(pytz.all_timezones)
        i = self.choiceTimeZone.FindString(str(tzlocal.get_localzone()))
        self.choiceTimeZone.SetSelection(i)
        self.dateRange = None
        
    def OnStartDateChanged(self, event):
        startTime = self.StartDatePicker.GetValue()
        if startTime.IsLaterThan(wx.DateTime.Now()):
            self.StartDatePicker.SetValue(wx.DateTime.Now())
                    
    def OnEndDateChanged(self, event):
        endTime = self.EndDatePicker.GetValue()
        if endTime.IsLaterThan(wx.DateTime.Now()):
            self.EndDatePicker.SetValue(wx.DateTime.Now())
    
    def _GetTicks(self, wxTimeObject):
        return wxTimeObject.GetHour() * 3600 + wxTimeObject.GetMinute() * 60 + wxTimeObject.GetSecond()
    
    def OnOKClicked(self, event): 
        def wxDatetimeToUnixTime(wxDateTime, wxDateTime2, timezone):
            """Converts 2 wxpython DateTime with timezone to unix time
            timezone is a python datetime.tzinfo object"""
            d = wxDateTime  # get date from this object
            t = wxDateTime2 # get time from this object
            dt = datetime(d.GetYear(), d.GetMonth()+1, d.GetDay(),
                                   t.GetHour(), t.GetMinute(), t.GetSecond())
            return datetimeTzToUnixTime(dt, timezone)
            
        self.selectedTz = self.choiceTimeZone.GetString(self.choiceTimeZone.GetSelection())
        tz = pytz.timezone(self.selectedTz)
        
        selectedDate = self.StartDatePicker.GetValue()
        selectedTime = self.StartTimeCtrl.GetWxDateTime()
        startTime = wxDatetimeToUnixTime(selectedDate, selectedTime, tz)
        
        selectedDate = self.EndDatePicker.GetValue()
        selectedTime = self.EndTimeCtrl.GetWxDateTime()
        endTime = wxDatetimeToUnixTime(selectedDate, selectedTime, tz)
        self.dateRange = (startTime, endTime)
        self.Close()

    def OnCancelClicked(self, event):  
        self.Close()
        
class Variable ( HasTraits ):
    name  = Str( '<unknown>' )
    group  = Str( '<unknown>' )
    fileName = Str('<unknown>')

class DataGroup ( HasTraits ):
    name = Str( '<unknown>' )
    variables = List( Variable )
    fileName = Str('<unknown>')
    
class H5File ( HasTraits ):
    name        = Str( '<unknown>' )
    groups = List( DataGroup ) 
    def getGroup(self, name):
        for g in self.groups:
            if g:
                if g.name == name:
                    return g
        return None

class TreeEditHandler(Handler):
    def show_help(self, info, control=None):
        webbrowser.open(r'file:///' + Program_Path + r'/Manual/user_guide.html#concatenate-h5-files')  
       
class TreeEdit(HasTraits):
    h5FileName = Str
    h5Left = Instance(H5File)
    h5Right = Instance(H5File)
    node = Any
    move2Left = Button(label="<<")
    move2Right = Button(label=">>")
    moveAll2Right = Button(label="All >>")
    defineDateRange = Button
    largeDataset = Bool(False)
    selectedVar = Str
    selectedGroup = Str
    selectedFile = Str
    instruction = Str("""\
    Left panel lists avariable variables in the selected HDF5 files.
    Please select variables to be concatenated in the new file.
    Click button on the right to only concatenate files with specific date range.""")
    tree_editor = TreeEditor(
        nodes = [
            TreeNode( node_for  = [ H5File ],
                      auto_open = True,
                      children  = 'groups',
                      label     = 'name',
                      view      = View(),
                      menu      = Menu()),
            TreeNode( node_for  = [ DataGroup ],
                      auto_open = True,
                      children  = 'variables',
                      label     = 'name',
                      view      = View(),
                      menu      = Menu()),
            TreeNode( node_for  = [ Variable ],
                      label     = 'name',
                      view      = View(),
                      menu      = Menu())
        ], editable=False, selected = 'node'
    )
    
    traits_view = View(
               VGroup(
                   HGroup(Item("instruction", style = "readonly", show_label=False),
                          Item("defineDateRange", show_label=False, width=80)),
                   Group(Item("largeDataset", label="Large dataset. Click 'Help' to see details about this option."),
                         show_left=False, padding=5),
                   HGroup(
                       Item('h5Left', editor = tree_editor, resizable = True),
                       VGroup(Item('move2Right', show_label=False, width=30), 
                              Item('move2Left', show_label=False, width=30),
                              Item('moveAll2Right', show_label=False, width=30)),
                       Item('h5Right', editor = tree_editor, resizable = True),
                       show_labels = False)),
                title = 'Select Variables',
                buttons = [OKButton, CancelButton, HelpButton],
                resizable = True,
                width = 600,
                height = 500,
                kind = 'livemodal',
                handler=TreeEditHandler() )
    
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        
        h5 = tables.openFile(self.h5FileName)
        groupList = []
        for k in h5.walkNodes("/"):
            if isinstance(k, tables.Table):
                table = h5.getNode(k._v_pathname)
                varList = []
                for v in table.colnames:
                    varList.append(Variable(name=v, group=k._v_pathname, fileName=self.h5FileName))
                groupList.append(DataGroup(name=k._v_pathname, variables=varList, fileName=self.h5FileName))
        self.h5Left = H5File(name=self.h5FileName, groups=groupList)
        self.h5Right = H5File(name="New File", groups=[])
        h5.close()
    
    def _node_changed(self):
        if isinstance(self.node, Variable):
            self.selectedVar = self.node.name
            self.selectedGroup = self.node.group
            self.selectedFile = self.node.fileName
        elif isinstance(self.node, DataGroup):
            self.selectedGroup = self.node.name
            self.selectedFile = self.node.fileName
            self.selectedVar = ""
        elif isinstance(self.node, H5File):
            self.selectedFile = self.node.name
            self.selectedGroup = ""
            self.selectedVar = ""
            
    def _move2Right_fired(self):
        self._moveVariables(self.h5Left, self.h5Right)
        
    def _move2Left_fired(self):
        self._moveVariables(self.h5Right, self.h5Left)    
        
    def _moveAll2Right_fired(self):
        self.selectedFile = self.h5Left.name
        self.selectedGroup = ""
        self.selectedVar = ""
        self._moveVariables(self.h5Left, self.h5Right)    
            
    def _moveVariables(self, source, dest):
        if self.selectedFile == dest.name:
            return
        if len(self.selectedVar) > 0:   # a variable is selected
            g = source.getGroup(self.selectedGroup)
            g.variables = [v for v in g.variables if v.name != self.selectedVar]
            gr = dest.getGroup(self.selectedGroup)
            if gr is not None:
                gr.variables.append(Variable(name=self.selectedVar, group=self.selectedGroup, fileName=dest.name))
            else:
                varList = [Variable(name=self.selectedVar, group=self.selectedGroup, fileName=dest.name)]
                dest.groups.append(DataGroup(name=self.selectedGroup, variables=varList, fileName=dest.name))
        elif len(self.selectedGroup) > 0:   # a group is selected
            gl = source.getGroup(self.selectedGroup) 
            for v in gl.variables:
                v.fileName = dest.name
            gr = dest.getGroup(self.selectedGroup)
            if gr is None:
                dest.groups.append(gl)
            else:
                for v in gl.variables:
                    gr.variables.append(v)
            source.groups = [g for g in source.groups if g.name != self.selectedGroup]
        elif len(self.selectedFile) > 0:    # a file is selected
            for g in source.groups:
                for v in g.variables:
                        v.fileName = dest.name
                gr = dest.getGroup(g.name)
                if gr is None:
                    dest.groups.append(g)
                else:
                    for v in g.variables:
                        gr.variables.append(v)
            source.groups = []
        self.selectedVar = ""
        self.selectedGroup = ""
        self.selectedFile = ""
        
    def _defineDateRange_fired(self):
        ds = DateRangeSelector(None, wx.ID_ANY, "")
        ds.ShowModal()
        if ds.dateRange is not None:
            self.dateRange = ds.dateRange
            self.privateLog = ds.chkPrivateLog.GetValue()
            self.timeZone = ds.selectedTz
        ds.Destroy()
               
    def getSelectedDict(self):
        select = {}
        for g in self.h5Right.groups:
            if g:
                select[g.name] = []
                for v in g.variables:
                    select[g.name].append(v.name)
        if hasattr(self, "dateRange"):
            select["user_DateRange"] = self.dateRange
            select["user_PrivateLog"] = self.privateLog
            select["user_TimeZone"] = self.timeZone
        select["user_LargeDateset"] = self.largeDataset
        return select                        
                        
class Window(HasTraits):
    pass

class FigureStats(Window):
    statsInfo = Str(editor=TextEditor(multi_line=True))
    Variables = ListStr
    traits_view = Instance(View)
    def __init__(self, *a, **k):
        Window.__init__(self, *a, **k)
        self.statsInfo = ""
        for i, s in enumerate(self.stats):
            self.statsInfo += "[%s]\n" % self.Variables[i]
            self.statsInfo += "Average = %s\nStd dev = %s\nPeak to peak = %s\n" % (s.mean, s.std, s.ptp) if s is not None else "None\n"
                    
        self.traits_view = View(VGroup(Item("statsInfo", style='custom', width=400, show_label = False)), 
                                buttons=[OKButton], title="Statistics",
                                width=450, height=300, resizable=False, kind="modal")

class ImageEditorHandler(Handler):
    def onCancelClicked(self, info):
        info.ui.dispose()
        
    def onApplyClicked(self, info):
        obj = info.object
        try:
            a = obj.figure.gca()
            line = a.get_lines()[0]
            if obj.figure.displayMode == 'DateTime':
                tz = pytz.timezone(obj.timeZone)
                dt = datetime.strptime(obj.xMin, "%Y-%m-%d %H:%M:%S")
                xMin = mpl.dates.date2num(tz.localize(dt)) 
                dt = datetime.strptime(obj.xMax, "%Y-%m-%d %H:%M:%S")
                xMax = mpl.dates.date2num(tz.localize(dt)) 
                a.xaxis.set_major_formatter(mpl.dates.DateFormatter('%H:%M:%S\n%Y/%m/%d', tz))
                obj.figure.tz = tz
            else:
                xMin = float(obj.xMin)
                xMax = float(obj.xMax)
            a.set_xlim((xMin, xMax))
            a.set_xlabel(obj.xLabel)
            a.set_ylabel(obj.yLabel)
            a.set_ylim((obj.yMin, obj.yMax))
            a.set_title(obj.title)
            line.set_marker(marker2Command[obj.marker])
            line.set_linestyle(linestyle2Command[obj.line])
            obj.figure.canvas.draw()
            info.ui.dispose()
        except Exception, e:
            d = wx.MessageDialog(None, "%s" % e, str(Exception), style=wx.OK | wx.ICON_ERROR)
            d.ShowModal()
                                
class ImageEditor(Window):
    figure = Instance(Figure)
    xLabel = CStr(label="Label")
    yLabel = CStr(label="Label")
    xMin = CStr(label="Min")
    xMax = CStr(label="Max")
    yMin = CFloat(label="Min")
    yMax = CFloat(label="Max")
    title = CStr(label="Title")
    timeZone = CStr(label="Time zone")
    line = CStr(label="Line")
    marker = CStr(label="Marker")
    lineList = ListStr
    markerList = ListStr
    oldTimeZone = CStr
    tzList = ListStr
    setXmin2X0 = Button(label="x[0]", desc="first point of xData as xMin")
    traits_view = Instance(View)
                        
    def __init__(self, *a, **k):
        Window.__init__(self, *a, **k)
        
        a = self.figure.gca()
        line = a.get_lines()[0]
        xMin, xMax = a.get_xlim()
        self.yMin, self.yMax = a.get_ylim()
        self.xLabel = a.get_xlabel()
        self.yLabel = a.get_ylabel()
        self.title = a.get_title()
        self.marker = next(k for k, v in marker2Command.items() if v == line.get_marker())
        self.line = next(k for k, v in linestyle2Command.items() if v == line.get_linestyle())
        self.lineList = linestyle2Command.keys()
        self.markerList = marker2Command.keys()
        cancelButton = Action(name="Cancel", action="onCancelClicked")
        applyButton = Action(name="Apply", action="onApplyClicked")
        
        if self.figure.displayMode == 'DateTime':
            self.tzList = pytz.all_timezones
            self.timeZone = str(self.figure.tz)
            tzone = pytz.timezone(self.timeZone)
            self.oldTimeZone = self.timeZone
            self.xMin = mpl.dates.num2date(xMin, tz=tzone).strftime("%Y-%m-%d %H:%M:%S")
            self.xMax = mpl.dates.num2date(xMax, tz=tzone).strftime("%Y-%m-%d %H:%M:%S")
            self.traits_view = View(VGroup(
                                    HGroup(Item("title"), 
                                           Item("line", editor=EnumEditor(name="lineList")),
                                           Item("marker", editor=EnumEditor(name="markerList"))),
                                    VGroup(HGroup(Item("xMin", width=150), 
                                                  Item("setXmin2X0", width=-35, show_label=False),
                                                  Item("xMax", width=150)), 
                                           HGroup(Item("timeZone", editor=EnumEditor(name="tzList"))),
                                           HGroup(Item("xLabel")),
                                           label="x-Axis", show_border=True),
                                    HGroup(Item("yMin"), Item("yMax"), Item("yLabel"), label="y-Axis", show_border=True),
                                    ),
                                    buttons=[applyButton, cancelButton], title="Image Editor",
                                    width=460, height=300, resizable=False, kind="livemodal", handler=ImageEditorHandler())
        else:
            self.xMin = str(xMin)
            self.xMax = str(xMax)
            self.traits_view = View(VGroup(
                                    HGroup(Item("title"), 
                                           Item("line", editor=EnumEditor(name="lineList")),
                                           Item("marker", editor=EnumEditor(name="markerList"))),
                                    VGroup(HGroup(Item("xMin", width=150), Item("xMax", width=150)), 
                                           HGroup(Item("xLabel")), 
                                           label="x-Axis", show_border=True),
                                    HGroup(Item("yMin"), Item("yMax"), Item("yLabel"), label="y-Axis", show_border=True),
                                    ),
                                    buttons=[applyButton, cancelButton], title="Image Editor",
                                    width=460, height=300, resizable=False, kind="livemodal", handler=ImageEditorHandler())
        
    def _setXmin2X0_fired(self):
        a = self.figure.gca()
        line = a.get_lines()[0]
        xData = line.get_xdata()
        tzone = pytz.timezone(self.timeZone)
        self.xMin = mpl.dates.num2date(xData[0], tz=tzone).strftime("%Y-%m-%d %H:%M:%S")
    
    def _timeZone_changed(self):
        if self.xMin and self.xMax:
            try:
                tz = pytz.timezone(self.oldTimeZone)
                tz2 = pytz.timezone(self.timeZone)
                dt = datetime.strptime(self.xMin, "%Y-%m-%d %H:%M:%S")
                dt = tz.localize(dt)
                self.xMin = dt.astimezone(tz2).strftime("%Y-%m-%d %H:%M:%S")
                dt = datetime.strptime(self.xMax, "%Y-%m-%d %H:%M:%S")
                dt = tz.localize(dt)
                self.xMax = dt.astimezone(tz2).strftime("%Y-%m-%d %H:%M:%S")
            except Exception, e:
                d = wx.MessageDialog(None, "%s" % e, str(Exception), style=wx.OK | wx.ICON_ERROR)
                d.ShowModal()
        self.oldTimeZone = self.timeZone

class FigureInteraction(object):
    def __init__(self, fig, lock):
        self.fig = fig
        self.lock = lock
        self.canvas = fig.canvas
        w = self.canvas

        # Find the nearest top-level window
        while w and not w.IsTopLevel():
            w = w.GetParent()
        self.topLevel = {self.canvas: w}
        self.lastTime = 0
        self.lastButton = 0
        self._button_pressed = None
        self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)
        self._active = ""
        self._idle = True
        self._xypress = []
        self._lastCursor = None
        self.image_popup_menu = None
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('button_release_event', self.onRelease)
        self.canvas.mpl_connect('key_press_event', self.onKeyDown)
        self.canvas.mpl_connect('key_release_event', self.onKeyUp)
        self.canvas.mpl_connect('figure_enter_event', self.onEnterFigure)
        #self.canvas.mpl_connect('figure_leave_event', self.onLeaveFigure)
        #self.canvas.mpl_connect('axes_enter_event', self.onEnterAxes)
        #self.canvas.mpl_connect('axes_leave_event', self.onLeaveAxes)
        
        wx.EVT_RIGHT_DOWN(self.canvas, self.on_right_down)

        # Get all the subplots within the figure
        self.subplots = fig.axes
        self.autoscale = {}
        for s in self.subplots:
            self.autoscale[s] = True

    @checkLock
    def isActive(self):
        return self._active
        
    @checkLock
    def onEnterFigure(self, event):
        w = wx.Window.FindFocus()
        if w not in self.topLevel:
            p = w
            while p and not p.IsTopLevel():
                p = p.GetParent()
            self.topLevel[w] = p
        if self.topLevel[w] == self.topLevel[event.canvas]:
            event.canvas.SetFocus()
    
    @checkLock
    def onLeaveFigure(self, event):
        print "Leaving figure", event.canvas.figure

    @checkLock
    def onEnterAxes(self, event):
        print "Entering axes", event.inaxes

    @checkLock
    def onLeaveAxes(self, event):
        print "Leaving axes", event.inaxes

    @checkLock
    def onKeyDown(self, event):
        if self._active:
            return
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        elif event.key == "shift":
            self.setCursor(cursors.MOVE)

    @checkLock
    def onKeyUp(self, event):
        if self._active:
            return
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        elif event.key == "shift":
            self.setCursor(cursors.MAGNIFIER)
                
    def _append_menu_item(self, menu, wx_id, title, fxn):
        if wx_id is None:
            wx_id = wx.NewId()
        menu.Append(wx_id, title)
        wx.EVT_MENU(menu, wx_id, fxn)
    
    @checkLock
    def on_right_down(self, event):
        if self.fig.displayMode == "Histogram":
            return
        if self.image_popup_menu is None:
            menu = wx.Menu()
            self._append_menu_item(menu, None, "Export Image", self.saveImage)
            if "Allan Std Dev" in self.fig.viewer.traits_view.title:
                self._append_menu_item(menu, None, "Export Data", self.exportAllanStdDev)
            else:
                self._append_menu_item(menu, None, "Export Data in Current View", self.exportData)
            if self.fig.displayMode != "XY":
                self._append_menu_item(menu, None, "Export All Data in Current Time Range", self.exportDataAll)
            menu.AppendSeparator()
            self._append_menu_item(menu, None, "Edit Plot properties", self.editImage)
            menu.AppendSeparator()
            self._append_menu_item(menu, None, "Statistics", self.calStatistics)
            self.image_popup_menu = menu
        self.canvas.PopupMenuXY(self.image_popup_menu, event.X + 8,  event.Y + 8)

    @checkLock
    def draw(self):
        'redraw the canvases, update the locators'
        for a in self.fig.get_axes():
            xaxis = getattr(a, 'xaxis', None)
            yaxis = getattr(a, 'yaxis', None)
            locators = []
            if xaxis is not None:
                locators.append(xaxis.get_major_locator())
                locators.append(xaxis.get_minor_locator())
            if yaxis is not None:
                locators.append(yaxis.get_major_locator())
                locators.append(yaxis.get_minor_locator())

            for loc in locators:
                loc.refresh()
        self.canvas.draw()

    @checkLock
    def onRelease(self, event):
        # Get the axes within which the point falls
        if 'ZOOM' in self._active:
            self.release_zoom(event)
        elif self._active == "PAN" or self._active == "STRETCH":
            self.release_pan(event)
        self._active = ""

    @checkLock
    def release_zoom(self, event):
        if not self._xypress:
            return
        last_a = []

        for cur_xypress in self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, lim, trans = cur_xypress

            # ignore singular clicks - 5 pixels is a threshold
            if abs(x - lastx) < 5 or abs(y - lasty) < 5:
                self._xypress = None
                self.draw()
                return

            x0, y0, x1, y1 = lim.extents

            # zoom to rect
            inverse = a.transData.inverted()
            lastx, lasty = inverse.transform_point((lastx, lasty))
            x, y = inverse.transform_point((x, y))
            Xmin, Xmax = a.get_xlim()
            Ymin, Ymax = a.get_ylim()

            # detect twinx,y axes and avoid double zooming
            twinx, twiny = False, False
            if last_a:
                for la in last_a:
                    if a.get_shared_x_axes().joined(a, la):
                        twinx = True
                    if a.get_shared_y_axes().joined(a, la):
                        twiny = True
            last_a.append(a)

            if twinx:
                x0, x1 = Xmin, Xmax
            else:
                if Xmin < Xmax:
                    if x < lastx:
                        x0, x1 = x, lastx
                    else:
                        x0, x1 = lastx, x

                    if x0 < Xmin:
                        x0 = Xmin
                    if x1 > Xmax:
                        x1 = Xmax
                else:
                    if x > lastx:
                        x0, x1 = x, lastx
                    else:
                        x0, x1 = lastx, x

                    if x0 > Xmin:
                        x0 = Xmin
                    if x1 < Xmax:
                        x1 = Xmax

            if twiny:
                y0, y1 = Ymin, Ymax
            else:
                if Ymin < Ymax:
                    if y < lasty:
                        y0, y1 = y, lasty
                    else:
                        y0, y1 = lasty, y

                    if y0 < Ymin:
                        y0 = Ymin
                    if y1 > Ymax:
                        y1 = Ymax
                else:
                    if y > lasty:
                        y0, y1 = y, lasty
                    else:
                        y0, y1 = lasty, y

                    if y0 > Ymin:
                        y0 = Ymin
                    if y1 < Ymax:
                        y1 = Ymax

            if self._active == "ZOOMin":   
                a.set_xlim((x0, x1))
                a.set_ylim((y0, y1))

            elif self._active == "ZOOMout": 
                if a.get_xscale() == 'log':
                    alpha = np.log(Xmax / Xmin) / np.log(x1 / x0)
                    rx1 = pow(Xmin / x0, alpha) * Xmin
                    rx2 = pow(Xmax / x0, alpha) * Xmin
                else:
                    alpha = (Xmax - Xmin) / (x1 - x0)
                    rx1 = alpha * (Xmin - x0) + Xmin
                    rx2 = alpha * (Xmax - x0) + Xmin

                if a.get_yscale() == 'log':
                    alpha = np.log(Ymax / Ymin) / np.log(y1 / y0)
                    ry1 = pow(Ymin / y0, alpha) * Ymin
                    ry2 = pow(Ymax / y0, alpha) * Ymin
                else:
                    alpha = (Ymax - Ymin) / (y1 - y0)
                    ry1 = alpha * (Ymin - y0) + Ymin
                    ry2 = alpha * (Ymax - y0) + Ymin
                a.set_xlim((rx1, rx2))
                a.set_ylim((ry1, ry2))

        self.draw()
        self._xypress = None
        self._button_pressed = None
        try:
            del self.lastrect
        except AttributeError:
            pass

    @checkLock
    def onClick(self, event):
        # Get the axes within which the point falls
        self._active = "ACTIVE"
        axes = event.inaxes
        if axes not in self.subplots:
            return
        now, button = time.time(), event.button
        delay = now - self.lastTime
        self.lastTime, self.lastButton = now, button

        if button == self.lastButton and delay < 0.3:   # double click
            for a in self.fig.get_axes():
                if a.in_axes(event):
                    a.relim()
                    #a.autoscale_view()
                    a.autoscale()
                    self.autoscale[a] = True
            self.draw()
            return
        if event.key is None:
            self._active = "ZOOMin"
            self.press_zoom(event)
        elif event.key == "ctrl+control":
            self._active = "ZOOMout"
            self.press_zoom(event)
        elif event.key == "alt+alt":
            self._active = "STRETCH"
            self.press_pan(event)
        elif event.key == "shift":
            self._active = "PAN"
            self.press_pan(event)
        else:
            return

    @checkLock
    def press_zoom(self, event):
        if event.button == 1:
            self._button_pressed = 1
        elif event.button == 3:
            self._button_pressed = 3
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y
        self._xypress = []
        for i, a in enumerate(self.fig.get_axes()):
            if x is not None and y is not None and a.in_axes(event) \
                    and a.get_navigate() and a.can_zoom():
                self.autoscale[a] = False
                self._xypress.append((x, y, a, i, a.viewLim.frozen(), a.transData.frozen()))

    @checkLock
    def setCursor(self, cursor):
        if self._lastCursor != cursor:
            self.set_cursor(cursor)
            self._lastCursor = cursor

    @checkLock
    def onMouseMove(self, event):
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        else:
            if 'ZOOM' in self._active:
                self.setCursor(cursors.MAGNIFIER)
                if self._xypress:
                    x, y = event.x, event.y
                    lastx, lasty, a, ind, lim, trans = self._xypress[0]
                    self.draw_rubberband(event, x, y, lastx, lasty)
            elif self._active == 'PAN':
                self.setCursor(cursors.MOVE)
            else:
                if event.key is None:
                    self.setCursor(cursors.MAGNIFIER)
                elif event.key == "shift":
                    self.setCursor(cursors.MOVE)
                else:
                    self.setCursor(cursors.POINTER)

    @checkLock
    def draw_rubberband(self, event, x0, y0, x1, y1):
        'adapted from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/189744'
        canvas = self.canvas
        dc = wx.ClientDC(canvas)

        # Set logical function to XOR for rubberbanding
        dc.SetLogicalFunction(wx.XOR)

        # Set dc brush and pen
        # Here I set brush and pen to white and grey respectively
        # You can set it to your own choices

        # The brush setting is not really needed since we
        # dont do any filling of the dc. It is set just for
        # the sake of completion.

        wbrush = wx.Brush(wx.Colour(255, 255, 255), wx.TRANSPARENT)
        wpen = wx.Pen(wx.Colour(200, 200, 200), 1, wx.SOLID)
        dc.SetBrush(wbrush)
        dc.SetPen(wpen)

        dc.ResetBoundingBox()
        dc.BeginDrawing()
        height = self.canvas.figure.bbox.height
        y1 = height - y1
        y0 = height - y0

        if y1 < y0:
            y0, y1 = y1, y0
        if x1 < y0:
            x0, x1 = x1, x0

        w = x1 - x0
        h = y1 - y0

        rect = int(x0), int(y0), int(w), int(h)
        try:
            lastrect = self.lastrect
        except AttributeError:
            pass
        else:
            dc.DrawRectangle(*lastrect)  # erase last

        self.lastrect = rect
        dc.DrawRectangle(*rect)
        dc.EndDrawing()

    @checkLock
    def press_pan(self, event):
        'the press mouse button in pan/zoom mode callback'

        if event.button == 1:
            self._button_pressed = 1
        elif event.button == 3:
            self._button_pressed = 3
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y

        self._xypress = []
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if x is not None and y is not None and a.in_axes(event) and a.get_navigate():
                a.start_pan(x, y, event.button)
                self.autoscale[a] = False
                self._xypress.append((a, i))
                self.canvas.mpl_disconnect(self._idDrag)
                self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.drag_pan)

    @checkLock
    def release_pan(self, event):
        'the release mouse button callback in pan/zoom mode'
        self.canvas.mpl_disconnect(self._idDrag)
        self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)
        for a, ind in self._xypress:
            a.end_pan()
        if not self._xypress:
            return
        self._xypress = []
        self._button_pressed = None
        self.draw()

    @checkLock
    def drag_pan(self, event):
        'the drag callback in pan/zoom mode'

        for a, ind in self._xypress:
            # safer to use the recorded button at the press than current button:
            # multiple button can get pressed during motion...
            if self._active == "PAN":
                a.drag_pan(1, "shift", event.x, event.y)
            elif self._active == "STRETCH":
                a.drag_pan(3, "shift", event.x, event.y)
        self.dynamic_update()

    @checkLock
    def dynamic_update(self):
        d = self._idle
        self._idle = False
        if d:
            self.canvas.draw()
            self._idle = True

    @checkLock
    def set_cursor(self, cursor):
        cursor = wx.StockCursor(cursord[cursor])
        self.canvas.SetCursor(cursor)
    
    def getDefaultName(self, all_column=False):
        path = os.path.split(self.fig.viewer.dataFile)[1]
        filename = os.path.splitext(path)[0]
        if all_column:
            return filename
        else:
            ax = self.fig.gca()
            xlabel = ax.get_xlabel()
            ylabel = ax.get_ylabel()
            return "%s_%s_%s" % (filename, xlabel, ylabel)
    
    @checkLock
    def saveImage(self, event):
        fd = wx.FileDialog(None, "Export image name",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=self.getDefaultName(),
                           defaultDir="",
                           wildcard="JPG image (*.jpg)|*.jpg|PNG image (*.png)|*.png|PDF file (*.pdf)|*.pdf")

        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            self.fig.savefig(fname)
        
    @checkLock
    def exportAllanStdDev(self, event): 
        ax = self.fig.gca()
        lines = ax.get_lines()
        heading = []
        dataset = []
        format = []
        for i in range(0, len(lines), 2):
            label = lines[i].get_label()
            xdata, ydata = lines[i].get_data()
            dataset.extend([xdata, ydata])
            heading.extend([("Time_" + label, type(xdata[0])), (label, type(ydata[0]))])
            format.extend(["%-40s", "%-40s"]) 
        data = zip(*dataset)
        fd = wx.FileDialog(None, "Export data filename",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=self.getDefaultName(),
                           defaultDir="",
                           wildcard="CSV file (*.csv)|*.csv")
        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            with open(fname, "w") as f:
                r = range(len(format))
                f.write(",".join(format[i] % heading[i][0] for i in r) + "\n")
                for row in data:
                    f.write(",".join(format[i] % row[i] for i in r) + "\n")
        
    @checkLock
    def exportData(self, event):
        ax = self.fig.gca()
        xdata, ydata = ax.get_lines()[0].get_data()
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        if self.fig.displayMode == 'DateTime':
            xdata = [datenumToUnixTime(x) for x in xdata]
            x0 = datenumToUnixTime(x0)
            x1 = datenumToUnixTime(x1)
            heading = [('time', float64), (ylabel, type(ydata[0]))]
            format = "%-40d,%-40s\n"
        elif self.fig.displayMode == 'Minute':
            heading = [('Minute', float32), (ylabel, type(ydata[0]))]
            format = "%-40d,%-40s\n"
        elif self.fig.displayMode == 'Hour':
            heading = [('Hour', float32), (ylabel, type(ydata[0]))]
            format = "%-40d,%-40s\n"
        elif self.fig.displayMode == "XY":
            heading = [(xlabel, type(xdata[0])), (ylabel, type(ydata[0]))]
            format = "%-40s,%-40s\n"
        data = zip(xdata, ydata)
        data_selected = [row for row in data if x0<=row[0]<=x1 and y0<=row[1]<=y1]
        data_selected = array(data_selected, dtype=heading)
        fd = wx.FileDialog(None, "Export data filename",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=self.getDefaultName(),
                           defaultDir="",
                           wildcard="HDF5 file (*.h5)|*.h5|CSV file (*.csv)|*.csv|DAT file (*.dat)|*.dat")
        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            if fname.endswith(".h5"):
                try:
                    op = tables.openFile(fname, "w")
                    filters = tables.Filters(complevel=1, fletcher32=True)
                    table = op.createTable(op.root, "results", data_selected, filters=filters)
                    table.flush()
                finally:
                    op.close()
            else:
                with open(fname, "w") as f:
                    f.write("%-40s,%-40s\n" % (heading[0][0], ylabel))
                    for row in data_selected:
                        f.write(format % (row[0], row[1]))
                        
    def exportDataAll(self, event):
        ax = self.fig.gca()
        x0, x1 = ax.get_xlim()
        data = self.fig.viewer.table
        if "DATE_TIME" in data:
            col = "DATE_TIME"
        elif "time" in data:
            col = "time"
        else:
            col = "timestamp"
        if self.fig.displayMode == "DateTime":
            x0 = datenumToUnixTime(x0)
            x1 = datenumToUnixTime(x1)
        else:
            origin = datenumToUnixTime(self.fig.offset)
            x0 = origin + x0 * 86400.0 / self.fig.multiplier
            x1 = origin + x1 * 86400.0 / self.fig.multiplier
        if "DATE_TIME" in data or "time" in data:
            data_selected = data[(data[col] >= x0) & (data[col] <= x1)]
        else:
            x0 = unixTimeToTimestamp(x0)
            x1 = unixTimeToTimestamp(x1)
            data_selected = data[(data[col] >= x0) & (data[col] <= x1)]
        fd = wx.FileDialog(None, "Export data filename",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=self.getDefaultName(all_column=True),
                           defaultDir="",
                           wildcard="HDF5 file (*.h5)|*.h5")
        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            #data_selected.to_hdf(fname, "results", mode="w", format="table") # to_hdf doesn't work for old pandas
            try:
                op = tables.openFile(fname, "w")
                filters = tables.Filters(complevel=1, fletcher32=True)
                table = op.createTable(op.root, "results", data_selected.to_records(), filters=filters)
                table.flush()
            finally:
                op.close()
       
    def editImage(self, event):
        editor = ImageEditor(figure=self.fig)
        editor.edit_traits(view=editor.traits_view)
        
    def calStatistics(self, event):
        ax = self.fig.gca()
        line = ax.get_lines()[0]
        xLim = ax.get_xlim()
        xData, yData = line.get_data()
        xData = array(xData)
        yData = array(yData)
        yLim = ax.get_ylim()
        sel = (xData >= xLim[0]) & (xData <= xLim[1])
        boxsel = sel & (yData >= yLim[0]) & (yData <= yLim[1])
        s = getStatistics(yData[boxsel])
        varName = "XYPlot" if self.fig.displayMode == "XY" else self.fig.viewer.varName
        dlg = FigureStats(stats=[s], Variables=[varName])
        dlg.configure_traits(view=dlg.traits_view)

class _MPLFigureEditor(Editor):
    scrollable = True

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.object.figureInteraction = FigureInteraction(self.object.plot2dFigure, self.object.lock)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self, parent):
        panel = wx.Panel(parent, -1, style=wx.CLIP_CHILDREN)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        mpl_control = FigureCanvas(panel, -1, self.value)
        sizer.Add(mpl_control, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.value.canvas.SetMinSize((10, 10))
        return panel

class MPLFigureEditor(BasicEditorFactory):
    klass = _MPLFigureEditor

class Plot2D(HasTraits):
    plot2dFigure = Instance(Figure, (), {"facecolor": "lightgrey", "edgecolor": "black", "linewidth": 2})
    figureInteraction = Instance(FigureInteraction)
    xScale = CStr('linear')
    yScale = CStr('linear')
    xLabel = CStr
    yLabel = CStr
    title = CStr
    sharex = Instance(mpl.axes.Axes)
    sharey = Instance(mpl.axes.Axes)
    traits_view = View(Item("plot2dFigure", editor=MPLFigureEditor(), show_label=False), width=700, height=600, resizable=True)

    lock = Instance(threading.RLock, ())
    autoscaleOnUpdate = CBool(True)

    def plotData(self, *a, **k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        self.plot2dFigure.offset = 0
        share = {}
        if self.sharex:
            share['sharex'] = self.sharex
        if self.sharey:
            share['sharey'] = self.sharey
        self.axes = self.plot2dFigure.add_subplot(111, **share)
        handles = self.axes.plot(*a, **k)
        self.axes.grid(True)
        self.axes.set_xscale(self.xScale)
        self.axes.set_yscale(self.yScale)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        self.axes.set_title(self.title)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()
        return handles

    def plotTimeSeries(self, t, *a, **k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        self.tz = k.get("tz", pytz.timezone("UTC"))
        self.plot2dFigure.tz = self.tz
        self.plot2dFigure.offset = 0
        formatter = mpl.dates.DateFormatter('%H:%M:%S\n%Y/%m/%d', self.tz)
        if len(t) > 0:
            dt = datetime.fromtimestamp(t[0], tz=self.tz)
            t0 = mpl.dates.date2num(dt)
            tbase = t0 + (t - t[0]) / (24.0 * 3600.0)
        else:
            tbase = []
        share = {}
        if self.sharex:
            share['sharex'] = self.sharex
        if self.sharey:
            share['sharey'] = self.sharey
        self.axes = self.plot2dFigure.add_subplot(111, **share)
        handles = self.axes.plot_date(tbase, *a, **k)
        self.axes.grid(True)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        self.axes.set_title(self.title)
        self.axes.xaxis.set_major_formatter(formatter)
        self.axes.xaxis.set_major_locator(MaxNLocator(8))
        labels = self.axes.get_xticklabels()
        for l in labels:
            l.set(rotation=0, fontsize=10)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.tryCanvasDraw()    
        self.lock.release()
        return handles

    def plotHistogram(self, data, *a, **k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        self.axes = self.plot2dFigure.add_subplot(111)
        n, bins, patches = self.axes.hist(data, *a, **k)
        bin_centres = (bins[:-1] + bins[1:]) / 2.0
        coeff, var_matrix = curve_fit(gauss, bin_centres, n, p0=[1., 0., 1.])
        hist_fit = gauss(bin_centres, *coeff)
        self.axes.plot(bin_centres, hist_fit, 'r-')
        info = u"\u03BC = %s\n\u03C3 = %s" % (coeff[1], coeff[2])
        self.addText(0.05,0.9, info, bbox=dict(facecolor='white', alpha=1), transform=self.axes.transAxes)
        self.lock.release()
        return (n, bins)
    
    def addText(self, *a, **k):
        self.lock.acquire()
        handle = self.axes.text(*a, **k)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.tryCanvasDraw()    
        self.lock.release()
        return handle

    def updateData(self, handle, newX, newY):
        self.lock.acquire()
        handle.set_data(newX, newY)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        if self.autoscaleOnUpdate:
            self.autoscale()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.tryCanvasDraw()    
        self.lock.release()

    def updateTimeSeries(self, handle, newX, newY):
        self.lock.acquire()
        t = newX
        if len(t) > 0:
            dt = datetime.fromtimestamp(t[0], tz=self.tz)
            t0 = mpl.dates.date2num(dt)
            tbase = t0 + (t - t[0]) / (24.0 * 3600.0)
        else:
            tbase = []
        handle.set_data(tbase, newY)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        if self.autoscaleOnUpdate:
            self.autoscale()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.tryCanvasDraw()    
        self.lock.release()

    def redraw(self):
        self.lock.acquire()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.tryCanvasDraw()    
        self.lock.release()

    def tryCanvasDraw(self):
        try:
            self.plot2dFigure.canvas.draw()
        except:
            pass

    def autoscale(self):
        self.axes.relim()
        self.axes.autoscale()
        #self.axes.autoscale_view()
        if self.figureInteraction:
            self.figureInteraction.autoscale[self.axes] = True

class CurveFitPanel(HasTraits):
    input = ListStr
    fitParameters = Str()
    fitFunction = Str()
    initialGuess = Str()
    traits_view =  Instance(View)
    
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        self.fitParameters = self.input[0]
        self.fitFunction = self.input[1]
        self.initialGuess = self.input[2]
        self.traits_view = View(VGroup(Item("fitParameters"), Item("fitFunction"), Item("initialGuess")),
                           buttons=OKCancelButtons, width=500, title="Curve Fitting", kind="modal")

class HistogramHandler(Handler):
    def init(self, info):
        info.object.parent.infoSet.add(info)
        Handler.init(self, info)

    def close(self, info, is_ok):
        info.object.parent.infoSet.discard(info)
        info.ui.dispose()                           
                           
class HistogramViewer(HasTraits):
    plot = Instance(Plot2D, ())
    parent = Instance(object)
    dataFile = CStr("")
    data = CArray
    bin = CInt(100)
    normalized = CBool(False)
    saveData = Button
    saveImage = Button
    traits_view = View(VGroup(Item("plot", style="custom", show_label=False),
                              HGroup(Item("bin"),
                                     Item("normalized"),
                                     Item("saveData", show_label=False),
                                     Item("saveImage", show_label=False),
                                     padding=10)),
                       width=500, height=500,resizable=True, handler=HistogramHandler())
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        self.histData, self.histBins = self.plot.plotHistogram(self.data, bins=self.bin)
        self.plot.plot2dFigure.displayMode = "Histogram"
        self.plot.plot2dFigure.viewer = self
        
    def _bin_changed(self):
        self.histData, self.histBins = self.plot.plotHistogram(self.data, bins=self.bin, normed=self.normalized)
        self.plot.figureInteraction.subplots = self.plot.plot2dFigure.axes
        
    def _normalized_changed(self):
        self.histData, self.histBins = self.plot.plotHistogram(self.data, bins=self.bin, normed=self.normalized)
        self.plot.figureInteraction.subplots = self.plot.plot2dFigure.axes
        
    def _saveImage_fired(self):
        path = os.path.split(self.dataFile)[1]
        filename = os.path.splitext(path)[0]
        fd = wx.FileDialog(None, "Export image name",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=filename + "_histogram",
                           defaultDir="",
                           wildcard="JPG image (*.jpg)|*.jpg|PNG image (*.png)|*.png|PDF file (*.pdf)|*.pdf")
        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            self.plot.plot2dFigure.savefig(fname)
        
    def _saveData_fired(self):
        format = "%-40s,%-40s\n"
        bin_centres = (self.histBins[:-1] + self.histBins[1:]) / 2.0
        data = zip(bin_centres, self.histData)
        path = os.path.split(self.dataFile)[1]
        filename = os.path.splitext(path)[0]
        fd = wx.FileDialog(None, "Export data filename",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=filename + "_histogram",
                           defaultDir="",
                           wildcard="CSV file (*.csv)|*.csv")
        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            with open(fname, "w") as f:
                for row in data:
                    f.write(format % (row[0], row[1]))
                               
class XyViewerHandler(Handler):
    def init(self, info):
        info.object.parent.infoSet.add(info)
        Handler.init(self, info)

    def close(self, info, is_ok):
        info.object.parent.infoSet.discard(info)
        info.ui.dispose()
        
    def onSaveConfig(self, info):
        SaveConfigFile(info.object, XYPlot=True)
        
    def polyFit(self, info, order):
        obj = info.object
        obj.getSelection()
        f = bestPolyFitCentered(obj.xData, obj.yData, order)
        obj.information = "y = sum(c[n] * x^n)\n"
        for i, cn in enumerate(f.coeffs):
            obj.information += "c[%d] = %s %s%s\n" % (order-i, cn, u"\u00B1", f.sdev[i])
        obj.fitHandle.set_data(obj.xData, f.fittedValues)
        obj.plot.plot2dFigure.canvas.draw()
        
    def onLinearFit(self, info):
        self.polyFit(info, 1)
        
    def onQuadraticFit(self, info):
        self.polyFit(info, 2)
        
    def onPolyFit(self, info):
        dlg = wx.TextEntryDialog(None, "What's the degree of polynomial function for fitting?", defaultValue="1")
        dlg.ShowModal()
        result = dlg.GetValue()
        dlg.Destroy()
        try:
            order = int(result)
            self.polyFit(info, order)
        except:
            pass
            
    def onCurveFit(self, info):
        obj = info.object
        obj.getSelection()
        cf = CurveFitPanel(input=obj.CurveFitting)
        cf.configure_traits(view=cf.traits_view)
        try:
            obj.CurveFitting = [str(cf.fitParameters), str(cf.fitFunction), str(cf.initialGuess)]
            fitFunc = "lambda x," + cf.fitParameters + ":" + cf.fitFunction
            initGuess = [float(x) for x in cf.initialGuess.split(',')]
            popt, pcov = curve_fit(eval(fitFunc), obj.xData, obj.yData, initGuess)
            sdev = sqrt(pcov.diagonal())
            obj.information = "y = " + cf.fitFunction + "\n"
            for i, p in enumerate(cf.fitParameters.split(',')):
                obj.information += "%s = %s %s%s\n" % (p.strip(), popt[i], u"\u00B1", sdev[i])
            obj.fitHandle.set_data(obj.xData, eval(fitFunc)(obj.xData, *popt))
            obj.plot.plot2dFigure.canvas.draw()
        except Exception, e:
            wx.MessageBox("%s\n%s" % (Exception, e), "Error in Curve Fitting", style=wx.OK | wx.ICON_ERROR)
        
    def onIntegrate(self, info):
        obj = info.object
        obj.getSelection()
        obj.information = "Integrate using the composite trapezoidal rule\n"
        obj.information += "Result: %s" % str(trapz(obj.yData, obj.xData))
        
    def onStatistics(self, info):
        obj = info.object
        obj.getSelection()
        sy = getStatistics(obj.yData)
        obj.information = "Y Min = %s\nY Max = %s\nPeak to peak = %s\n" % (sy.min, sy.max, sy.ptp)
        obj.information += "Average = %s\nStd Dev = %s" % (sy.mean, sy.std)
        
    def onScreenShot(self, info):
        time.sleep(0.3)
        path = os.path.split(info.object.dataFile)[1]
        filename = os.path.splitext(path)[0] + "_Screenshot"
        TakeScreenShot(info.object.traits_view.title, filename)
        
    def onHelp(self, info):
        webbrowser.open(r'file:///' + Program_Path + r'/Manual/user_guide.html#correlation-xy-plot') 

class XyViewer(HasTraits):
    plot = Instance(Plot2D, ())
    dataInfo = CStr     # panel # of x- and y-axes data in SeriesWindow
    dataFile = CStr("")
    xArray = CArray
    yArray = CArray
    xMin = CFloat
    xMax = CFloat
    yMin = CFloat
    yMax = CFloat
    xScale = CStr('linear')
    yScale = CStr('linear')
    xLabel = CStr
    yLabel = CStr
    information = Str
    parent = Instance(object)
    enableAnalysis = Bool(False)
    traits_view = View

    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        # Menu
        saveConfig = Action(name="Save Configuration...", action="onSaveConfig")
        linearFit = Action(name="Linear fit", action="onLinearFit")
        quadraticFit = Action(name="Quadratic fit", action="onQuadraticFit") 
        polyFit = Action(name="Polynomial fit", action="onPolyFit")  
        curveFit = Action(name="Curve fit", action="onCurveFit")  
        integrate = Action(name="Integration", action="onIntegrate")
        statistics = Action(name="Statistics", action="onStatistics")
        manual = Action(name="Help", action="onHelp")
        screenshot = Action(name="Take ScreenShot", action="onScreenShot")
        
        window_items = [Item("plot", style="custom", height=0.8, show_label=False)]
        if self.enableAnalysis: 
            window_items.append(Item("information", style='custom', height=0.2, show_label = False))
            menu = MenuBar(Menu(saveConfig, screenshot, name='&File'),
                           Menu(Menu(linearFit, quadraticFit, polyFit, curveFit, name='Fitting'),
                                integrate, statistics, name='&Analysis'),
                           Menu(manual, name="&Help"))
        else:
            menu = None
        titleList = []
        for timeSeriesWindow in self.parent.parent.infoSet:
            for xyPlot in timeSeriesWindow.object.infoSet:
                titleList.append(xyPlot.object.traits_view.title.split(":")[0])
        title = "XYPlot"
        i = 2
        while title in titleList:
            title = "XYPlot " + str(i)
            i += 1
        self.traits_view = View(VGroup(*window_items),
                               menubar=menu, width=800, height=800,resizable=True, handler=XyViewerHandler(), title=title)
        if "plotVariables" in k:
            plotVariables = k["plotVariables"]
            self.dataHandles = self.plot.plotData(*plotVariables)
            if len(self.dataHandles) == 2:
                self.dataHandle = self.dataHandles[0]
                self.fitHandle = self.dataHandles[1]
            else:
                self.dataHandle, self.fitHandle = None, None
        self.plot.plot2dFigure.displayMode = "XY"
        self.plot.plot2dFigure.viewer = self
        self.xlim = None
        self.ylim = None
        self.CurveFitting = ["p1, p2", "p1 * x + p2", "1, 1"]
    
    def update(self):
        if self.dataHandle:
            self.plot.updateData(self.dataHandle, self.xArray, self.yArray)
        self.plot.axes.set_xscale(self.xScale)
        self.plot.axes.set_yscale(self.yScale)
        if self.xMin < self.xMax:
            self.plot.axes.set_xlim((self.xMin, self.xMax))
        if self.yMin < self.yMax:
            self.plot.axes.set_ylim((self.yMin, self.yMax))
        self.plot.axes.set_xlabel(self.xLabel)
        self.plot.axes.set_ylabel(self.yLabel)
    
    def getSelection(self):
        ax = self.plot.axes
        self.xLim = ax.get_xlim()
        self.yLim = ax.get_ylim()
        sel = (self.xArray >= self.xLim[0]) & (self.xArray <= self.xLim[1])
        self.boxSel = sel & (self.yArray >= self.yLim[0]) & (self.yArray <= self.yLim[1])
        self.xData = self.xArray[self.boxSel]
        self.yData = self.yArray[self.boxSel]
     
class DatViewer(HasTraits):
    plot = Instance(Plot2D, ())
    dataFile = CStr
    dataSetNameList = ListStr
    dataSetName = CStr
    varNameList = ListStr
    varName = CStr
    autoscaleY = CBool(True)
    blockAverage = CBool(False)
    expression = Str(editor=TextEditor(enter_set=False, auto_set=False))
    nAverage = CInt(1)
    mean = CFloat
    stdDev = CFloat
    peakToPeak = CFloat
    doAverage = Button
    loadScript = Button(desc="python script")
    parent = Instance(object)
    
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        self.tz = tzlocal.get_localzone()
        self.dataHandle = self.plot.plotTimeSeries([], [], '-', tz=self.tz)[0]
        self.plot.plot2dFigure.displayMode = "DateTime"
        self.plot.plot2dFigure.viewer = self
        self.plot.axes.callbacks.connect("xlim_changed", self.notify)
        self.xLim = None
        self.yLim = None
        self.xData = None
        self.yData = None
        self.boxSel = None
        self.updateFigure = True
        self.expression = "y"
    
    def notify(self, ax):
        self.xLim = ax.get_xlim()
        self.yLim = ax.get_ylim()
        self.xData = self.dataHandle.get_xdata()
        self.yData = self.dataHandle.get_ydata()
        self.sel = (self.xData >= self.xLim[0]) & (self.xData <= self.xLim[1])
        if self.autoscaleY:
            ymin, ymax = None, None
            if any(self.sel):
                ymin = min(self.yData[self.sel])
                ymax = max(self.yData[self.sel])
            if ymin is not None and ymax is not None:
                ax.set_ylim(ymin, ymax)
                self.boxSel = self.sel
        else:
            self.boxSel = self.sel & (self.yData >= self.yLim[0]) & (self.yData <= self.yLim[1])
        
        if any(self.boxSel):
            b = getStatistics(self.yData[self.boxSel])
            self.mean = b.mean
            self.stdDev = b.std
            self.peakToPeak = b.ptp
            
        # update other panels 
        if self.parent.listening:
            if self.plot.plot2dFigure.offset is None:
                wx.CallAfter(self.parent.notify, self, self.xLim, self.yLim, tz=self.plot.plot2dFigure.tz)
            else:
                wx.CallAfter(self.parent.notify, self, self.xLim, self.yLim)
            
    def _dataFile_changed(self):
        # Figure out the tree of tables and arrays
        self.dataSetNameList = []
        self.dataSetName = ""
        self.varName = ""
        
        if self.dataFile:
            self.ip = tables.openFile(self.dataFile)
            for n in self.ip.walkNodes("/"):
                if isinstance(n, tables.Table):
                    self.dataSetNameList.append(n._v_pathname)

            if 1 == len(self.dataSetNameList):
                # this triggers DatViewer::_dataSetName_changed()
                # which populates the var name dropdown
                self.dataSetName = self.dataSetNameList[0]
    
    def _dataSetName_changed(self):
        if self.dataSetName:
            # try:  # for pandas 0.16
                # self.table = self.data.get(self.dataSetName)
            # except:   # for old pandas
                # table = getattr(self.data.handle.root, self.dataSetName)
                # self.table = DataFrame.from_records(table.read())
            table = self.ip.getNode(self.dataSetName)
            self.table = DataFrame.from_records(table.read())
            self.table.fillna(0.0)
            self.varNameList = list(self.table.columns.values)
            if self.updateFigure:
                self.parent.filter = ""
            self.parent.checkDataSet()
        else:
            self.varNameList = []

        self.varName = ""
    
    def _varName_changed(self):
        if self.updateFigure:
            self.expression = "y"
            self.nAverage = 1
            self.updatePlot()
            
    def PlotXY(self, xdata, ydata, **k):
        if "enableAnalysis" in k:
            enableAnalysis = k["enableAnalysis"]
        else:
            enableAnalysis = False
        viewer = XyViewer(parent=self.parent, dataFile=self.dataFile, plotVariables=[[], [], '.', [], [], 'r-'], enableAnalysis=enableAnalysis)
        if "xMin" not in k:
            k["xMin"] = min(xdata)
        if "xMax" not in k:
            k["xMax"] = max(xdata)
        if "yMin" not in k:
            k["yMin"] = min(ydata)
        if "yMax" not in k:
            k["yMax"] = max(ydata)
        viewer.set(xArray=array(xdata), yArray=array(ydata), **k)
        viewer.update()
        viewer.trait_view().set(title="XY Plot")
        viewer.edit_traits(view=viewer.traits_view)
        return viewer
            
    def VariableSelector(self, message):
        dlg = CorrelationPlotSelector(nViewers=self.parent.nViewers, 
                                      Variables=[v.varName for v in self.parent.viewers],
                                      instruction=message)
        dlg.configure_traits(view=dlg.traits_view)
        return dlg.getVariables()
            
    def runScript(self, script):
        #script = re.sub(r'\bx\b', self.varName, script)
        env = {}
        for col in self.tableFiltered.columns.values:
            if col[0].isdigit():
                env['dat' + col] = array(self.tableFiltered[col])
            else:
                env[col] = array(self.tableFiltered[col])
        env.update({"_Figure_": self.plot.plot2dFigure, 
                    "_PlotXY_": self.PlotXY, "_VariableSelector_": self.VariableSelector,
                    "_Panels_": self.parent.viewers,
                    "y": array(self.tableFiltered[self.varName]),
                    "x": array(self.xData)})
        if script.endswith(".py"):
            if os.path.exists(script):
                with open(script, "r") as f:
                    script = f.read()
        if "_RESULT_" not in script and "\n" not in script:
            script = "_RESULT_ = " + script
        if "numpy" not in script:
            script = "from numpy import *\n" + script
        try:
            exec script in env
        except Exception, err:
            d = wx.MessageDialog(None, "%s: %s\n%s" % (Exception, err, traceback.format_exc()), "Script Error", style=wx.OK | wx.ICON_ERROR)
            d.ShowModal()
        if "_RESULT_" in env:
            return env["_RESULT_"]
        else:
            return None #array(self.tableFiltered[self.varName])
        
    def runFilter(self, filter):
        env = {}
        for col in self.table.columns.values:
            if col[0].isdigit():
                env['dat' + col] = self.table[col]
            else:
                env[col] = self.table[col]
        if "_RESULT_" not in filter and "\n" not in filter:
            filter = "_RESULT_ = " + filter
        exec filter in env
        return env["_RESULT_"]
        
    def getXData(self):
        if len(self.parent.filter) > 0:
            self.tableFiltered = self.table[self.runFilter(self.parent.filter)]
        else:
            self.tableFiltered = self.table
        
        if "DATE_TIME" in self.tableFiltered:
            dateTime = self.tableFiltered["DATE_TIME"]
        elif "timestamp" in self.tableFiltered:
            dateTime = [unixTime(int(t)) for t in self.tableFiltered["timestamp"]]
        elif "time" in self.tableFiltered:
            dateTime = self.tableFiltered["time"]
        else:
            raise Exception("No time-related data is found in the data set!")
        if self.plot.plot2dFigure.displayMode == 'DateTime':
            return array(dateTime)
        else:
            multiplier = DisplayMode2Multiplier(self.plot.plot2dFigure.displayMode)
            ret = (dateTime - datenumToUnixTime(self.plot.plot2dFigure.offset)) / 86400.0 * multiplier
            return array(ret)
    
    def updatePlot(self):
        #self.plot.updateTimeSeries(self.dataHandle, [], [])
        try:
            if self.varName:
                xLim = self.xLim
                xData = self.getXData()
                values = self.runScript(self.expression)
                if values is not None:
                    p = argsort(xData)
                    self.plot.set(xLabel=self.plot.plot2dFigure.displayMode, yLabel=self.varName)
                    if self.plot.plot2dFigure.displayMode == 'DateTime':
                        self.plot.updateTimeSeries(self.dataHandle, xData[p], values[p])
                    else:
                        self.plot.updateData(self.dataHandle, xData[p], values[p])
                self.notify(self.plot.axes)
                if xLim is not None:
                    wx.CallAfter(self.plot.axes.set_xlim, xLim)

        except Exception, e:
            d = wx.MessageDialog(None, "%s" % e, "Error while displaying", style=wx.OK | wx.ICON_ERROR)
            d.ShowModal()
            
    def _expression_changed(self):
        if self.varName and self.updateFigure:
            self.updatePlot()
    
    def _doAverage_fired(self):
        try:
            if self.varName:
                if self.blockAverage:
                    xData = self.xData[self.boxSel]
                    yData = self.yData[self.boxSel]
                    if self.plot.plot2dFigure.displayMode == 'DateTime':
                        blockSize = self.nAverage / 1440.0  # self.nAverage should be in unit of minute
                    elif self.plot.plot2dFigure.displayMode == 'Minute':
                        blockSize = self.nAverage
                    elif self.plot.plot2dFigure.displayMode == 'Hour':
                        blockSize = self.nAverage / 60.0
                    fTime, fData = [0], [0]
                    numP = 1.0
                    start_time = xData[0]
                    for t, y in zip(xData, yData):
                        if t > start_time + blockSize:
                            fTime.append(0)
                            fData.append(0)
                            numP = 1.0
                            start_time = t
                        fTime[-1] = (numP-1)/numP * fTime[-1] + t/numP
                        fData[-1] = (numP-1)/numP * fData[-1] + y/numP
                        numP += 1.0
                    viewer = self.PlotXY(fTime, fData, xLabel=self.plot.plot2dFigure.displayMode, yLabel=self.varName, enableAnalysis=True)
                    viewer.plot.axes.set_title("Block Average: size = %s minutes" % self.nAverage, fontdict = {'size': 18, 'weight': 'bold'})
                    viewer.plot.redraw()
                    sy = getStatistics(fData)
                    viewer.information = "Data number = %d\nY Min = %s\nY Max = %s\nPeak to peak = %s\n" % (len(fData), sy.min, sy.max, sy.ptp)
                    viewer.information += "Average = %s\nStd Dev = %s" % (sy.mean, sy.std)
                else:
                    xData = self.getXData()
                    values = self.runScript(self.expression)
                    p = argsort(xData)
                    fKernel = ones(self.nAverage, dtype=float) / self.nAverage
                    fTime = lfilter(fKernel, [1], xData[p])[self.nAverage - 1:]
                    fData = lfilter(fKernel, [1], values[p])[self.nAverage - 1:]
                    self.plot.updateTimeSeries(self.dataHandle, fTime, fData)
                    self.notify(self.plot.axes)
        except Exception, e:
            d = wx.MessageDialog(None, "%s" % e, "Error while displaying", style=wx.OK | wx.ICON_ERROR)
            d.ShowModal()
       
    def _loadScript_fired(self):
        d = wx.FileDialog(None, "Open Script file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, 
                          wildcard="Script files (*.py)|*.py", defaultDir=r".\Scripts")
        if d.ShowModal() == wx.ID_OK:
            scriptFile = d.GetPath()
        else:
            return 0
        d.Destroy()
        self.updateFigure = False
        self.expression = scriptFile
        self.updatePlot()
        self.updateFigure = True
    
class CorrelationPlotSelector(HasTraits):
    nViewers = CInt(3)
    instruction = CStr("Select 2 variables and make correlation plot.")
    Yvar = CStr(label="Y:")
    Xvar = CStr(label="X:")
    Variables = ListStr
    vs = CStr("  vs")
    traits_view = Instance(View)
    
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        
        self.traits_view = View(VGroup(
                                Item("instruction", width=400, style="readonly", show_label=False, padding=5),
                                HGroup(Item("Yvar", width=100, editor=EnumEditor(name="Variables")),
                                       Item("vs", style='readonly', width=30, show_label=False),
                                       Item("Xvar", width=100, editor=EnumEditor(name="Variables")),
                                       padding=10),
                                ), 
                                buttons=OKCancelButtons, title="Select Plot Variables", resizable=False, kind="modal")
                                
    def getVariables(self):
        try:
            y = self.Variables.index(self.Yvar)
            x = self.Variables.index(self.Xvar)
            return (x, y)
        except:
            return None

class AnalysisSelector(HasTraits):
    nViewers = CInt(3)
    Variables = ListStr
    instruction = CStr("Select the Variable(s) for analysis:")
    frame1 = Bool(True)
    frame2 = Bool(True)
    frame3 = Bool(True)
    traits_view = Instance(View)
    
    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        a = []
        for i in range(self.nViewers):
            a.append(Item("frame%d" % (i+1), label=self.Variables[i]))
        self.traits_view = View(VGroup(Item("instruction", style="readonly", show_label=False),
                                       *a, padding=10),
                       buttons=OKCancelButtons, title="Select Frames for Analysis",
                       resizable=False, kind="modal")
    
    def getSelection(self):
        sel = [self.frame1]
        if self.nViewers > 1:
            sel.append(self.frame2)
        if self.nViewers > 2:
            sel.append(self.frame3)
        return sel

def TakeScreenShot(windowTitle, fileName):
    try:
        import win32gui
        hwnd = win32gui.FindWindow(None, windowTitle)
        rect = win32gui.GetWindowRect(hwnd)
        offsetX = rect[0]
        offsetY = rect[1]
        width = rect[2] - offsetX
        height = rect[3] - offsetY
    except:
        offsetX = 0
        offsetY = 0
        width = rect[0]
        height = rect[1]
        
    #Create a DC for the whole screen area
    dcScreen = wx.ScreenDC()
    rect = wx.GetDisplaySize()

    #Create a Bitmap that will hold the screenshot image later on
    #Note that the Bitmap must have a size big enough to hold the screenshot
    #-1 means using the current default colour depth
    bmp = wx.EmptyBitmap(width, height)

    #Create a memory DC that will be used for actually taking the screenshot
    memDC = wx.MemoryDC()

    #Tell the memory DC to use our Bitmap
    #all drawing action on the memory DC will go to the Bitmap now
    memDC.SelectObject(bmp)

    #Blit (in this case copy) the actual screen on the memory DC
    #and thus the Bitmap
    memDC.Blit( 0, #Copy to this X coordinate
                0, #Copy to this Y coordinate
                width, #Copy this width
                height, #Copy this height
                dcScreen, #From where do we copy?
                offsetX, #What's the X offset in the original DC?
                offsetY  #What's the Y offset in the original DC?
                )

    #Select the Bitmap out of the memory DC by selecting a new
    #uninitialized Bitmap
    memDC.SelectObject(wx.NullBitmap)
    img = bmp.ConvertToImage()
    
    fd = wx.FileDialog(None, "Capture Screenshot",
                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                   defaultFile=fileName,
                   defaultDir="",
                   wildcard="PNG Images (*.png)|*.png")
    if fd.ShowModal() == wx.ID_OK:
        fileName = fd.GetPath()
    else:
        fd.Destroy()
        return
    fd.Destroy()
    img.SaveFile(fileName, wx.BITMAP_TYPE_PNG)
        
class SeriesWindowHandler(Handler):
    def init(self, info):
        info.object.parent.infoSet.add(info)
        Handler.init(self, info)

    def close(self, info, is_ok):
        for i in info.object.infoSet:
            i.ui.dispose()
        info.object.parent.infoSet.discard(info)
        info.ui.dispose()
        
    def onSaveConfig(self, info):
        SaveConfigFile(info.object)

    def onScreenShot(self, info):
        time.sleep(0.3)
        title = info.object.traits_view.title
        path = os.path.split(info.object.dataFile)[1]
        filename = os.path.splitext(path)[0] + "_Screenshot" 
        TakeScreenShot(title, filename)
                
    def onXaxisInDateTime(self, info):
        for fr in info.object.viewers:
            fig = fr.plot.plot2dFigure
            if fig.displayMode != 'DateTime':
                ax = fig.gca()
                line = ax.get_lines()[0]
                p = SaveFigureProperty(fig, ax)
                tMin, tMax = p.xlim
                yMin, yMax = p.ylim
                xData, yData = line.get_data()
                multiplier = DisplayMode2Multiplier(p.displayMode)
                new_xData = [datenumToUnixTime(dn/multiplier + p.offset) for dn in xData]
                fr.dataHandle = fr.plot.plotTimeSeries(new_xData, yData, '-', tz=p.tz)[0]
                fr.plot.figureInteraction.subplots = fig.axes
                p.xlim = (tMin/multiplier + p.offset, tMax/multiplier + p.offset)
                p.displayMode = 'DateTime'
                p.xlabel = "DateTime"
                SetFigureProperty(fig, fr.plot.axes, p)
                fr.plot.axes.callbacks.connect("xlim_changed", fr.notify)
                
    def onXaxisInMinute(self, info):
        self.XaxisConverter(info, 'Minute')
                    
    def onXaxisInHour(self, info):
        self.XaxisConverter(info, 'Hour')

    def XaxisConverter(self, info, displayMode):
        multiplier = DisplayMode2Multiplier(displayMode)
        for fr in info.object.viewers:
            fig = fr.plot.plot2dFigure
            ax = fig.gca()
            line = ax.get_lines()[0]
            p = SaveFigureProperty(fig, ax)
            tMin, tMax = p.xlim
            yMin, yMax = p.ylim
            xData, yData = line.get_data()
            if p.displayMode == 'DateTime':
                new_xData = (xData - tMin) * multiplier
                fr.dataHandle = fr.plot.plotData(new_xData, yData, '-')[0]
                fr.plot.figureInteraction.subplots = fig.axes
                fr.plot.axes.callbacks.connect("xlim_changed", fr.notify)
                p.xlim = (0.0, (tMax - tMin) * multiplier)
                p.offset = tMin
            else:
                oldMultiplier = DisplayMode2Multiplier(p.displayMode)
                scale = multiplier / oldMultiplier
                new_xData = xData * scale
                fr.plot.set(xLabel=displayMode)
                fr.plot.updateData(fr.dataHandle, new_xData, yData)
                p.xlim = (tMin * scale, tMax * scale)
            p.displayMode = displayMode
            p.xlabel = displayMode
            SetFigureProperty(fig, fr.plot.axes, p)
                
    def onCorrelationPlot(self, info):
        dlg = CorrelationPlotSelector(nViewers=info.object.nViewers,
                                      Variables=[v.varName for v in info.object.viewers])
        dlg.configure_traits(view=dlg.traits_view)
        vars = dlg.getVariables()
        if vars is not None:
            info.object.correlationPlot(*vars)

    def onAllenPlot(self, info):
        obj = info.object
        if obj.nViewers > 1:
            a = AnalysisSelector(nViewers=obj.nViewers, Variables=[v.varName for v in obj.viewers])
            a.configure_traits(view=a.traits_view)
            sel = a.getSelection()
        else:
            sel = [True]
        plotVariables = []
        legends = []
        colors = ['b', 'r', 'y']
        xMax, yMax, yMin = -1e10, -1e10, 1e10
        for i, fr in enumerate(obj.viewers):
            if sel[i]:
                try:
                    n = len(fr.boxSel)
                    if n > 0:
                        xArray, yArray, fit_xData, fit_yData = AllenStandardDeviation(fr)
                        plotVariables.extend([xArray, yArray, colors[i]+'o', fit_xData, fit_yData, colors[i]+'-'])
                        xMax = max(xMax, max(xArray))
                        yMax = max(yMax, max(yArray))
                        yMin = min(yMin, min(yArray))
                        legends.append(fr.varName)
                except:
                    raise
        if len(plotVariables) > 0:
            viewer = XyViewer(parent=obj, dataFile=obj.dataFile, plotVariables=plotVariables)
            viewer.set(xLabel="Second", yLabel='Allan Std Dev', xScale='log', yScale='log', 
                    xMin=1, xMax=xMax, yMin=yMin, yMax=yMax)
            viewer.update()
            viewer.plot.axes.grid(which='both')
            for i in range(0, len(plotVariables)/3, 2):
                viewer.dataHandles[i].set_label(legends[i/2])
            viewer.plot.axes.legend(loc = 3) # location: lower left
            viewer.plot.axes.set_title("Allan Standard Deviation Plot", fontdict = {'size': 18, 'weight': 'bold'})
            title = viewer.traits_view.title+": Allan Std Dev"
            viewer.traits_view.set(title=title)
            viewer.edit_traits(view=viewer.traits_view)
   
    def onHistogram(self, info):
        obj = info.object
        if obj.nViewers > 1:
            a = AnalysisSelector(nViewers=obj.nViewers,
                                 Variables=[v.varName for v in obj.viewers])
            a.configure_traits(view=a.traits_view)
            sel = a.getSelection()
        else:
            sel = [True]
        for i, fr in enumerate(obj.viewers):
            if sel[i]:
                try:
                    n = len(fr.boxSel)
                    if n > 0:
                        viewer = HistogramViewer(parent=obj, dataFile=obj.dataFile, data=fr.yData[fr.boxSel])
                        viewer.trait_view().set(title="Histogram: %s" % (fr.varName), x=100*i+100, y=100*i+100)
                        viewer.edit_traits()
                except:
                    raise
            
    def onStatistics(self, info):
        stats = []
        vars = []
        for fr in info.object.viewers:
            vars.append(fr.varName)
            if fr.boxSel is not None:
                data = fr.yData[fr.boxSel]
                stats.append(getStatistics(data))
            else:
                stats.append(None)
        dlg = FigureStats(stats=stats, Variables=vars)
        dlg.configure_traits(view=dlg.traits_view)
   
    def onHelp(self, info):
        webbrowser.open(r'file:///' + Program_Path + r'/Manual/user_guide.html#time-series-plot')    
        
class SeriesWindow(Window):
    dataFile = CStr
    viewers = List(DatViewer)
    traits_view = Instance(View)
    nViewers = CInt(3)
    filter = Str(editor=TextEditor(enter_set=False, auto_set=False))
    enableFilter = CBool(True)
    parent = Any()
        
    def __init__(self, *a, **k):
        Window.__init__(self, *a, **k)
        self.infoSet = set()
        self.tz = k.get("tz", pytz.timezone("UTC"))
        for n in range(self.nViewers):
            self.viewers.append(DatViewer(parent=self, tz=self.tz))
        self.listening = True
        a = []
        self.cDict = {}
        w = 150
        saveConfig = Action(name="Save Configuration...", action="onSaveConfig")
        takeScreenShot = Action(name="Take ScreenShot...", action="onScreenShot")
        xaxisDateTime = Action(name="x-Axis in Datetime", action="onXaxisInDateTime", style="radio", checked=True)
        xaxisMinute = Action(name="x-Axis in Minute", action="onXaxisInMinute", style="radio")
        xaxisHour = Action(name="x-Axis in Hour", action="onXaxisInHour", style="radio")
        statistics = Action(name="Statistics", action="onStatistics")
        correlationPlot = Action(name="Correlation Plot", action="onCorrelationPlot", enabled_when="object.nViewers > 1")
        allenPlot = Action(name="Allan Standard Deviation Plot", action="onAllenPlot")
        histogram = Action(name="Histogram", action="onHistogram")
        manual = Action(name="Help", action="onHelp")
        for i, fr in enumerate(self.viewers):
            a.append(
                HGroup(
                    Item("plot", object="h%d" % i, style="custom", show_label=False, springy=True),
                    VGroup(
                        Item("dataSetName", object="h%d" % i, editor=EnumEditor(name="dataSetNameList"), width=w),
                        Item("varName", object="h%d" % i, editor=EnumEditor(name="varNameList"), width=w),
                        HGroup(Item("expression", object="h%d" % i, width=-200),
                               Item("loadScript", object="h%d" % i, show_label=False, width=10)),
                        HGroup(Item("autoscaleY", object="h%d" % i), 
                               HGroup(
                                   Item("nAverage", label="Size", object="h%d" % i, width=-30),
                                   Item("blockAverage", label="Block", object="h%d" % i),
                                   Item("doAverage", object="h%d" % i, show_label=False),
                                   show_border=True, label="Average")),
                        Item("mean", object="h%d" % i, width=w),
                        Item("stdDev", object="h%d" % i, width=w),
                        Item("peakToPeak", object="h%d" % i, width=w),
                    )))
            self.cDict["h%d" % i] = fr
        
        tGroup = Group(*a, **dict(layout="split"))
        self.cDict["object"] = self
        self.traits_view = View(VGroup(tGroup, 
                                       Item("filter", enabled_when="object.enableFilter")),
                                menubar=MenuBar(Menu(saveConfig, takeScreenShot, name='&File'),
                                                Menu(correlationPlot, allenPlot, Separator(), statistics, histogram, name='&Analysis'),
                                                Menu(xaxisDateTime, xaxisMinute, xaxisHour, name='&View'),
                                                Menu(manual, name='&Help')),
                                buttons=NoButtons, title="Time Series Viewer",
                                width=800, height=600, resizable=True, handler=SeriesWindowHandler())

    def notify(self, child, xlim, ylim, tz=None):
        self.listening = False
        for v in self.viewers:
            v.plot.axes.set_xlim(xlim)
            if tz is not None:
                v.plot.axes.xaxis.set_major_formatter(mpl.dates.DateFormatter('%H:%M:%S\n%Y/%m/%d', tz))
            v.plot.redraw()
        self.listening = True

    def _dataFile_changed(self):
        for v in self.viewers:
            v.set(dataFile=self.dataFile)   
            
    def _filter_changed(self):
        for v in self.viewers:
            if v.varName and v.updateFigure:
                v.updatePlot()
                
    def checkDataSet(self):
        flag = True
        for v in self.viewers:
            flag = flag & (self.viewers[0].dataSetName == v.dataSetName)
        self.enableFilter = flag
    
    def correlationPlot(self, xView, yView):
        xV = self.viewers[xView]
        yV = self.viewers[yView]
        try:
            viewer = XyViewer(parent=self, plotVariables=[[], [], '.', [], [], 'r-'], enableAnalysis=True)
            if not (len(xV.yData[xV.sel]) > 0 and len(yV.yData[yV.sel]) > 0):
                raise ValueError
            dataInfo = "%d;%d" % (xView, yView)
            viewer.set(xArray=xV.yData[xV.sel], yArray=yV.yData[yV.sel],
                       xLabel=xV.varName, yLabel=yV.varName, dataInfo=dataInfo, dataFile=self.dataFile,
                       xMin=xV.yLim[0], xMax=xV.yLim[1], yMin=yV.yLim[0], yMax=yV.yLim[1])
            viewer.update()
            title = viewer.traits_view.title + ": Correlation"
            viewer.traits_view.set(title=title)
            viewer.edit_traits(view=viewer.traits_view)
            return viewer
        except Exception, e:
            wx.MessageBox("No or incompatible data for correlation plot within window.\n%s" % e)
            
class NotebookHandler(Handler):
    datDirName = CStr

    def onAbout(self, info):
        verFormatStr = "%s\n\n" \
                       "Version:\t%s\n" \
                       "\n" \
                       "Web site:\t\twww.picarro.com\n" \
                       "Technical support:\t408-962-3900\n" \
                       "Email:\t\ttechsupport@picarro.com\n" \
                       "\n" \
                       "Copyright (c) 2005 - %d, Picarro Inc.\n"
        verMsg = verFormatStr % (FULLAPPNAME, APPVERSION, time.localtime()[0])
        wx.MessageBox(verMsg, APPNAME, wx.OK)

    def onOpen(self, info):
        d = wx.FileDialog(None, "Open HDF5 file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            info.object.dataFile = d.GetPath()
            #info.ui.title = "Viewing [" + info.object.dataFile + "]"
        d.Destroy()
        
    def onLoadConfig(self, info):
        def BatchSetFigure(config, params):
            for row in params:
                loadFigureProperty(config, *row)
            
        def loadFigureProperty(config, figureHandle, axesHandle, section):
            fig, ax, co = figureHandle, axesHandle, config
            displayMode = co.get(section, "displayMode", "DateTime")
            if displayMode != "XY":
                tz = pytz.timezone(co.get(section, "tz", "UTC"))
                offset = co.getfloat(section, "offset", 0.0)
            else:
                tz, offset = None, None
            b = Bunch(displayMode=displayMode, tz=tz, offset=offset,
                      title=co.get(section, "title", ""),
                      xlabel=co.get(section, "xlabel", ""),
                      ylabel=co.get(section, "ylabel", ""),
                      xlim=eval(co.get(section, "xlim", "None")),
                      ylim=eval(co.get(section, "ylim", "None")),
                      linestyle=co.get(section, "linestyle", "-"),
                      marker=co.get(section, "marker", ""))
            SetFigureProperty(figureHandle, axesHandle, b)
            
        d = wx.FileDialog(None, "Open Config file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="Config files (*.ini)|*.ini")
        if d.ShowModal() == wx.ID_OK:
            info.object.configFile = d.GetPath()
        else:
            return 
        d.Destroy()
        co = CustomConfigObj(info.object.configFile)
        dataFile = co.get("Main", "Data", info.object.dataFile)
        filter = co.get("Main", "Filter", "")
        nViewer = co.getint("Main", "Viewer", 0)
        if len(dataFile) > 0:
            info.object.dataFile = dataFile
            window = self.onSeries(info, nViewer)
            window.filter = filter
            viewers = window.viewers
            params = []
            for i, fr in enumerate(viewers):
                fr.updateFigure = False
                fr.dataSetName = co.get("Viewer%d" % i, "dataSetName", "")
                fr.varName = co.get("Viewer%d" % i, "varName", "")
                fr.expression = ""
                fr.updateFigure = True
                fr.expression = co.get("Viewer%d" % i, "Expression", "x")
                params.append([fr.plot.plot2dFigure, fr.plot.axes, "Figure%d" % i])
            if co.has_section("XYPlot"):
                xVar = co.getint("XYPlot", "x_Variable", 0)
                yVar = co.getint("XYPlot", "y_Variable", 0)
                fr = window.correlationPlot(xVar, yVar)
                params.append([fr.plot.plot2dFigure, fr.plot.axes, "Figure_XYPlot"])
            wx.CallAfter(BatchSetFigure, co, params)
        else:
            wx.MessageBox("Please open or convert a file first")
              
    def onConcatenateZip(self, info):
        # first let the user choose the .zip archive
        dz = wx.FileDialog(None, "Open .zip HD5 archive to concatenate",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                           wildcard="zip files (*.zip)|*.zip")
        if dz.ShowModal() == wx.ID_OK:
            zipname = dz.GetPath()
        else: return
        dz.Destroy()

        if zipfile.is_zipfile(zipname):
            fname, variableDict = self.inspectZip(zipname)
            if len(variableDict) == 1: return
            # give the user a chance to change it and warn about overwrites
            fd = wx.FileDialog(None, "Output file",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR,
                               defaultFile=fname,
                               wildcard="h5 files (*.h5)|*.h5")
            if fd.ShowModal() == wx.ID_OK:
                fname = fd.GetPath()
            else: return
            fd.Destroy()    
            
            c = ConcatenateZip2File(zipname, fname, variableDict)
            if not c.openFile():
                wx.MessageBox("Cannot open %s. File may be in use." % fname)
                return
            self.threadFileOperation(c, "Concatenating files", "Preparing for file concatenation...", 0.5)
            info.object.dataFile = fname
        else:
            wx.MessageBox("%s is not a .zip archive!" % os.path.split(zipname)[1])

    def inspectZip(self, fileName):
        zipArchive = zipfile.ZipFile(fileName, 'r')
        tmpDir = tempfile.gettempdir()
        try:
            zipfiles = zipArchive.namelist()
            # enumerate files in the .zip archive
            for zfname in zipfiles:
                if zfname.endswith(".h5"):
                    zf = zipArchive.extract(zfname, tmpDir)
                    te = TreeEdit(h5FileName=zf)
                    te.configure_traits()
                    fname = os.path.splitext(fileName)[0] + ".h5"
                    varDict = te.getSelectedDict()
                    zipArchive.close()
                    os.remove(zf)
                    return fname, varDict
        finally:
            zipArchive.close()
        return None, None
            
    def inspectFolder(self, dir):
        # walk the tree, return the filename for the first H5 file we find
        for root, dirs, files in os.walk(dir):
            for name in files:
                fname = os.path.join(root, name)
                if name.endswith(".h5"):
                    te = TreeEdit(h5FileName=fname)
                    te.configure_traits()
                    return fname, te.getSelectedDict()
                elif name.endswith(".zip"):
                    return self.inspectZip(fname)
        return None, None
    
    def threadFileOperation(self, optClass, dlgTitle, dlgMsg, sleepTime=0.2):
        optRun = threading.Thread(target = optClass.run)
        optRun.setDaemon(True)
        optRun.start()
        pd = wx.ProgressDialog(dlgTitle, dlgMsg, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
        while optRun.isAlive():
            if optClass.progress >= 0:
                m = optClass.message
                if m != "":
                    pd.Update(optClass.progress, newmsg=optClass.message)
                time.sleep(sleepTime)
            else:
                break
        if optClass.progress >= 0:
            pd.Update(100)
        else:
            wx.MessageBox(optClass.message, caption="Error", style=wx.ICON_ERROR)
        pd.Destroy()
    
    def onConcatenateFolder(self, info):
        # dir must exist, this suppresses the Make New Folder button
        fValidDir = False
        fPromptForDir = True
        defaultOutputFilename = None
        if len(self.datDirName) > 0:
            defaultPath = self.datDirName
        else:
            defaultPath = r"C:\Picarro\G2000\Log\Archive"
        
        # get folder containing files to concatenate
        while fValidDir is False and fPromptForDir is True:
            d = wx.DirDialog(None, "Select directory tree containing .h5 and/or zip archive of .h5 files",
                             style=wx.DD_DIR_MUST_EXIST | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                             defaultPath=defaultPath)

            if d.ShowModal() == wx.ID_OK:
                path = d.GetPath()
                
                # validate by generating a default output filename from the dir name
                # if None is returned, then it didn't contain any .H5 or ZIPs with .H5 files
                defaultOutputFilename, variableDict = self.inspectFolder(path)
                if len(variableDict) == 1:
                    fPromptForDir = False
                elif defaultOutputFilename is not None and variableDict is not None:
                    fValidDir = True
                else:
                    # warn user that the folder doesn't contain any H5 or ZIP H5 archives
                    # let the user choose whether to select a different folder
                    retCode = wx.MessageBox("Selected folder does not contain any .h5 files or zip archives of .h5 files.\n\nChoose a different folder?",
                                            path, wx.YES_NO | wx.ICON_ERROR)

                    if retCode == wx.ID_YES:
                        # use the parent folder for the last selected folder as a new default,
                        # maybe the user chose the wrong child folder
                        defaultPath = os.path.split(path)[0]
                    else:
                        # user wants to bail, doesn't want to select a different folder
                        fPromptForDir = False

            else:
                # user cancelled out, don't prompt for a folder
                fPromptForDir = False

            # clean up this select folder dialog
            d.Destroy()

            # save off selected folder if it contains valid H5 or ZIP/H5 files
            if fValidDir is True:
                self.datDirName = path

        # user cancelled if still don't have a valid dir, so bail out of concatenating
        if fValidDir is False:
            return
        # get output filename
        # initially use the default filename generated from the selected folder (from above)
        fname = os.path.split(defaultOutputFilename)[1]
        
        # initially use the parent folder of the selected folder
        defaultOutputPath = os.path.split(self.datDirName)[0]
        
        fValidFilename = False
        fPromptForFilename = True
        concatenater = ConcatenateFolder2File(self.datDirName, defaultOutputFilename, variableDict)

        while fValidFilename is False and fPromptForFilename is True:
            # prompt for the filename
            fd = wx.FileDialog(None, "Concatenated output h5 filename",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR,
                               defaultFile=fname,
                               defaultDir=defaultOutputPath,
                               wildcard="h5 files (*.h5)|*.h5")

            if fd.ShowModal() == wx.ID_OK:
                concatenater.fileName = fd.GetPath()
                
                # TODO: assert that self.datDirName is set and folder exists
                # if not self.datDirName:
                #    self.datDirName = os.path.split(fname)[0]
                
                # test whether we can open and write to the output file
                if concatenater.openFile():
                    # succeeded with open, we have a valid output file and it is now open
                    fValidFilename = True
                else:
                    retCode = wx.MessageBox("Cannot open %s. File may be in use.\n\nTry a different output filename?" % fname,
                                            caption="Set concatenated output h5 filename",
                                            style=wx.YES_NO | wx.ICON_ERROR)

                    if retCode == wx.ID_YES:
                        # user wants to specify a different output file
                        # use the same folder as this problem output file to prompt again
                        defaultOutputPath = os.path.split(concatenater.fileName)[0]

                        # generate an output filename, use the selected folder name to generate
                        # a name but this time append date/time info to it
                        fnameBase = self.defaultFilenameFromDir(self.datDirName)
                        fnameBase = os.path.splitext(fnameBase)[0]
                        fnameSuffix = time.strftime("_%Y%m%d_%H%M%S.h5", time.localtime())
                        fname = fnameBase + fnameSuffix
                    else:
                        # user doesn't want another prompt for a different filename (bailing out)
                        fPromptForFilename = False

            else:
                # user cancelled out of the file dialog, done prompting
                fPromptForFilename = False

            # clean up the file dialog
            fd.Destroy()

        if fValidFilename is False:
            return

        # now have a valid input folder and output filename (which is already open)
        # do the concatenation
        self.threadFileOperation(concatenater, "Concatenating files", "Preparing for file concatenation...", 0.5)
        info.object.dataFile = concatenater.fileName
    
    def onBatchConvertDatToH5(self, info):
        d = wx.DirDialog(None, "Open directory with .dat files",
                         style=wx.DD_DIR_MUST_EXIST | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        if d.ShowModal() == wx.ID_OK:
            path = d.GetPath()
            c = Dat2h5BatchConvert(path)
            self.threadFileOperation(c, "Batch Convert DAT to H5 files", "Preparing for file converting...", 0.5)
        d.Destroy()

    def onBatchConvertH5ToDat(self, info):
        d = wx.DirDialog(None, "Open directory with .h5 files",
                         style=wx.DD_DIR_MUST_EXIST | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        if d.ShowModal() == wx.ID_OK:
            path = d.GetPath()
            c = h52DatBatchConvert(path)
            self.threadFileOperation(c, "Batch Convert H5 to DAT files", "Preparing for file converting...", 0.5)
        d.Destroy()

    def onConvertDatToH5(self, info):
        d = wx.FileDialog(None, "Open DAT file",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                          wildcard="dat files (*.dat)|*.dat")

        if d.ShowModal() == wx.ID_OK:
            datName = d.GetPath()
            c = Dat2h5(datName, datName[:-3] + "h5")
            d.Destroy()
            self.threadFileOperation(c, "Convert DAT file to HDF5 format", "Converting %s" % datName)
        else:
            d.Destroy()

    def onConvertH5ToDat(self, info):
        d = wx.FileDialog(None, "Open H5 file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            h5Name = d.GetPath()
            c = h52Dat(h5Name, h5Name[:-2] + "dat")
            d.Destroy()
            self.threadFileOperation(c, "Convert H5 file to DAT format", "Converting %s" % h5Name)
        else:
            d.Destroy()
            
    def onSeries(self, info, nFrames):
        if not info.object.dataFile:
            wx.MessageBox("Please open or convert a file first")
            return
        window = SeriesWindow(nViewers=nFrames, tz=info.object.tz, parent=info.object)
        window.set(dataFile=info.object.dataFile)
        titleList = []
        for i in info.object.infoSet:
            titleList.append(i.object.traits_view.title)
        title = "Time Series Viewer: " + info.object.dataFile
        i = 2
        while title in titleList:
            title = "Time Series Viewer " + str(i) + " :" + info.object.dataFile
            i += 1
        window.traits_view.set(title=title)
        window.edit_traits(view=window.traits_view, context=window.cDict)
        return window

    def onSeries1(self, info):
        return self.onSeries(info, 1)

    def onSeries2(self, info):
        return self.onSeries(info, 2)
        
    def onSeries3(self, info):
        return self.onSeries(info, 3)

    def onInterpolation(self, info):
        # get interval
        d = wx.TextEntryDialog(None, "Dataset will be interpolated on a time grid with a constant interval.\nEnter the desired interval in seconds", defaultValue='1.0')
        try:
            if d.ShowModal() == wx.ID_OK:
                interval = float(d.GetValue())
            else:
                return
        except:
            m = wx.MessageDialog(None, "Unacceptable interval!", style=wx.OK | wx.ICON_ERROR)
            m.ShowModal()
            return
        finally:
            d.Destroy()
        # get source file
        d = wx.FileDialog(None, "Open HDF5 file to interpolate", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            input = d.GetPath()
            d.Destroy() 
        else:
            d.Destroy()
            return
        # get destination file   
        d = wx.FileDialog(None, "Output file", style=wx.FD_OPEN, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            output = d.GetPath()
            d.Destroy() 
        else:
            d.Destroy()
            return
        
        fi = FileInterpolation(input, output, interval)
        self.threadFileOperation(fi, "Data Interpolation", "Interpolating...", 0.5)
        info.object.dataFile = output
    
    def onBlockAverage(self, info):
        # get block size
        d = wx.TextEntryDialog(None, "Enter block size in minutes", defaultValue='1.0')
        try:
            if d.ShowModal() == wx.ID_OK:
                blockSize = float(d.GetValue()) * 60.0
            else:
                return
        except:
            m = wx.MessageDialog(None, "Unacceptable block size!", style=wx.OK | wx.ICON_ERROR)
            m.ShowModal()
            return
        finally:
            d.Destroy()
        # get source file
        d = wx.FileDialog(None, "Open source HDF5 file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            input = d.GetPath()
            d.Destroy() 
        else:
            d.Destroy()
            return
        # get destination file   
        d = wx.FileDialog(None, "Output file", style=wx.FD_OPEN, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            output = d.GetPath()
            d.Destroy() 
        else:
            d.Destroy()
            return
        ba = FileBlockAverage(input, output, blockSize)
        self.threadFileOperation(ba, "Block Average", "Processing...", 0.5)
        info.object.dataFile = output
    
    def onHelp(self, info):
        webbrowser.open(r'file:///' + Program_Path + r'/Manual/index.html')
        
    def onExit(self, info):
        self.close(info, True)
        sys.exit(0)

    def close(self, info, is_ok):
        for i in info.object.infoSet:
            for ii in i.object.infoSet:
                ii.ui.dispose()
            i.ui.dispose()
        info.ui.dispose()

class ViewNotebook(HasTraits):
    dataFile = CStr("")
    config = Instance(CustomConfigObj)
    tzString = CStr("UTC")

    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        if self.config:
            if "Config" in self.config:
                config = self.config["Config"]
                self.tzString = config.get("tz", self.tzString)
        self.tz = pytz.timezone(self.tzString)
        self.infoSet = set()
        
        # File menu
        openAction = Action(name="&Open H5 File...\tCtrl+O", action="onOpen")
        openConfigAction = Action(name="Load Config...\t", action="onLoadConfig")
        openZipAction = Action(name="Unpack Zip File...\tZ", action="onConcatenateZip")
        concatenateActionNew = Action(name="Concatenate H5 Files...\tF", action="onConcatenateFolder")
        convertDatAction = Action(name="Convert &DAT to H5...\tAlt+Shift+C", action="onConvertDatToH5")
        convertH5Action = Action(name="Convert &H5 to DAT...\tAlt+C", action="onConvertH5ToDat")
        batchConvertDatAction = Action(name="&Batch Convert DAT to H5...\tB", action="onBatchConvertDatToH5")
        batchConvertH5Action = Action(name="Batch &Convert H5 to DAT...\tC", action="onBatchConvertH5ToDat")
        interpolationAction = Action(name="Interpolation...", action="onInterpolation")
        blockAverageAction = Action(name="Block Average...", action="onBlockAverage")
        exitAction = Action(name="E&xit", action="onExit")

        # New menu
        series1Action = Action(name="Time Series Plot (&1 Frame)...\t1", action="onSeries1")
        series2Action = Action(name="Time Series Plot (&2 Frames)...\t2", action="onSeries2")
        series3Action = Action(name="Time Series Plot (&3 Frames)...\t3", action="onSeries3")
        
        # Help menu
        aboutAction = Action(name="About...", action="onAbout")
        helpAction = Action(name="Help...", action="onHelp")

        # Curiously, when incorporating separators in the menu the last menu item group must
        # be put in first so it ends up at the bottom of the menu.
        #title = "HDF5 File Viewer"
        title = "%s %s" % (FULLAPPNAME, APPVERSION)

        self.traits_view = View(Item("dataFile", style="readonly", label="H5 file:", padding=10),
                                buttons=NoButtons, title=title,
                                menubar=MenuBar(Menu(exitAction,
                                                     Separator(),
                                                     openAction,
                                                     openConfigAction,
                                                     Separator(),
                                                     openZipAction,
                                                     concatenateActionNew,
                                                     Separator(),
                                                     convertDatAction,
                                                     convertH5Action,
                                                     batchConvertDatAction,
                                                     batchConvertH5Action,
                                                     Separator(),
                                                     interpolationAction,
                                                     blockAverageAction,
                                                     name='&File'),
                                                Menu(series1Action,
                                                     series2Action,
                                                     series3Action,
                                                     name='&New'),
                                                Menu(helpAction,
                                                     aboutAction,
                                                     name='&Help')),
                                handler=NotebookHandler(),
                                width=800,
                                # height=100,
                                resizable=True)

_DEFAULT_CONFIG_NAME = "DatViewer.ini"

HELP_STRING = """\
DatViewer.py [-h] [-c<FILENAME>] [-v]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file. Default = "datViewer.ini"
-v  Print version number.

View/analyze data in an HDF5 file.
"""

def printUsage():
    print HELP_STRING

def printVersion():
    print "%s %s" % (APPNAME, APPVERSION)

def handleCommandSwitches():
    import getopt

    shortOpts = 'hc:p:v'
    longOpts = ["help", "prefs", "version"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    # assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    # support /? and /h for help
    if "/?" in args or "/h" in args:
        options["-h"] = ""

    #executeTest = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit(0)

    if "-v" in options or "--version" in options:
        printVersion()
        sys.exit(0)

    # Start with option defaults...
    configFile = _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile

if __name__ == "__main__":
    gettext.install("app")
    configFile = handleCommandSwitches()

    #config = CustomConfigObj(configFile)
    viewNotebook = ViewNotebook()   #config=config)
    viewNotebook.configure_traits(view=viewNotebook.traits_view)
