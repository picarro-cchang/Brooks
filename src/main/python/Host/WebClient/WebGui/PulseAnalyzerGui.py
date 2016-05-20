#!/usr/bin/env python
# File History:
# 09-07-28 Alex  Created file

import wx

class PulseAnalyzerGui(wx.Dialog):
    def __init__(self, paramTupleList, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.panel_2 = wx.Panel(self, -1)
        self.nameList = []
        self.labelList =[]
        self.textCtrlList = []
        self.numParams = len(paramTupleList)
        for name, label, default in paramTupleList:
            self.nameList.append(name)
            self.labelList.append(wx.StaticText(self.panel_2, -1, label))
            self.textCtrlList.append(wx.TextCtrl(self.panel_2, -1, default))
        self.okButton = wx.Button(self.panel_1, wx.ID_OK, "")
        self.cancelButton = wx.Button(self.panel_1, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("Pulse Analyzer Parameters")
        for textCtrl in self.textCtrlList:
            textCtrl.SetMinSize((200, -1))

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.FlexGridSizer(self.numParams, 2, 10, 10)
        grid_sizer_1.Add(self.labelList[0], 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.textCtrlList[0], 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 10)
        for idx in range(1,self.numParams):
            grid_sizer_1.Add(self.labelList[idx], 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)
            grid_sizer_1.Add(self.textCtrlList[idx], 1, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 10)
        self.panel_2.SetSizer(grid_sizer_1)
        grid_sizer_1.AddGrowableCol(1)
        sizer_1.Add(self.panel_2, 1, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 1, 0, 0)
        sizer_2.Add(self.okButton, 0, wx.TOP|wx.BOTTOM, 15)
        sizer_2.Add((20, 40), 0, 0, 0)
        sizer_2.Add(self.cancelButton, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 15)
        #sizer_2.Add((20, 20), 1, 0, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    paramTupleList = [("co2Thres", "CO2 Threshold", "500.0"), ("ch4Thres", "CH4 Threshold", "1.0"), ("waitTime", "Wait Time (seconds)", "5"), ("triggerTime", "Trigger Time (seconds)", "60"), ("bufferSize", "Buffer Size", "20")]
    dlg = PulseAnalyzerGui(paramTupleList, None, -1, "")
    app.SetTopWindow(dlg)
    getParamVals = (dlg.ShowModal() == wx.ID_OK)
    resDict = {}
    if getParamVals:
        for idx in range(len(paramTupleList)):
            resDict[dlg.nameList[idx]] = dlg.textCtrlList[idx].GetValue()
        print resDict
        dlg.Destroy()
    else:
        pass
    dlg.Destroy()
    app.MainLoop()