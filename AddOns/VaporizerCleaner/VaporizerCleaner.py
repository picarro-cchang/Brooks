# Embedded file name: VaporizerCleaner.py
import os
import sys
import wx
import time
import CmdFIFO
import threading
from SharedTypes import RPC_PORT_DRIVER
from VaporizerCleanerFrame import VaporizerCleanerFrame
DISP_TIME_PRECISION = 0.01
EXE_INTERVAL = 60000 * DISP_TIME_PRECISION
VALVE_SEQ = {0: (0.1, 4),
 1: (0.2, 2),
 2: (0.2, 5),
 3: (0.2, 4),
 4: (0.1, 2),
 5: (0.2, 1),
 6: (0.2, 0)}

class VaporizerCleaner(VaporizerCleanerFrame):

    def __init__(self, *args, **kwds):
        VaporizerCleanerFrame.__init__(self, *args, **kwds)
        self.iOutletValve.Enable(True)
        self.iPumpdownRoutine.Enable(False)
        self.DriverRpc = CmdFIFO.CmdFIFOServerProxy('http://localhost:%d' % RPC_PORT_DRIVER, ClientName='Vaporizer Cleaner')
        self.runRoutine = False
        self.openOutlet = False
        self.firstRun = True
        self.valveSeqIdx = 0
        self.reqTime, self.valveMask = VALVE_SEQ[self.valveSeqIdx]
        self.stepTimer = wx.Timer(self)
        self.stepTimer.Start(EXE_INTERVAL)
        self.bindEvents()

    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onOutletValveMenu, self.iOutletValve)
        self.Bind(wx.EVT_MENU, self.onPumpdownRoutineMenu, self.iPumpdownRoutine)
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_TIMER, self.onStepTimer, self.stepTimer)

    def onOutletValveMenu(self, evt):
        if self.firstRun:
            d = wx.MessageDialog(None, 'Please ensure Coordinator is not currently running.\n', 'Confirmation', wx.OK | wx.CANCEL)
            okClicked = d.ShowModal() == wx.ID_OK
            d.Destroy()
            if not okClicked:
                return
            else:
                self.firstRun = False
        if not self.openOutlet:
            self.openOutlet = True
            self._setValveStatus(4)
            self.iCtrl.SetLabel(self.idOutletValve, 'Close Outlet Valve')
            self.iPumpdownRoutine.Enable(False)
        else:
            self.openOutlet = False
            self._setValveStatus(0)
            self.textCtrlElapsedTime.SetValue('0.00')
            self.iCtrl.SetLabel(self.idOutletValve, 'Open Outlet Valve')
            self.iPumpdownRoutine.Enable(True)
        return

    def onPumpdownRoutineMenu(self, evt):
        if not self.runRoutine:
            self.runRoutine = True
            self._setValveStatus(self.valveMask)
            self.iCtrl.SetLabel(self.idPumpdownRoutine, 'Stop Vaporizer Pumpdown Routine')
            self.iOutletValve.Enable(False)
        else:
            self.runRoutine = False
            self.valveSeqIdx = 0
            self.reqTime, self.valveMask = VALVE_SEQ[self.valveSeqIdx]
            self._setValveStatus(0)
            self.textCtrlElapsedTime.SetValue('0.00')
            self.iCtrl.SetLabel(self.idPumpdownRoutine, 'Start Vaporizer Pumpdown Routine')
            self.iOutletValve.Enable(True)

    def onStepTimer(self, evt):
        elapsedTime = float(self.textCtrlElapsedTime.GetValue())
        if self.runRoutine:
            if elapsedTime < self.reqTime:
                self.textCtrlElapsedTime.SetValue('%.2f' % (elapsedTime + DISP_TIME_PRECISION))
            else:
                self.valveSeqIdx = (self.valveSeqIdx + 1) % 7
                self.reqTime, self.valveMask = VALVE_SEQ[self.valveSeqIdx]
                self._setValveStatus(self.valveMask)
                self.textCtrlElapsedTime.SetValue('0.00')
        elif self.openOutlet:
            self.textCtrlElapsedTime.SetValue('%.2f' % (elapsedTime + DISP_TIME_PRECISION))
        else:
            return

    def onClose(self, evt):
        try:
            self._setValveStatus(0)
            time.sleep(0.1)
        except:
            pass

        sys.exit(0)
        self.Destroy()

    def onAboutMenu(self, evt):
        d = wx.MessageDialog(None, 'Copyright 1999-2009 Picarro Inc. All rights reserved.\n\nVersion: 0.01\n\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.', 'About Vaporizer Cleaner', wx.OK)
        d.ShowModal()
        d.Destroy()
        return

    def _setValveStatus(self, mask):
        self.DriverRpc.setValveMask(mask)
        for i in range(3):
            if mask & 1 << i:
                self.textCtrlValve[i].SetValue('Open')
            else:
                self.textCtrlValve[i].SetValue('Closed')


if __name__ == '__main__':
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = VaporizerCleaner(None, -1, '')
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()