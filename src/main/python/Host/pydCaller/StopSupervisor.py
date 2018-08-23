import wx
from Host.Common.StopSupervisor import StopSupervisor, HandleCommandSwitches

if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    shutDownOption = HandleCommandSwitches()
    frame = StopSupervisor(None, -1, "")
    if shutDownOption == -1:
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()
    else:
        frame.Stop(shutDownOption)