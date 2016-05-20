APP_NAME = "ValveSequencer"

import wx
from Host.ValveSequencer.ValveSequencer import HandleCommandSwitches, ValveSequencer
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    #Get and handle the command line options...
    (configFile, showAtStart) = HandleCommandSwitches()
    Log("%s started." % APP_NAME, Level = 0)
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = ValveSequencer(configFile, showAtStart, None, -1, "")
    app.SetTopWindow(frame)
    app.MainLoop()
    Log("Exiting program")