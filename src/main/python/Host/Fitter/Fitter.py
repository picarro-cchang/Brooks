#!/usr/bin/python
#
"""
File Name: fitter.py
Purpose:
    Starts the fitterThread and allows intermediate and final outputs to be viewed and plotted for
    diagnosis and debugging of fitter scripts

File History:
    07-02-xx sze   In progress
    07-05-07 sze   Modifications to allow a list of analyses to be passed back from the fit script
    07-05-08 sze   Renamed fitter to fitterThread and fitViewer to fitter
    07-09-26 sze   Added handling of pickled files
    07-09-26 sze   Added RPCport configuration option to allow multiple fitters in a pool
    08-09-18 alex  Replaced SortedConfigParser with CustomConfigObj
    08-10-13 alex  Replaced TCP by RPC (FITTER_STATE_TCP --> FITTER_STATE_PROC)
    09-06-30 alex  Support HDF5 format for spectra data

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import sys
import os
import wx
import wx.grid
import wx.py
import time
import calendar
import threading
from wx import stc
from wx.py import shell
from wx.py.filling import FillingTree, SIMPLETYPES
from numpy import array, float_, linspace, log, mean, ndarray, polyfit, shape, std, sum, zeros
from os.path import dirname as os_dirname
from string import maketrans
from Queue import Queue, Empty

from Host.Fitter.fitterThread import FITTER_STATE_IDLE, FITTER_STATE_PROC, FITTER_STATE_READY, FITTER_STATE_FITTING, FITTER_STATE_COMPLETE
from Host.Fitter.fitterThread import main as fitterMain
from Host.Common.SharedTypes import RPC_PORT_FITTER_BASE, BROADCAST_PORT_FITTER_BASE
from Host.Common.GraphPanel import GraphPanel, Sequence, Series
from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
from Host.Common.SingleInstance import SingleInstance

APP_NAME = "Fitter"
__version__ = 1.0
_DEFAULT_CONFIG_NAME = "Fitter.ini"
_MAIN_CONFIG_SECTION = "Setup"
CONFIG_DIR = os.environ['PICARRO_CONF_DIR']
LOG_DIR = os.environ['PICARRO_LOG_DIR']

EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if sys.platform == 'win32':
    threading._time = time.clock #prevents threading.Timer from getting screwed by local time changes

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    TimeStamp = time.clock
else:
    TimeStamp = time.time

class SequenceManager(object):
    """Manage a collection of sequences of equal lengths in a LIFO structure to minimize
    allocation of new objects"""
    def __init__(self,seqLen):
        self.seqLen = seqLen
        self.sequences = []
    def getSequence(self):
        if not self.sequences:
            return Sequence(self.seqLen)
        else:
            return self.sequences.pop()
    def freeSequence(self,sequence):
        # Note that when a sequence is freed, it may still be pointed to by someone else.
        # This is OK since we free all sequences before getting any more. We just need
        # to ensure that the same sequence does not appear more than once in the free
        # list so that it is not gotten more than once.
        sequence.Clear()
        if sequence not in self.sequences:
            self.sequences.append(sequence)

################################################################################
# FitViewManager maintains a dictionary containing fitter output objects which
#  may be viewed by the history and variable viewers
################################################################################

class FitViewManager(object):
    def __init__(self,config):
        self.config = config
        self.nSeq = config.getint("FitViewer","nParamHistory")
        self.seqMgr = SequenceManager(self.nSeq)
        self.fitViewDict = dict(analyses={},fitOutputs=dict(time=self.seqMgr.getSequence()))

    def getFitViewDict(self):
        return self.fitViewDict

    def freeSequencesInDict(self,dictName):
        "Free all sequences"
        for k in dictName:
            v = dictName[k]
            if isinstance(v,Sequence):
                self.seqMgr.freeSequence(v)
            elif isinstance(v,dict):
                self.freeSequencesInDict(v)

    def freeSequences(self):
        self.freeSequencesInDict(self.fitViewDict)

    def clear(self):
        self.freeSequences()
        self.fitViewDict["analyses"].clear()
        self.fitViewDict["fitOutputs"].clear()
        self.fitViewDict["fitOutputs"]["time"]=self.seqMgr.getSequence()

    def update(self,dataAnalysisResults):
        data,analysisList,fitOutputs = dataAnalysisResults
        if not analysisList: return
        for analysis in analysisList:
            if analysis is None:
                continue
            time = analysis["time"]
            for output in fitOutputs:
                if output not in self.fitViewDict["fitOutputs"]:
                    self.fitViewDict["fitOutputs"][output] = ss = self.seqMgr.getSequence()
                    ss.CopyPointers(self.fitViewDict["fitOutputs"]["time"])

            if analysis["name"] not in self.fitViewDict["analyses"]:
                ad = self.fitViewDict["analyses"][analysis["name"]] = dict(byFunction={},byProperty={},
                                                                    byIndex={},time=self.seqMgr.getSequence())
                m = analysis.model
                for i in range(len(m.parameters)):
                    ad["byIndex"]["%03d" % i] = self.seqMgr.getSequence()
                for i in m.basisFunctionByIndex:
                    f = m.basisFunctionByIndex[i]
                    if i<1000: # This is a Galatry peak
                        pd = ad["byFunction"]["peak_%03d" % i] = {}
                        pd["center"] = ad["byIndex"]["%03d" % f.paramIndices[0]]
                        pd["strength"] = ad["byIndex"]["%03d" % f.paramIndices[1]]
                        pd["y"] = ad["byIndex"]["%03d" % f.paramIndices[2]]
                        pd["z"] = ad["byIndex"]["%03d" % f.paramIndices[3]]
                        pd["v"] = ad["byIndex"]["%03d" % f.paramIndices[4]]
                        pd["peak"] = self.seqMgr.getSequence()
                        pd["base"] = self.seqMgr.getSequence()
                    else:
                        pd = ad["byFunction"]["%04d" % i] = {}
                        for j in range(f.numParams()): # Link function parameters to model parameters
                            pd["a%d" % j] = ad["byIndex"]["%03d" % f.paramIndices[j]]
                    pd["_type_"] = "%s" % (type(f),)

            # Fill up Sequences with outputs from each analysis
            ad = self.fitViewDict["analyses"][analysis["name"]]
            ad["time"].Add(time)
            m = analysis.model
            # First get the timestamp for the spectral point
            # Next fill up values of the model parameters
            for i in range(len(m.parameters)):
                ad["byIndex"]["%03d" % i].Add(m.parameters[i])
            # Deal with "peak" and "base" values
            for i in m.basisFunctionByIndex:
                f = m.basisFunctionByIndex[i]
                if i<1000: # This is a Galatry peak
                    pd = ad["byFunction"]["peak_%03d" % i]
                    pd["peak"].Add(analysis[i,"peak"])
                    pd["base"].Add(analysis[i,"base"])
        # Fill up fitOutputs sequences, applying zero-order hold to channels with missing data
        for seq in self.fitViewDict["fitOutputs"]:
            ss = self.fitViewDict["fitOutputs"][seq]
            if seq in fitOutputs:
                ss.Add(fitOutputs[seq])
            elif seq == "time":
                ss.Add(time)
            else:
                ss.Add(ss.GetLatest())

class HistoryViewTree(FillingTree):
    name = 'History View Tree'
    def __init__(self, parent, *args, **kwargs):
        FillingTree.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.init = True

    def objHasChildren(self, obj):
        """Return true if object has children."""
        if self.objGetChildren(obj) and not isinstance(obj,Sequence):
            return True
        else:
            return False

    def OnItemActivated(self, event):
        item = event.GetItem()
        if not isinstance(self.GetPyData(item),Sequence): return
        self.varName = self.getFullName(item)
        timeItem = item
        while timeItem != self.root:
            timeItem = self.GetItemParent(timeItem)
            if "time" in self.GetPyData(timeItem): break
        else:
            raise ValueError("Cannot find timebase")
        self.timeName = self.getFullName(timeItem)+"['time']"
        self.init = True
        wx.FutureCall(20,self.forceRefresh)
        pass

    def forceRefresh(self,init=False):
        rootName = self.getFullName(self.root)
        rootObject = self.GetPyData(self.root)
        if not rootObject['analyses']:
            self.init = True
            self.parent.graph.RemoveAllSeries()
        elif self.init:
            try:
                t = eval(self.timeName,{rootName:rootObject})
                v = eval(self.varName,{rootName:rootObject})
                self.setTitle(self.varName)
                series = Series(t,v)
                self.parent.graph.RemoveAllSeries()
                self.parent.graph.AddSeriesAsLine(series,colour='blue',width=1)
                self.parent.graph.AddSeriesAsPoints(series,colour="black",fillcolour="blue",marker="square",size=1,width=1)
                self.parent.graph.SetGraphProperties(ylabel="")
                self.parent.setMode("graph")
                self.init = False
            except:
                self.init = True
        self.parent.graph.Update()

    def display(self):
        pass

class HistoryViewText(stc.StyledTextCtrl):
    """HistoryViewText based on StyledTextCtrl."""
    name = 'History View Text'

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN):
        stc.StyledTextCtrl.__init__(self, parent, id, pos, size, style)
        # Configure various defaults and user preferences.
        self.SetReadOnly(True)
        self.SetWrapMode(True)

    def SetText(self, *args, **kwds):
        self.SetReadOnly(False)
        stc.StyledTextCtrl.SetText(self, *args, **kwds)
        self.SetReadOnly(True)
class HistoryView(wx.SplitterWindow):
    """History view based on wxSplitterWindow."""

    name = 'History View'

    def __init__(self, config, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.SP_3D|wx.SP_LIVE_UPDATE,
                 name='History View Window', rootObject=None,
                 rootLabel=None, rootIsNamespace=False, static=False):
        """Create a Filling instance."""
        wx.SplitterWindow.__init__(self, parent, id, pos, size, style, name)

        self.tree = HistoryViewTree(parent=self, rootObject=rootObject,
                                    rootLabel=rootLabel,
                                    rootIsNamespace=rootIsNamespace,
                                    static=static)
        self.text = HistoryViewText(parent=self)
        self.graph = GraphPanel(parent=self,id=-1)
        self.config = config

        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graph.SetGraphProperties(ylabel='Sample Data',grid=True,
                                      timeAxes=((self.config.getfloat("FitViewer","TimeOffset_hr"),
                                                 self.config.getboolean("FitViewer","UseUTC")),False),
                                      backgroundColour=bg,frameColour=bg)
        self.graph.Hide()

        wx.FutureCall(1, self.SplitVertically, self.tree, self.text, 200)
        self.mode = "text"

        self.SetMinimumPaneSize(1)

        # Override the filling so that descriptions go to FillingText.
        self.tree.setText = self.text.SetText

        # Display the root item.
        self.tree.SelectItem(self.tree.root)
        self.tree.display()

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnChanged)

    def OnChanged(self, event):
        #this is important: do not evaluate this event=> otherwise, splitterwindow behaves strange
        #event.Skip()
        pass

    def setMode(self,mode):
        if mode in ["graph","text"]:
            if mode == self.mode: return
            elif mode == "graph":
                self.text.Hide()
                self.ReplaceWindow(self.text,self.graph)
                self.graph.Show()
                self.graph.Update()
            else:
                self.graph.Hide()
                self.ReplaceWindow(self.graph,self.text)
                self.text.Show()
            self.mode = mode
        else:
            raise ValueError("Unknown mode")

class HistoryViewFrame(wx.Frame):
    """Frame containing the namespace tree component."""

    name = 'History View Frame'

    def __init__(self, config, root, parent=None, id=-1, title='Fit output history inspector',
                 pos=wx.DefaultPosition, size=(600, 400),
                 style=wx.DEFAULT_FRAME_STYLE, rootObject=None,
                 rootLabel=None, rootIsNamespace=False, static=False):
        """Create FillingFrame instance."""
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        intro = 'Select a fit parameter to view history'
        self.CreateStatusBar()
        self.SetStatusText(intro)
        # import images
        # self.SetIcon(images.getPyIcon())
        self.root = root
        self.historyView = HistoryView(config = config,
                                       parent=self, rootObject=rootObject,
                                       rootLabel=rootLabel,
                                       rootIsNamespace=rootIsNamespace,
                                       static=static)
        # Override so that status messages go to the status bar.
        self.historyView.tree.setStatusText = self.SetStatusText
        self.historyView.tree.setTitle = self.SetTitle
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def OnClose(self,evt):
        self.root.historyFrames.remove(self)
        print "Closing history frame, number left = %d" % (len(self.root.historyFrames),)
        evt.Skip()

    def Refresh(self):
        try:
            self.historyView.tree.forceRefresh()
        except:
            pass
class VariableViewTree(FillingTree):
    name = 'Variable View Tree'
    def __init__(self, parent, *args, **kwargs):
        FillingTree.__init__(self, parent, *args, **kwargs)
        self.parent = parent

    def OnItemActivated(self, event):
        """Add name of item to list of variables to display"""
        item = event.GetItem()
        if not isinstance(self.GetPyData(item),Sequence): return
        text = self.getFullName(item)
        if text in self.parent.varList:
            self.parent.varList.remove(text)
        else:
            self.parent.varList.append(text)
        wx.FutureCall(20,self.parent.table.ForceRefresh)

    def objHasChildren(self, obj):
        """Return true if object has children."""
        if self.objGetChildren(obj) and not isinstance(obj,Sequence):
            return True
        else:
            return False

    def display(self):
        pass

class MyGrid(wx.grid.Grid):
    def __init__(self,*args,**kwargs):
        wx.grid.Grid.__init__(self,*args,**kwargs)
        self.popupMenu = wx.Menu()
        for text in ["Copy","Regress","Statistics"]:
            item = self.popupMenu.Append(-1,text)
            self.Bind(wx.EVT_MENU, self.OnPopItemSelected,item)
        self.Bind(wx.EVT_CHAR,self.OnChar)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnShowPopUp)
        self.transtable = maketrans("\t\n\r","   ")

    def OnChar(self,event):
        if event.GetKeyCode() == 3:
            self.OnCopy()
        else:
            event.Skip()

    def OnShowPopUp(self,event):
        pos = event.GetPosition()
        # pos = self.ScreenToClient(pos)
        self.PopupMenu(self.popupMenu,pos)
        event.Skip()

    def OnPopItemSelected(self,event):
        item = self.popupMenu.FindItemById(event.GetId())
        text = item.GetText()
        if text == "Copy":
            self.OnCopy()
        if text == "Regress":
            self.OnRegress()
        if text == "Statistics":
            self.OnStats()

    def GetSelection(self):
        result = []
        for i in range(self.GetNumberRows()):
            rowData = []
            for j in range(self.GetNumberCols()):
                if self.IsInSelection(i,j) or (i==self.GetGridCursorRow() and j==self.GetGridCursorCol()):
                    rowData.append(self.GetCellValue(i,j))
            if rowData: result.append(rowData)
        return result

    def OnStats(self):
        data = self.GetSelection()
        if len(data) != 1:
            wx.MessageBox("Need single row for mean and standard deviation","Error")
            return
        try:
            x = array([float(d) for d in data[0]],float_)
        except:
            wx.MessageBox("Cannot convert data into floats","Error")
            return
        mu = mean(x)
        sigma = std(x)
        nsf = 4
        if sigma > 0 and abs(mu)>0:
            nsf = max(4,3-log(sigma/abs(mu))/log(10.0))
        wx.MessageBox("Mean: %.*g, StdDev: %.4g" % (int(nsf),mu,sigma),"Information")

    def OnRegress(self):
        data = self.GetSelection()
        if len(data) != 2 or (len(data[0]) != len(data[1])):
            wx.MessageBox("Need two rows of equal length for regression","Error")
        try:
            x = array([float(d) for d in data[0]],float_)
            y = array([float(d) for d in data[1]],float_)
        except:
            wx.MessageBox("Cannot convert regression data into floats","Error")
            return
        p = polyfit(x,y,1)
        m = sum(x*y)/sum(x**2)
        sc = '+'
        if p[1]<0: sc = '-'
        wx.MessageBox("Line of best fit: y = %.4g x %s %.4g\nBest line through origin: y = %.4g x" % (p[0],sc,abs(p[1]),m),"Information")

    def OnCopy(self):
        result = "\n".join(["\t".join([str(item).translate(self.transtable) for item in row]) for row in self.GetSelection()])
        data = wx.TextDataObject()
        data.SetText(result)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unable to open the clipboard","Error")

class VariableViewTable(MyGrid):
    """VariableViewTable based on grid control."""
    name = 'Variable View Table'
    def __init__(self, parent, nColumns, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        MyGrid.__init__(self,parent,id=id,pos=pos,size=size)
        self.parent = parent
        self.table = VariableTable(parent,nColumns)
        self.SetTable(self.table,True)
        self.AutoSizeColumn(0)
        self.SetRowLabelSize(0)
    def ForceRefresh(self):
        self.Refresh()
        self.AutoSizeColumn(0)
        wx.grid.Grid.ForceRefresh(self)

class VariableTable(wx.grid.PyGridTableBase):
    def __init__(self,parent,nColumns):
        self.varName = None
        self.cachedRow = None
        self.cachedVarList = None
        self.parent = parent
        self.nColumns = nColumns + 1
        wx.grid.PyGridTableBase.__init__(self)
    def GetNumberRows(self):
        return 50
    def GetNumberCols(self):
        return self.nColumns
    def IsEmptyCell(self,row,col):
        return False
    def GetColLabelValue(self,col):
        if col == 0: return "Variable"
        else: return "%d" % (col-1,)
    def GetValue(self,row,col):
        index = self.parent.parent.indexEdit.GetValue()
        retVal = ""
        if row != self.cachedRow or self.parent.varList != self.cachedVarList or self.varName is None:
            self.cachedRow = row
            self.cachedVarList = self.parent.varList
            if row<len(self.cachedVarList):
                viewTree = self.parent.tree
                rootName = viewTree.getFullName(viewTree.root)
                rootObject = viewTree.GetPyData(viewTree.root)
                self.varName = self.parent.varList[row]
                self.useTimeFmt = self.varName.find("['time']") >= 0
                try:
                    seq = eval(self.varName,{rootName:rootObject}).GetValues()
                    try:
                        self.values = eval('seq['+index+']',{'seq':seq})
                    except:
                        self.values = array([])
                except:
                    self.values = array([])
        if row<len(self.cachedVarList):
            if col==0:
                retVal = self.varName
            elif isinstance(self.values,ndarray):
                if col-1<len(self.values):
                    if self.useTimeFmt:
                        retVal = self.formatTime(self.values[col-1])
                    else:
                        retVal = "%.5f" % (self.values[col-1],)
            else:
                if col == 1:
                    if self.useTimeFmt:
                        retVal = self.formatTime(self.values)
                    else:
                        retVal = "%.5f" % self.values
        return retVal

    def SetValue(self,row,col,value):
        pass


#    def GetColLabelValue(self,col):
#        return "Multi\nLine"

class VariableView(wx.SplitterWindow):
    """Variable view based on wxSplitterWindow."""

    name = 'Variable View'

    def __init__(self, config, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.SP_3D|wx.SP_LIVE_UPDATE,
                 name='Variable View Window', rootObject=None,
                 rootLabel=None, rootIsNamespace=False, static=False):
        """Create a Filling instance."""
        wx.SplitterWindow.__init__(self, parent, id, pos, size, style, name)
        self.parent = parent
        self.config = config
        self.tree = VariableViewTree(parent=self, rootObject=rootObject,
                                    rootLabel=rootLabel,
                                    rootIsNamespace=rootIsNamespace,
                                    static=static)
        self.varList = []
        self.table = VariableViewTable(parent=self,nColumns=self.config.getint("FitViewer","nParamHistory"))
        self.table.table.formatTime = self.__formatTime(self.config.getboolean("FitViewer","UseUTC"),
                                      self.config.getfloat("FitViewer","TimeOffset_hr"))
        # Set up the formatTime function for the view table based on the configuration file
        wx.FutureCall(1, self.SplitVertically, self.tree, self.table, 200)
        self.SetMinimumPaneSize(1)

        # Override the filling so that descriptions go to FillingText.
        # self.tree.setText = self.table.SetText

        # Display the root item.
        self.tree.SelectItem(self.tree.root)
        self.tree.display()

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnChanged)

    def OnChanged(self, event):
        #this is important: do not evaluate this event=> otherwise, splitterwindow behaves strange
        #event.Skip()
        pass

    def __formatTime(self,utcTime,offsetTime):
        """Returns a formatter for time values"""
        format="%H:%M:%S\n%d-%b-%Y"
        if utcTime:
            to_tm = lambda t: time.gmtime(max(0,t+3600*offsetTime))
            from_tm = lambda tm: calendar.timegm(tm)-3600*offsetTime
        else:
            to_tm = lambda t: time.localtime(max(0,t+3600*offsetTime))
            from_tm = lambda tm: time.mktime(tm)-3600*offsetTime
        return lambda timeVal: time.strftime(format,to_tm(timeVal))

class VariableViewFrame(wx.Frame):
    """Frame containing the namespace tree component."""

    name = 'Variable View Frame'

    def __init__(self, config, root, parent=None, id=-1, title='Fit output variable inspector',
                 pos=wx.DefaultPosition, size=(600, 400),
                 style=wx.DEFAULT_FRAME_STYLE, rootObject=None,
                 rootLabel=None, rootIsNamespace=False, static=False):
        """Create FillingFrame instance."""
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        intro = 'Select a fit parameter to add to list of variables'
        self.CreateStatusBar()
        self.SetStatusText(intro)
        self.root = root
        panel = wx.Panel(self)
        label = wx.StaticText(parent = panel, id = -1, label = "Indices to display (: for all)")
        self.indexEdit = wx.TextCtrl(parent = panel, id = -1, value = "-5:", size = (50,-1))
        self.refresh = wx.Button(parent=panel,id=-1,label="Refresh")
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(label,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL,border=5)
        box.Add(self.indexEdit,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL,border=5)
        box.Add(self.refresh,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL,border=5)
        panel.SetSizer(box)
        self.variableView = VariableView(config = config,
                                         parent=self, rootObject=rootObject,
                                         rootLabel=rootLabel,
                                         rootIsNamespace=rootIsNamespace,
                                         static=static)
        stack = wx.BoxSizer(wx.VERTICAL)
        stack.Add(panel,flag=wx.EXPAND)
        stack.Add(self.variableView,proportion=1,flag=wx.EXPAND)
        self.SetSizer(stack)
        # Override so that status messages go to the status bar.
        self.variableView.tree.setStatusText = self.SetStatusText
        self.Bind(wx.EVT_BUTTON,self.OnRefresh,self.refresh)
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def OnClose(self,evt):
        self.root.variableFrames.remove(self)
        print "Closing variable frame, number left = %d" % (len(self.root.variableFrames),)
        evt.Skip()

    def OnRefresh(self,evt):
        self.Refresh()

    def Refresh(self):
        self.variableView.table.ForceRefresh()

################################################################################
# FitViewer is the top level frame for viewing fitter outputs
################################################################################
class FitViewer(wx.Frame):
    def __init__(self,configFile,useViewer,options):
        wx.Frame.__init__(self,parent=None,id=-1,title='Fit Viewer',size=(1000,700))
        self.config = CustomConfigObj(configFile)
        self.shutDown = False
        self.step = True
        self.colorDatabase = ColorDatabase(self.config,'Colors')
        self.filePaths = []
        self.analysisList = None
        self.rpcPort = self.config.getint("Setup","RPCport",RPC_PORT_FITTER_BASE)
        self.broadcastPort = self.rpcPort - RPC_PORT_FITTER_BASE + BROADCAST_PORT_FITTER_BASE
        splitter = wx.SplitterWindow(self,id=-1,style=wx.SP_LIVE_UPDATE)
        #self.notebook = wx.Notebook(splitter,-1,style=0)
        #self.residualsPanel = ResidualsPanel(self.config,self.notebook,self)
        #self.notebook.AddPage(self.residualsPanel.getPanel(),"Model/Residuals")
        self.residualsPanel = ResidualsPanel(self.config,splitter,self)
        #p2 = self.layoutFrame(self.notebook)
        #self.notebook.AddPage(p2,"Page 2")
        panel = wx.Panel(splitter,id=-1)

        self.newGraph = wx.Button(panel,-1,"New Graph")
        self.newTable = wx.Button(panel,-1,"New Table")
        self.inputSelect = wx.RadioBox(panel, -1, "Select Input",
                    choices=["Data Input", "HDF5 files", "Pickled files"], majorDimension=3,
                    style=wx.RA_SPECIFY_ROWS)
        self.selectFiles = wx.Button(panel,-1,"Select Files")
        self.dataDirLabel = wx.StaticText(panel,-1,"Data Directory")
        self.dataDir = wx.TextCtrl(panel,-1,"",style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_NO_VSCROLL,size=(-1,50))
        self.reset = wx.Button(panel,-1,"<<",size=(30,-1))
        self.process = wx.Button(panel,-1,"Process")
        self.batchMode = wx.RadioBox(panel,-1,choices=["Single","Continuous"], majorDimension=2,
                    style=wx.RA_SPECIFY_COLS)
        self.batchMode.SetSelection(1)
        self.currentFileLabel = wx.StaticText(panel,-1,"Current File")
        self.currentFile = wx.TextCtrl(panel,-1,"",style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_NO_VSCROLL,size=(-1,50))
        self.updateViewer = wx.CheckBox(panel,-1,label="Update viewer with fitter data")
        self.updateViewer.SetValue(True)

        self.analysisName = wx.Choice(panel,-1)
        # wx.TextCtrl(panel,-1,"",style=wx.TE_READONLY)
        self.analysisStage = wx.Choice(panel,-1,size=(45,-1))
        self.modelLabel = wx.StaticText(panel,-1,"Model Components")
        self.modelList = wx.CheckListBox(panel, -1)
        self.defDir = os.curdir

        #self.multiText = wx.TextCtrl(panel,-1,"Here is some text",style=wx.TE_MULTILINE)
        #self.shell = shell.Shell(panel,locals=locals())

        self.selectFiles.Disable()
        self.reset.Disable()
        self.process.Disable()
        box = wx.BoxSizer(wx.VERTICAL)
        hstaticBox = wx.StaticBox(panel,id=-1,label="Open Inspector")
        hbox = wx.StaticBoxSizer(hstaticBox,wx.HORIZONTAL)
        hbox.Add(self.newGraph,proportion=0,flag=wx.BOTTOM|wx.LEFT,border=5)
        hbox.Add((1,-1),proportion=1)
        hbox.Add(self.newTable,proportion=0,flag=wx.BOTTOM|wx.LEFT,border=5)
        box.Add(hbox,proportion=0,flag=wx.EXPAND|wx.LEFT|wx.RIGHT,border=10)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.inputSelect,proportion=0,flag=wx.LEFT,border=10)
        hbox.Add((1,-1),proportion=1)
        hbox.Add(self.selectFiles,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT,border=15)
        box.Add(hbox,flag=wx.EXPAND|wx.TOP|wx.BOTTOM,border=10)
        box.Add(self.dataDirLabel,proportion=0,flag=wx.LEFT|wx.RIGHT,border=10)
        box.Add(self.dataDir,proportion=0,flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND,border=10)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.reset,proportion=0,flag=wx.LEFT|wx.RIGHT,border=10)
        hbox.Add(self.process,proportion=1,flag=wx.RIGHT,border=10)
        box.Add(hbox,flag=wx.EXPAND)
        box.Add(self.batchMode,proportion=0,flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,border=10)
        box.Add(self.currentFileLabel,proportion=0,flag=wx.LEFT|wx.RIGHT,border=10)
        box.Add(self.currentFile,proportion=0,flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND,border=10)
        box.Add(self.updateViewer,proportion = 0,flag=wx.LEFT,border = 10)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.analysisName,proportion=1,flag=wx.LEFT|wx.RIGHT,border=10)
        hbox.Add(self.analysisStage,proportion=0,flag=wx.RIGHT,border=10)
        box.Add(hbox,proportion=0,flag=wx.EXPAND|wx.TOP|wx.BOTTOM,border=10)
        box.Add(self.modelLabel,proportion=0,flag=wx.LEFT|wx.RIGHT,border=10)
        box.Add(self.modelList,proportion=1,flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND,border=10)

        #box.Add(self.multiText,proportion=1,flag=wx.GROW)
        #box.Add(self.shell,proportion=1,flag=wx.GROW)
        panel.SetSizer(box)
        splitter.SetMinimumPaneSize(200)
        splitter.SplitVertically(panel,self.residualsPanel.getPanel(),200)
        self.Bind(wx.EVT_BUTTON,self.OnNewGraph,self.newGraph)
        self.Bind(wx.EVT_BUTTON,self.OnNewTable,self.newTable)

        self.Bind(wx.EVT_BUTTON,self.OnSelectFiles,self.selectFiles)
        self.Bind(wx.EVT_BUTTON,self.OnProcess,self.process)
        self.Bind(wx.EVT_BUTTON,self.OnReset,self.reset)

        self.Bind(wx.EVT_RADIOBOX,self.OnInputSelect,self.inputSelect)
        self.Bind(wx.EVT_RADIOBOX,self.OnBatchMode,self.batchMode)
        self.Bind(wx.EVT_CHECKBOX,self.OnUpdateViewer,self.updateViewer)
        self.Bind(wx.EVT_CHECKLISTBOX,self.OnModelSelect,self.modelList)

        # RSF needed?
        # self.Bind(wx.EVT_CHOICE,self.OnAnalysisStage,self.analysisStage)

        self.Bind(wx.EVT_CHOICE,self.OnAnalysisName,self.analysisName)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.fitterRpc = CmdFIFOServerProxy("http://localhost:%d" % self.rpcPort, ClientName = "FitViewer")
        self.fitQueue = Queue(1)
        self.historyFrames = []
        self.variableFrames = []
        self.fitViewManager = FitViewManager(self.config)
        self.clearHistory()
        self.updateTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.OnTimer,self.updateTimer)
        # Start the fitter in a separate thread
        self.fitterThread = threading.Thread(target=fitterMain,args=(configFile,self.fitQueue,useViewer))
        self.fitterThread.setDaemon(True)
        self.fitterThread.start()
        # sometimes RPC functions are called when fitter thread hasn't been started yet
        # so try calling RPC function several times
        counts = 0
        while True:
            try:
                if "-o" in options: self.fitterRpc.FITTER_setOption(options["-o"])
                if "-d" in options: self.fitterRpc.FITTER_setInputFile(options["-d"])
                break
            except:
                counts += 1
                if counts < 10:
                    time.sleep(0.2)
                    continue
                else:
                    raise

        self.updateTimer.Start(200)

    def clearHistory(self):
        self.funcsByAnalysisSerial = {}
        self.checkList = []
        self.lastAnalysisTime = 0
        self.analysisDone = True
        self.fitViewManager.clear()

    def calculateBasicSeries(self):
        """Calculate data, model and residuals on coarse grid and add to appropriate series"""
        # self.residualsPanel.dataFreq.Clear()
        # self.residualsPanel.dataLoss.Clear()
        # self.residualsPanel.modelLoss.Clear()
        # self.residualsPanel.res.Clear()

        analysis = self.analysisList[self.analysisName.GetSelection()]
        if analysis is not None:
            self.residualsPanel.dataFreq.Clear()
            self.residualsPanel.dataLoss.Clear()
            self.residualsPanel.modelLoss.Clear()
            self.residualsPanel.res.Clear()
            for x in analysis.xData: self.residualsPanel.dataFreq.Add(x)
            for i in range(len(analysis.yData)):
                y = analysis.yData[i]
                self.residualsPanel.dataLoss.Add(y)
                self.residualsPanel.modelLoss.Add(y-analysis.res[i])
                self.residualsPanel.res.Add(analysis.res[i])

    def calculateDetailedSeries(self):
        """Calculate model and partial model on fine grid, partial residual on coarse grid and
        add to appropriate series"""
        # self.residualsPanel.fineFreq.Clear()
        # self.residualsPanel.fineModel.Clear()
        # self.residualsPanel.finePartialModel.Clear()
        # self.residualsPanel.partialRes.Clear()

        analysis = self.analysisList[self.analysisName.GetSelection()]
        if analysis is not None:
            self.residualsPanel.fineFreq.Clear()
            self.residualsPanel.fineModel.Clear()
            self.residualsPanel.finePartialModel.Clear()
            self.residualsPanel.partialRes.Clear()
            xfine = linspace(min(analysis.xData),max(analysis.xData),self.residualsPanel.finePoints)
            yfine = analysis.mockData(self.anStage,xfine)
            for x in xfine: self.residualsPanel.fineFreq.Add(x)
            for y in yfine:
                self.residualsPanel.fineModel.Add(y)
            yfine = self.partialModel(xfine)
            for y in yfine:
                self.residualsPanel.finePartialModel.Add(y)
            yPartial = self.partialModel(analysis.xData)
            for i in range(len(analysis.yData)):
                self.residualsPanel.partialRes.Add(analysis.yData[i]-yPartial[i])

    def setupModelAnalyses(self):
        if self.analysisName.IsEmpty():
            for i in range(len(self.analysisList)):
                self.analysisName.Append("analysis: " + str(i))
            self.analysisName.SetSelection(0)
        return

        # self.analysisName.Clear()
        # for analysis in self.analysisList:
        #     self.analysisName.Append(analysis.name)
        # self.analysisName.SetSelection(len(self.analysisList)-1)

    def doModelAnalysis(self):
        if not self.analysisList: return
        analysis = self.analysisList[self.analysisName.GetSelection()]
        if analysis is not None:
            self.analysisStage.Clear()
            for i in range(analysis.nSteps()): self.analysisStage.Append("%d" % i)
            self.anStage = analysis.nSteps()-1
            self.analysisStage.SetSelection(self.anStage)
            # Construct lists of model function labels and the functions themselves for this analysis
            model = analysis.model
            ser = analysis.serialNumber
            baselineFunc = model.funcList[0]
            self.functionLabels = [ "baseline (%s)" % baselineFunc.name ]
            self.functionList = [ baselineFunc ]
            for i in sorted(model.basisFunctionByIndex.keys()):
                func = model.basisFunctionByIndex[i]
                self.functionLabels.append("%d (%s)" % (i,func.name,))
                self.functionList.append(func)
            self.modelList.Set(self.functionLabels)
            # Check the appropriate boxes, depending on the self.funcsByAnalysisSerial dictionary
            nItems = len(self.functionList)
            if ser not in self.funcsByAnalysisSerial:
                # If this is the first time the analysis has been seen, check all boxes
                self.funcsByAnalysisSerial[ser] = [ True for i in range(nItems) ]
            self.checkList = self.funcsByAnalysisSerial[ser]

            for i in range(nItems):
                self.modelList.Check(i,self.checkList[i])

            if len(analysis.xData) == 0:
                Log('No xData; skipping rest of model analysis', Level=1)
                return

            analysis.computeResiduals(self.anStage)
            self.calculateBasicSeries()
            self.calculateDetailedSeries()
            self.residualsPanel.setupFineDisplay()
            self.residualsPanel.Update()

    def getColorFromIni(self,section,name):
        return self.colorDatabase.getColor(self.config.get(section,name))

    def layoutFrame(self,parent):
        panel = wx.Panel(parent=parent,id=-1)
        # Define the graph panel
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graphPanel1 = GraphPanel(parent=panel,id=-1)
        self.graphPanel1.SetGraphProperties(ylabel='Data and Fit',grid=True,
                                           backgroundColour=bg,frameColour=bg)
        self.graphPanel1.Update()
        self.graphPanel2 = GraphPanel(parent=panel,id=-1)
        self.graphPanel2.SetGraphProperties(ylabel='Residual',grid=True,
                                           backgroundColour=bg,frameColour=bg)
        self.graphPanel2.Update()
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.graphPanel1,proportion=1,flag=wx.GROW)
        vbox.Add(self.graphPanel2,proportion=1,flag=wx.GROW)
        panel.SetSizer(vbox)
        return panel
    def partialModel(self,x):
        """Evaluate the partial model as defined by self.checkList at the
        frequencies specified by x"""
        # Use numpy indexing to extract out the functions selected
        analysis = self.analysisList[self.analysisName.GetSelection()]
        funcs = array(self.functionList)[array(self.checkList)]
        model = analysis.model
        y = zeros(shape(x),x.dtype)
        if model.xModifier is not None: x = model.xModifier(x)
        for f in funcs: y = y + f(x)
        return y

    def OnAnalysisName(self,evt):
        self.doModelAnalysis()

    # RSF comment out to see if this is needed
    # def OnAnalysisStage(self,evt):
    #     analysis = self.analysisList[self.analysisName.GetSelection()]
    #     self.anStage = int(self.analysisStage.GetStringSelection())
    #     analysis.computeResiduals(self.anStage)
    #     self.calculateBasicSeries()
    #     self.calculateDetailedSeries()
    #     self.residualsPanel.setupFineDisplay()
    #     self.residualsPanel.Update()

    def OnBatchMode(self,evt):
        mode = evt.GetEventObject().GetSelection()
        self.fitterRpc.FITTER_setSingleModeRpc(mode == 0)
    def OnClose(self,evt):
        while self.historyFrames:
            self.historyFrames[0].Close()
        while self.variableFrames:
            self.variableFrames[0].Close()
        if self.shutDown or self.inputSelect.GetSelection() in [1,2]:
            sys.exit()
            evt.Skip()
        else:
            self.fitterRpc.FITTER_updateViewer(False)
            self.Hide()
    def OnInputSelect(self,evt):
        self.selectFiles.Enable(self.inputSelect.GetSelection() in [1,2])
        self.filePaths = []
        self.dataDir.SetValue("")
        self.currentFile.SetValue("")
        self.fitterRpc.FITTER_setProcModeRpc(self.inputSelect.GetSelection() in [0])
        self.fitViewManager.clear()
        for f in self.historyFrames: f.Refresh()
        for f in self.variableFrames: f.Refresh()
    def OnModelSelect(self,evt):
        analysis = self.analysisList[self.analysisName.GetSelection()]
        if analysis is not None:
            ser = analysis.serialNumber
            self.checkList = []
            nItems = len(self.functionList)
            for i in range(nItems):
                self.checkList.append(self.modelList.IsChecked(i))
            self.funcsByAnalysisSerial[ser] = self.checkList
            self.calculateDetailedSeries()
            self.residualsPanel.setupFineDisplay()
            self.residualsPanel.Update()

    def OnNewGraph(self,evt):
        historyFrame = HistoryViewFrame(config=self.config,root=self,
                                                      rootObject=self.fitViewManager.getFitViewDict(),
                                                      rootIsNamespace=False,
                                                      rootLabel="fitter")
        self.historyFrames.append(historyFrame)
        print "History frame count = %d" % (len(self.historyFrames),)
        historyFrame.Show()

    def OnNewTable(self,evt):
        variableFrame = VariableViewFrame(config=self.config,root=self,
                                                         rootObject=self.fitViewManager.getFitViewDict(),
                                                         rootIsNamespace=False,
                                                         rootLabel="fitter")
        self.variableFrames.append(variableFrame)
        print "Variable frame count = %d" % (len(self.variableFrames),)
        variableFrame.Show()

    def OnProcess(self,evt):
        self.fitterRpc.FITTER_fitSpectrumRpc()

    def OnReset(self,evt):
        self.clearHistory()
        if self.filePaths:
            self.fitViewManager.clear()
            for f in self.historyFrames: f.Refresh()
            for f in self.variableFrames: f.Refresh()
            if self.inputSelect.GetSelection() == 1:
                self.fitterRpc.FITTER_makeHdf5RepositoryRpc(self.filePaths)
            elif self.inputSelect.GetSelection() == 2:
                self.fitterRpc.FITTER_makePickledRepositoryRpc(self.filePaths)
            self.currentFile.SetValue("")

    def OnSelectFiles(self,evt):
        wildcard = "*.*"
        if self.inputSelect.GetSelection() == 1:
            wildcard = "*.h5"
        elif self.inputSelect.GetSelection() == 2:
            wildcard = "*.rdf"

        dialog = wx.FileDialog(None,"Select files to process",self.defDir,"",wildcard,wx.OPEN|wx.MULTIPLE)
        self.filePaths = []
        if dialog.ShowModal() == wx.ID_OK:
            self.filePaths = dialog.GetPaths()
            self.defDir = os.path.split(self.filePaths[0])[0]
            self.dataDir.SetValue(self.defDir)
            self.fitViewManager.clear()
            for f in self.historyFrames: f.Refresh()
            for f in self.variableFrames: f.Refresh()
            if self.inputSelect.GetSelection() == 1:
                self.fitterRpc.FITTER_makeHdf5RepositoryRpc(self.filePaths)
            elif self.inputSelect.GetSelection() == 2:
                self.fitterRpc.FITTER_makePickledRepositoryRpc(self.filePaths)
        dialog.Destroy()

    def OnTimer(self,evt):
        try:
            command,packet = self.fitQueue.get(False)
            if command == 0:
                self.fitterRpc.FITTER_updateViewer(self.updateViewer.Value)
                self.Show()
            elif command == 1:
                (data,analysisList,resultsDict),fileName = packet
                self.analysisDone = False
                self.currentFile.SetValue("%s\n[%d to %d]" % (fileName,data.startRow,data.endRow))
                self.fitViewManager.update([data,analysisList,resultsDict])
                if analysisList:
                    self.analysisList = analysisList
                    self.setupModelAnalyses() # Sets up the analysis choice combobox
                    #
                    # Commenting out the below section prevents plotting of the coarse grid fit
                    # results and allows the fine grid fit view to persist.
                    #
                    # if self.batchMode.GetSelection() == 1:
                    #     self.calculateBasicSeries()
                    #     self.residualsPanel.setupCoarseDisplay()
                    #     self.residualsPanel.Update()
                    # else:
                    #     self.doModelAnalysis()
                    #     self.analysisDone = True
                    # for f in self.historyFrames: f.Refresh()
                    # for f in self.variableFrames: f.Refresh()
                # self.lastAnalysisTime = TimeStamp()
            elif command == 2:
                self.shutDown = True
                self.Close()
            elif command == 3:
                # Display message box
                self.updateTimer.Stop()
                wx.MessageBox(packet,caption="Fitter exception",style=wx.OK | wx.ICON_ERROR)
                self.updateTimer.Start()
            elif command == 4:
                # Maximize the FitViewer
                try:
                    self.Maximize(packet)
                except:
                    pass
        except Empty: # fitQueue is empty
            if TimeStamp()-self.lastAnalysisTime > 0.5:
                if not self.analysisDone:
                    self.doModelAnalysis()
                    self.analysisDone = True
        try:
            fitterState = self.fitterRpc.FITTER_getFitterStateRpc()
            self.process.Enable(fitterState == FITTER_STATE_READY)
        except:
            pass
            # Disable err msg because it fills the terminal and won't
            # let me see the error message that cause the code to
            # get here.
            #print "Fitter thread not communicating (ok during shutdown)"
        self.reset.Enable(bool(self.filePaths))
        self.batchMode.Enable(self.inputSelect.GetSelection() != 0)

    def OnUpdateViewer(self,evt):
        self.fitterRpc.FITTER_updateViewer(self.updateViewer.Value)

class ColorDatabase(object):
    # The color database allows the user to give names to colors. A named color may be use to define
    #  another color, up to the maximum depth specified by maxIter. It is implemented by looking up color
    #  names is a dictionary (self.dbase) and recursively looking up the result until it is not found.
    #  The unknown key is assumed to be a hexadecimal color specification (as a string of the
    #  form "#RRGGBB") or a string describing one of the standard wxPython colors.
    def __init__(self,config,secname):
        self.dbase = {}
        self.config = config
        self.secname = secname
    # We get the color from the config file on an "as-needed" basis, resolving any back references which may
    #  be present. This is necessary because the order of the keys in an INI file is required to be undefined,
    #  and we cannot assume that dependencies occur before usage.
    def getColor(self,name):
        name = name.lower()
        if name not in self.dbase:
            if self.config.has_option(self.secname,name):
                self.dbase[name] = self.getColor(self.config.get(self.secname,name).lower())
            else:
                return name
        return self.dbase[name]
    def removeColor(self,name):
        del self.dbase[name]
    def clear(self):
        self.dbase.clear()
class ResidualsPanel(object):
    def __init__(self,config,parent,root):
        self.root = root
        self.panel = wx.Panel(parent=parent,id=-1)
        # Define the graph panel
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graphPanel1 = GraphPanel(parent=self.panel,id=-1)
        self.graphPanel1.SetGraphProperties(ylabel='Data and Fit',grid=True,
                                           backgroundColour=bg,frameColour=bg)
        #self.graphPanel1.Update()
        self.graphPanel2 = GraphPanel(parent=self.panel,id=-1)
        self.graphPanel2.SetGraphProperties(ylabel='Residuals',grid=True,
                                           backgroundColour=bg,frameColour=bg)
        #self.graphPanel2.Update()
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.graphPanel1,proportion=1,flag=wx.GROW)
        vbox.Add(self.graphPanel2,proportion=1,flag=wx.GROW)
        self.panel.SetSizer(vbox)
        # Create the sequences for the panels
        maxDataGroups = config.getint("FitViewer","MaxDataGroups")
        self.dataFreq = Sequence(maxDataGroups)
        self.modelLoss = Sequence(maxDataGroups)
        self.dataLoss = Sequence(maxDataGroups)
        self.res = Sequence(maxDataGroups)
        self.partialRes = Sequence(maxDataGroups)
        self.finePoints = config.getint("FitViewer","FinePoints")
        self.fineFreq = Sequence(self.finePoints)
        self.fineModel = Sequence(self.finePoints)
        self.finePartialModel = Sequence(self.finePoints)
        self.modelSeries = Series(self.dataFreq,self.modelLoss)
        self.dataSeries  = Series(self.dataFreq,self.dataLoss)
        self.fineModelSeries = Series(self.fineFreq,self.fineModel)
        self.finePartialModelSeries = Series(self.fineFreq,self.finePartialModel)
        self.resSeries = Series(self.dataFreq,self.res)
        self.partialResSeries = Series(self.dataFreq,self.partialRes)
        # Add sequences to graph panels
        self.mode = ""
        self.setupCoarseDisplay()

    def setupFineDisplay(self):
        if self.mode != "fine":
            self.graphPanel1.RemoveAllSeries()
            self.graphPanel1.AddSeriesAsPoints(self.dataSeries,fillcolour=self.root.getColorFromIni("FitViewer","DataColor"),
                                               colour="black",marker="square",size=1,width=1)
            # self.graphPanel1.AddSeriesAsLine(self.fineModelSeries,
            #                                  colour=self.root.getColorFromIni("FitViewer","ModelColor"),
            #                                  width=self.root.config.getfloat("FitViewer","LineWidth"))
            # self.graphPanel1.AddSeriesAsLine(self.finePartialModelSeries,
            #                                  colour=self.root.getColorFromIni("FitViewer","PartialModelColor"),
            #                                  width=self.root.config.getfloat("FitViewer","LineWidth"))
            self.graphPanel1.AddSeriesAsLine(self.fineModelSeries,
                                             colour="black",
                                             width=1)
            self.graphPanel1.AddSeriesAsLine(self.finePartialModelSeries,
                                             colour="red",
                                             width=1)
            self.graphPanel2.RemoveAllSeries()
            self.graphPanel2.AddSeriesAsLine(self.resSeries,colour=self.root.getColorFromIni("FitViewer","ResidualColor"),
                                             width=self.root.config.getfloat("FitViewer","LineWidth"))
            self.graphPanel2.AddSeriesAsPoints(self.resSeries,fillcolour=self.root.getColorFromIni("FitViewer","ResidualColor"),
                                               colour="black",marker="square",size=1,width=1)
            self.graphPanel2.AddSeriesAsLine(self.partialResSeries,colour=self.root.getColorFromIni("FitViewer","PartialResidualColor"),
                                             width=self.root.config.getfloat("FitViewer","LineWidth"))
            self.graphPanel2.AddSeriesAsPoints(self.partialResSeries,fillcolour=self.root.getColorFromIni("FitViewer","PartialResidualColor"),
                                               colour="black",marker="square",size=1,width=1)
            self.mode = "fine"

    def setupCoarseDisplay(self):
        if self.mode != "coarse":
            self.graphPanel1.RemoveAllSeries()
            self.graphPanel1.AddSeriesAsPoints(self.dataSeries,fillcolour=self.root.getColorFromIni("FitViewer","DataColor"),
                                               colour="black",marker="square",size=1,width=1)
            # self.graphPanel1.AddSeriesAsLine(self.modelSeries,colour=self.root.getColorFromIni("FitViewer","ModelColor"),
            #                                  width=self.root.config.getfloat("FitViewer","LineWidth"))
            self.graphPanel1.AddSeriesAsLine(self.modelSeries,colour="blue",
                                             width=1)
            self.graphPanel2.RemoveAllSeries()
            self.graphPanel2.AddSeriesAsLine(self.resSeries,colour=self.root.getColorFromIni("FitViewer","ResidualColor"),
                                             width=self.root.config.getfloat("FitViewer","LineWidth"))
            self.graphPanel2.AddSeriesAsPoints(self.resSeries,fillcolour=self.root.getColorFromIni("FitViewer","ResidualColor"),
                                               colour="black",marker="square",size=1,width=1)
            self.mode = "coarse"

    def getPanel(self):
        return self.panel
    def Update(self):
        self.graphPanel1.Update()
        self.graphPanel2.Update()

HELP_STRING = \
"""\
Fitter.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./Fitter.ini"

