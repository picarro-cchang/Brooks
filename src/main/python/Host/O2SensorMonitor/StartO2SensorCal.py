import wx
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_O2_SENSOR_MONITOR

app = wx.PySimpleApp()
try:
    O2Sensor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_O2_SENSOR_MONITOR,
                                        "StartO2SensorCalibration", IsDontCareConnection=False)
    if O2Sensor:
        O2Sensor.showGui()
except:
    d = wx.MessageDialog(None, "O2 sensor monitor is NOT running!", "Error", style=wx.OK | wx.ICON_ERROR)
    d.ShowModal()
    d.Destroy()