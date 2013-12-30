#!/usr/bin/python
"""
File Name: Notifier.py
Purpose: Checks the data received and sends out e-mail notifications as needed.

File History:
    19-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from __future__ import with_statement

import wx
from math import ceil
import os
from Queue import Queue
from Subject import Subject
from threading import Thread
from time import time, sleep
from traceback import format_exc
from EmailSender import EmailSender

class MapError(Exception):
    pass

class ReduceError(Exception):
    pass

class ScriptUtils(object):
    def __init__(self, notifier):
        assert isinstance(notifier, Notifier)
        self.notifier = notifier
        self.set = notifier.set
        self.email = notifier.emailSender.sendMessage
        self.fetch = notifier.fetch
        self.show = notifier.showOnPanel
        
    def assertLimits(self, minVal=None, maxVal=None):
        """Returns predicate which gives True if value is >= minVal and <= maxVal"""
        def predicate(value):
            if value is None or isinstance(value, Exception): return True
            if minVal is not None and value < minVal: return False
            if maxVal is not None and value > maxVal: return False
            return True
        return predicate
    
    def assertMaskedValueEqual(self, checkVal, mask=None):
        """Returns a predicate which returns True if value & mask is equal to checkVal"""
        def predicate(value):
            if value is None or isinstance(value, Exception): return True
            if mask is not None:
                value = value & mask
            return value == checkVal
        return predicate
    
    def assertMaskedValueNotEqual(self, checkVal, mask=None):
        """Returns a predicate which returns True if value & mask is not equal to checkVal"""
        def predicate(value):
            if value is None or isinstance(value, Exception): return True
            if mask is not None:
                value = value & mask
            return value != checkVal
        return predicate
    
    def assertAvailable(self, value):
        if value is None: return True
        return not isinstance(value, Exception)
        
    def countTrue(self, boolList):
        nTrue = 0
        for b in boolList:
            if b: nTrue += 1
        return nTrue
    
    def countFalse(self, boolList):
        nFalse = 0
        for b in boolList:
            if not b: nFalse += 1
        return nFalse
        
class Notifier(Subject):
    """Determines if something is wrong and notifies user via a message on the GUI or e-mail.
    
    Listen to "message" to see what gets sent back to the GUI.
    
    """
        
    def __init__(self, dataModel, basePath, scripts, pane, emailSender, *args, **kwargs):
        assert isinstance(emailSender, EmailSender)
        Subject.__init__(self, *args, **kwargs)
        self.message = ""
        self.variable = ()
        self.loop = 0
        self.dataModel = dataModel
        self.notifyQueue = Queue(0)
        self.periodicExecutor = PeriodicExecutor(5.0, self.periodicNotify)
        path = os.path.join(basePath, scripts['Script'])
        with file(path, "r") as fp:
            sourceString = fp.read()
            # Convert to Unix line ending
            sourceString.replace("\r\n", "\n")
            sourceString.replace("\r", "\n")
            self.scriptCode = compile(sourceString, path, "exec") #providing path accurately allows debugging of script        
        
        self.pane = pane
        self.emailSender = emailSender

        self.scriptUtils = ScriptUtils(self)
        self.env = {"UTILS": self.scriptUtils, "INIT":True}

        self.monitorThread = None
        
    def startMonitor(self):
        self.monitorThread = Thread(target=self.monitor)
        self.monitorThread.setDaemon(True)
        self.monitorThread.start()
        self.dataModel.addListener(self.enqueueChange)
        
    def makePanel(self):
        self.env["DATA"] = {"type":"getLabels"}
        exec self.scriptCode in self.env
        panelLabels = self.env["PANEL_LABELS"]
        textCtrls = {}
        
        paneSizer = self.pane.GetSizer()
        for label in panelLabels:
            staticText = wx.StaticText(self.pane, wx.ID_ANY, label)
            textCtrl = wx.TextCtrl(self.pane, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_RICH2)
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(staticText, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
            sizer.Add(textCtrl, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)
            paneSizer.Add(sizer, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
            textCtrls[label] = textCtrl
        self.pane.Layout()
        return textCtrls

    def fetch(self, data, varList, mapFunc=None, reduceFunc=None, numPoints=1):
        """Gets latest data specified by varList, passed through mapFunc and reduceFunc.
        
        Extract the variables specified by varList from the data and pass these through the
        transformation function xform. 
        For example, to extract the wind speed from its components, we specify the components in
         varList and apply Pythagorus theorem in xform.
         
        Args:
            data: Dictionary of lists, one for each variable
            varList: Variable names to be used to generate the quantity of interest
            mapFunc: Transformation function to map onto variables in varList to produce list 
                of intermediate results
            reduceFunc: Reduction function to apply to intermediate results
            numPoints: Maximum number of points to extract
        Returns:
            Output of reduction function or MapError or ReduceError object
        """    
        for v in varList:
            if v not in data: return MapError("%s not found" % v)
        result = []
        for k in range(-numPoints,0):
            try:
                args = [data[v][k] for v in varList]
                if None in args:
                    result.append(None)
                elif mapFunc is None:
                    result.append(data[varList[0]][k])
                else:
                    result.append(mapFunc(*[data[v][k] for v in varList]))
            except IndexError:
                pass
        if len(result) == 0: 
            return ReduceError()
        if reduceFunc is None:
            return result[-1]
        else:
            return reduceFunc(result)
    
    def showOnPanel(self, value, panelLabel, asString="%s", warningAsserts=None, errorAsserts=None):
        """Shows the value on the notification panel.
    
        Args:
            value: Value to show, or None if information is unavailable
            asString: Format string or a function to convert valueList into string to be displayed. 
                Can return None to indicate invalid data.
            panelLabel: Variable name on notification panel
            errorAsserts:  Function or a list of functions acting on value. If any of these returns False,
                this indicates an error condition
            warningAsserts: Function or a list of functions acting on value. If any of these returns False,
                this indicates a warning condition
        """
        if self.predicateNand(value, errorAsserts):
            status = "ERROR"
        elif self.predicateNand(value, warningAsserts):
            status = "WARNING"
        else:
            status = "NORMAL"
            
        if isinstance(value, MapError):
            self.set("variable", (panelLabel, "UNAVAILABLE", status))
        elif value is None or isinstance(value, ReduceError):
            self.set("variable", (panelLabel, "INVALID", status))
        else:
            if isinstance(asString, (str, unicode)):
                s = asString % value
            else:    
                s = asString(value)
            self.set("variable", (panelLabel, s, status))
            
    def predicateNand(self, value, predicates=None):
        """Applies predicates to value and returns True if any returns False.
        
        This is the logical NAND of the individual predicates.
        """
        result = False
        if predicates is not None:
            try:
                iterator = iter(predicates)
            except TypeError: # Just one predicate (not iterable)
                predicates = [predicates]
            for pred in predicates:
                if not pred(value):
                    result = True
                    break
        return result
                    
    def periodicNotify(self):
        self.loop += 1
        self.notifyQueue.put({"type":"time", "time":time(), "model":self.dataModel})
    
    def enqueueChange(self, model):
        self.notifyQueue.put({"type":"update", "changed":model.changed, "model":model})
        
    def monitor(self):
        while True:
            try:
                self.env["DATA"] = self.notifyQueue.get()
                exec self.scriptCode in self.env
            except:
                exc = format_exc()
                self.set("message", "%s" % exc)
        
class PeriodicExecutor(object):    
    """Runs a  function periodically at integer multiples of a specified period.
    
    To stop running the function, call cancel. This returns once the execution thread has stopped.
    
    Args:
        period: Period (in seconds). The function is called when time.time() is an integer multiple of period.
        func: Function to call
        Arguments following are passed to func whenever it is executed
    """
    def __init__(self, period, func, *args, **kwargs):
        self.thread = Thread(target=self.executor)
        self.period = period
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.cancelling = False
        self.thread.setDaemon(True)
        self.thread.start()
        
    def executor(self):
        oldMult = None
        while not self.cancelling:
            now = time()
            mult = ceil(now/self.period)
            if mult == oldMult:
                mult += 1
            waitTime = max(0.0, self.period * mult - now)
            if waitTime > 0:
                sleep(waitTime)
            oldMult = mult
            self.func(*self.args, **self.kwargs)
        
    def cancel(self):
        self.cancelling = True
        self.thread.join()
        