"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    import getopt

    shortOpts = 'c:d:hvo:'
    longOpts = ["help","viewer","ini="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit(0)

    useViewer = False
    if "-v" in options or "--viewer" in options:
        useViewer = True

    #Start with option defaults...
    configFile = ""

    if "--ini" in options:
        configFile = os.path.join(CONFIG_DIR, options["--ini"])
        print "Config file specified at command line: %s" % configFile
    # Allow Integration tools to use -c command switch
    elif "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return (configFile, useViewer, options)

def main():
    """
    Allow Fitter to have up to 3 total instances running
    for instruments with three lasers
    We will start with the name Fitter1 and increment to
    Fitter2, and Fitter3 if necessary
    """
    count = 1
    max_count = 4
    my_instance = SingleInstance((APP_NAME + str(count)))
    if my_instance.alreadyrunning():
        for x in range(count, max_count):
            count += 1
            my_instance = SingleInstance((APP_NAME + str(count)))
            if my_instance.alreadyrunning():
                continue
            else:
                start()
                break
    else:
        start()


def start():
    app = wx.PySimpleApp()
    configFile, useViewer, options = HandleCommandSwitches()
    Log("%s started." % APP_NAME, Level=1)
    frame = FitViewer(configFile, useViewer, options)
    app.MainLoop()
    Log("Exiting program")


if __name__ == "__main__":
    main()
