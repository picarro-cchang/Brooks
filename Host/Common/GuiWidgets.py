#!/usr/bin/python
#
# File Name: GuiWidgets.py
# Purpose: Defines custom widgets for use in GUIs
#
# Notes:
#
# File History:
# 09-08-29 sze  Initial version
import wx

class CheckIndicator(wx.CheckBox):
    """ Use a checkbox as a read-only state indicator. Disable user interaction """
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.CHK_3STATE
        wx.CheckBox.__init__(self, *args, **kwds)
        self.Bind(wx.EVT_LEFT_UP, self.Pass)
        self.Bind(wx.EVT_LEFT_DOWN, self.Pass)
        self.Bind(wx.EVT_MOTION, self.Pass)
        self.Bind(wx.EVT_LEFT_DCLICK, self.Pass)
        self.SetForegroundColour(wx.BLUE)

    def Pass(self,e):
        pass
    