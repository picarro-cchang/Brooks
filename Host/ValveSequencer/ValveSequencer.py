#!/usr/bin/python
#
# File Name: ValveSequencer.py
# Purpose: Valve control with GUI
#
# File History:
# 08-11-01 alex  Created
# 09-07-20 alex Added more RPC calls and added one more flag to control the start/stop of the sequencer instead of turning on/off the timer. Main reason:
#                   the timer can't be started by any thread other than main thread, and therefore the RPC call would fail.

APP_NAME = "ValveSequencer"
APP_DESCRIPTION = "Valve control with GUI"
__version__ = 1.0

import sys
import os
import string
import wx
import threading

from ValveSequencerFrame import ValveSequencerFrame, NUM_VALVES
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_VALVE_SEQUENCER
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

DISP_TIME_PRECISION = 0.01 # in minute
EXE_INTERVAL = 60000 * DISP_TIME_PRECISION # in ms
SKIP_INTERVAL = 1 # in ms

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, APP_NAME)

class RpcServerThread(threading.Thread):
    def __init__(self, RpcServer, ExitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
            
class ValveSequencer(ValveSequencerFrame):
    def __init__(self, *args, **kwds):
        ValveSequencerFrame.__init__(self, *args, **kwds)
        self.stepTimer = wx.Timer(self)
        self.numSkippedSteps = 0
        self.seqData = None
        self.filename = None
        self.defaultPath = None
        self.holdNewSeq = False
        
        # Run initialization functions
        self.bindEvents()
        self.startServer()

        # Show valve states at start-up
        self.showCurrent(0)
        self.currentStep = 0
        self.freshStart = True
        
        # A flag used to start/stop the sequencer for RPC calls (can't start timer directly from RPC)
        self.runSequencer = False
        self.stepTimer.Start(EXE_INTERVAL)
        self.Show(True)
        
    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onEnableMenu, id = self.idEnableSeq)    
        #self.Bind(wx.EVT_MENU, self.onDisableMenu, id = self.idDisableSeq)
        self.Bind(wx.EVT_MENU, self.onGoFirstStepMenu, id = self.idGoFirstStep)        
        self.Bind(wx.EVT_MENU, self.onLoadFileMenu, id = self.idLoadFile)
        self.Bind(wx.EVT_MENU, self.onSaveFileMenu, id = self.idSaveFile)        
        self.Bind(wx.EVT_SPINCTRL, self.onTotStepsSpinCtrl, self.spinCtrlTotSteps)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.buttonApply)      
        self.Bind(wx.EVT_BUTTON, self.onRunNextButton, self.buttonRunNext) 
        for idx in range(NUM_VALVES):
            self.Bind(wx.EVT_CHECKBOX, self.onCurValState, self.curCheckboxList[idx])   
        self.Bind(wx.EVT_TIMER, self.onStepTimer, self.stepTimer)            
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.bindDynamicEvents() 
        
    def bindDynamicEvents(self):
        """Dynamic binding that changes as the user modifies the valve sequence.
        """
        for row in range(self.numSteps):
            self.Bind(wx.EVT_TEXT, self.onValCodeTextCtrl, self.valCodeTextCtrlList[row])
            self.Bind(wx.EVT_TEXT, self.onDurationTextCtrl, self.durationTextCtrlList[row])
            self.Bind(wx.EVT_TEXT, self.onRotValCodeTextCtrl, self.rotValCodeTextCtrlList[row])
            for idx in range(NUM_VALVES):
                self.Bind(wx.EVT_CHECKBOX, self.onValStateCheckbox, self.valStateCheckboxSet[row][idx])

    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_VALVE_SEQUENCER),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)  
        self.rpcServer.register_function(self.showGui)
        self.rpcServer.register_function(self.hideGui)
        self.rpcServer.register_function(self.isGuiOn)
        self.rpcServer.register_function(self.shutdown)
        self.rpcServer.register_function(self.setValves)
        self.rpcServer.register_function(self.getValves)
        self.rpcServer.register_function(self.startValveSeq)
        self.rpcServer.register_function(self.stopValveSeq)
        self.rpcServer.register_function(self.getValveSeqStatus)
        
        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.shutdown)
        self.rpcThread.start()

    def showGui(self):
        self.Show(True)

    def hideGui(self):
        self.Show(False)
        
    def isGuiOn(self):
        return self.Shown
        
    def shutdown(self):
        #self.rpcServer.stop_server()
        self.onClose(None, True)
        
    def setValves(self, mask = None):
        # Have to update the current row before setting valve register
        if mask == None:
            valCode = int(self.curTextCtrlList[2].GetValue())
            rotValCode = int(self.curTextCtrlList[3].GetValue())
            mask = 64 * rotValCode + valCode
        else:
            valCode = mask % 64
        CRDS_Driver.setValveMask(mask)
        Log("Set valves with new mask %d" % (mask))
        print "Set valves with new mask %d" % (mask)

    def getValves(self):
        return CRDS_Driver.getValveMask()

    def startValveSeq(self):
        self.runSequencer = True
        self.frameMenubar.SetLabel(self.idEnableSeq,"Disable Sequencer")
        print "Valve Sequencer started."
        
    def stopValveSeq(self):
        self.runSequencer = False
        self.frameMenubar.SetLabel(self.idEnableSeq,"Enable Sequencer")
        print "Valve Sequencer stopped."
        
    def isSeqRunning(self):
        return (self.stepTimer.IsRunning() and self.runSequencer)
        
    def getValveSeqStatus(self):
        if self.isSeqRunning():
            return ("ON;%d" % CRDS_Driver.getValveMask())
        else:
            return ("OFF;%d" % CRDS_Driver.getValveMask())
    
    def showCurrent(self, stepNum):
        mask = self.getValves()
        if type(mask) == type(1):                   
            valCode = mask % 64
            rotValCode = (mask - valCode) / 64
            self.curTextCtrlList[2].SetValue(str(valCode))
            self.curTextCtrlList[3].SetValue(str(rotValCode))
            newVal = valCode
            for idx in range(NUM_VALVES):
                self.curCheckboxList[idx].SetValue(newVal % 2)
                newVal = newVal >> 1 
        else:
            pass
        self.curTextCtrlList[0].SetValue(str(stepNum))    
            
    def onEnableMenu(self, event):
        if not self.stepTimer.IsRunning():
            self.stepTimer.Start(EXE_INTERVAL)
        if self.runSequencer:
            self.stopValveSeq()
        else:
            self.startValveSeq()
                
    #def onDisableMenu(self, event):
    #    self.stepTimer.Stop()

    def onGoFirstStepMenu(self, event):
        if self.isSeqRunning():     
            self.currentStep = 1        
            self._runStep(1)
            
    def onTotStepsSpinCtrl(self, event):
        self._addTitleNote()    
        self.setNumSteps(self.spinCtrlTotSteps.GetValue())
        self.setPanelCtrl(loadNewSeq = False)   
        self.doLayout()
        self.bindDynamicEvents() 

    def onApplyButton(self, event):
        if not self.isSeqRunning():
            self.stepTimer.Start(EXE_INTERVAL)
            self.startValveSeq()
        self.holdNewSeq = False
        self.currentStep = self.spinCtrlGoToStep.GetValue()
        self._runStep(self.currentStep)
            
    def onRunNextButton(self, event):
        if self.isSeqRunning():     
            if self.holdNewSeq:
                self.currentStep = 1
                self.holdNewSeq = False
            else:
                if self.currentStep < self.numSteps:
                    self.currentStep += 1
                else:
                    self.currentStep = 1                      
            self._runStep(self.currentStep)
            
    def onStepTimer(self, event):
        if not self.runSequencer:
            return
        remTime = float(self.curTextCtrlList[1].GetValue())
        if (self.stepTimer.GetInterval() == EXE_INTERVAL) and (remTime > DISP_TIME_PRECISION):      
            if self.freshStart:
                self.setValves()
                self.freshStart = False
            # Update remaining time    
            self.curTextCtrlList[1].SetValue(str(remTime-DISP_TIME_PRECISION))          
        else:  
            self.onRunNextButton(event)
            
    def onValStateCheckbox(self, event):
        self._addTitleNote()    
        (row, pos) = divmod(self.valStateIdList.index(event.GetEventObject().GetId()), NUM_VALVES)
        curValCode = int(self.valCodeTextCtrlList[row].GetValue())
        deviation = 2**pos
        eventChecked = event.IsChecked()
        if eventChecked:
            newValCode = curValCode + deviation
        else:
            newValCode = curValCode - deviation
            
        self.valCodeTextCtrlList[row].SetValue(str(newValCode))
        
    def onValCodeTextCtrl(self, event):
        self._addTitleNote()    
        row = self.valCodeIdList.index(event.GetEventObject().GetId())
        try:
            newVal = int(event.GetString()) 
            if newVal > 63:
                self.valCodeTextCtrlList[row].SetValue("63")
                return
            elif newVal < 0:
                self.valCodeTextCtrlList[row].SetValue("0")
                return
        except ValueError:
            return
                  
        for idx in range(NUM_VALVES):
            self.valStateCheckboxSet[row][idx].SetValue(newVal % 2)
            newVal = newVal >> 1     
        
    def onDurationTextCtrl(self, event):
        self._addTitleNote()    
            
    def onRotValCodeTextCtrl(self, event):
        self._addTitleNote()
        
    def _runStep(self, stepNum):  
        self.freshStart = False    
        rowNum = stepNum-1
        curDuration = float(self.durationTextCtrlList[rowNum].GetValue())
        if curDuration < DISP_TIME_PRECISION:
            self.stepTimer.Start(SKIP_INTERVAL)
            self.numSkippedSteps += 1
        else:  
            self._updateCurrentRow(rowNum)
            self.setValves()
            self.stepTimer.Start(EXE_INTERVAL)
            self.numSkippedSteps = 0
   
        if self.numSkippedSteps == self.numSteps:
            self.stopValveSeq()
            print "No valve step to be run - Valve Sequencer stopped."
            self.numSkippedSteps = 0

    def _updateCurrentRow(self, row):            
        self.curTextCtrlList[0].SetValue(str(row+1))
        self.curTextCtrlList[1].SetValue(self.durationTextCtrlList[row].GetValue())
        self.curTextCtrlList[2].SetValue(self.valCodeTextCtrlList[row].GetValue())
        self.curTextCtrlList[3].SetValue(self.rotValCodeTextCtrlList[row].GetValue())        
        for idx in range(NUM_VALVES):
            self.curCheckboxList[idx].SetValue(self.valStateCheckboxSet[row][idx].GetValue())

    def _addTitleNote(self):
        curTitle = self.GetTitle()
        if (curTitle != "External Valve Sequencer") and (curTitle[-1] != "*"):
            self.SetTitle(curTitle + "*")
                
    def onCurValState(self, event):    
        # Make current valve state checkboxes as READONLY
        self.curCheckboxList[self.curValStateIdList.index(event.GetEventObject().GetId())].SetValue(not event.IsChecked())
        
    def onClose(self, event, forced=False):
        if not forced:
            d = wx.MessageDialog(None,"Terminate Valve Sequencer?", "Exit Confirmation", \
                                 style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
            close = (d.ShowModal() == wx.ID_YES)
            d.Destroy()
            if not close:
                return
        self.Destroy()
        event.Skip()

    def onLoadFileMenu(self, event):
        if self.isSeqRunning():
            msgDlg = wx.MessageDialog(self, "Valve Sequencer is running. Do you want to finish the current step after loading the new sequence? \
                                      \n\nSelect 'YES' to continue the current step and run the new sequence afterwards. \
                                      \n\nSelect 'NO' to abandon the current step and run the new sequence immediately.",
                                      "Finish current step?", wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
            self.holdNewSeq = (msgDlg.ShowModal() == wx.ID_YES)                       
            msgDlg.Destroy()    
 
        if not self.defaultPath:
            self.defaultPath = os.getcwd()
            
        dlg = wx.FileDialog(self, "Select Valve Sequence File...",
                            self.defaultPath, wildcard = "*.seq", style=wx.OPEN)
                            
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.defaultPath = os.path.dirname(self.filename)
            try:
                fd = open(self.filename, "r")
                self.seqData = fd.readlines()
                fd.close()
                
                # Process the data in the sequence file
                numSteps = len(self.seqData)  
                self.spinCtrlTotSteps.SetValue(numSteps)
                self.setNumSteps(numSteps)
                self.setPanelCtrl(loadNewSeq = True)   
                self.doLayout()
                self.bindDynamicEvents()           
                for row in range(numSteps):
                    # Separate the values by any number of spaces
                    (dur, valCode, rotValCode) = string.split(self.seqData[row])[:3]
                    self.durationTextCtrlList[row].SetValue(dur)    
                    self.valCodeTextCtrlList[row].SetValue(valCode)
                    self.rotValCodeTextCtrlList[row].SetValue(rotValCode)   
                self.SetTitle("External Valve Sequencer (%s)" % self.filename)                
            except Exception, errMsg:
                wx.MessageBox("Loading %s failed!\nPython Error: %s" % (self.filename, errMsg))
                self.holdNewSeq = False
                dlg.Destroy()
                return
                
            if self.isSeqRunning():
                if self.holdNewSeq == False:
                    # Start new sequence right away
                    self.currentStep = 1
                    self._runStep(1)
                else:
                    # Hold new sequence
                    self.curTextCtrlList[0].SetValue(str(self.currentStep)+" (Last Seq.)")
            else:
                self.holdNewSeq = False
                self.showCurrent(0)
                self.curTextCtrlList[1].SetValue("0") 
                self.currentStep = 0
                self.freshStart = True
        else:
            self.holdNewSeq = False
        dlg.Destroy()             
        
    def onSaveFileMenu(self, event):        
        # Update self.seqData
        self.seqData = []
        for row in range(self.spinCtrlTotSteps.GetValue()):
            newData = "%10s %10s %10s\n" % (self.durationTextCtrlList[row].GetValue(),
                                       self.valCodeTextCtrlList[row].GetValue(),
                                       self.rotValCodeTextCtrlList[row].GetValue())
            self.seqData.append(newData)

        if self.filename:
            defaultVSFile = self.filename
        else:
            defaultVSFile = ""

        if not self.defaultPath:
            self.defaultPath = os.getcwd()
            
        dlg = wx.FileDialog(self, "Save Valve Sequence as...",
                            self.defaultPath, defaultVSFile, wildcard = "*.seq", style=wx.SAVE|wx.OVERWRITE_PROMPT)
                            
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if not os.path.splitext(filename)[1]:
                # Ensure filename extension
                filename = filename + ".seq"
            self.filename = filename
            self.defaultPath = os.path.dirname(self.filename)            
            try:
                fd = open(self.filename, "w")
                fd.writelines(self.seqData)
                fd.close()
                self.SetTitle("External Valve Sequencer (%s)" % self.filename)                
            except Exception, errMsg:
                wx.MessageBox("Saving %s failed!\nPython Error: %s" % (self.filename, errMsg))
        dlg.Destroy()    
                
if __name__ == "__main__":
    Log("%s started." % APP_NAME, Level = 0)
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = ValveSequencer(None, -1, "")
    app.SetTopWindow(frame)
    app.MainLoop()
    Log("Exiting program")
