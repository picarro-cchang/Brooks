import os
import sys
import time
import wx
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER
from Host.Coordinator.CoordinatorParamGui import InitialParamDialogGui


PARAM_LIST = [("start", "Starting Inlet Value", "10000"),
              ("end", "Target Inlet Value", "50000"),
              ("increment", "Inlet Value Increment", "1000"),
              ("incrementTime", "Increment Time Interval (second)", "1"),
              ]

DriverRpc  = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "AutoThresStats")
    
if __name__ == "__main__" :
    guiParamDict = {}
    app=wx.App()
    app.MainLoop()
    dlg = InitialParamDialogGui(PARAM_LIST, None, -1, "")
    dlg.SetTitle("Flow Controller for G2000")
    getParamVals = (dlg.ShowModal() == wx.ID_OK)
    #print dlg.nameList
    for idx in range(len(PARAM_LIST)):
        if getParamVals:
            guiParamDict[dlg.nameList[idx]] = dlg.textCtrlList[idx].GetValue()
        else:
            guiParamDict[dlg.nameList[idx]] = PARAM_LIST[idx][2]
    dlg.Destroy()
    start = int(guiParamDict["start"])
    end = int(guiParamDict["end"])
    increment = int(guiParamDict["increment"])
    incrementTime = float(guiParamDict["incrementTime"])
    
    d = wx.MessageDialog(None,"Start flow control now?", "Confirmation", \
        style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
    startFlow = (d.ShowModal() == wx.ID_YES)
    d.Destroy()
    if not startFlow:
        sys.exit()
            
    # Set outlet valve control
    DriverRpc.wrDasReg("VALVE_CNTRL_STATE_REGISTER", 1)
    
    # Open inlet valve gradually
    inletValList = range(start, end, increment)
    if inletValList[-1] != end:
        inletValList.append(end)
    dlg = wx.ProgressDialog("Flow Controller Progress", "Flow Controller Running", maximum = len(inletValList))
    count = 0
    for inletVal in inletValList:
        DriverRpc.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER", inletVal)
        time.sleep(incrementTime)
        count += 1
        dlg.Update(count)
    dlg.Destroy()

    
