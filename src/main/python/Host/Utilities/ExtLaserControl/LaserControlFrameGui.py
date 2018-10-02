# -*- coding: UTF8 -*-
#
# generated by wxGlade 0.7.0 on Sun Mar 01 10:17:30 2015
#

import wx
# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
from LaserControlPanel import LaserControlPanel
# end wxGlade


class LaserControlFrameGui(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: LaserControlFrameGui.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.notebook = wx.Notebook(self, wx.ID_ANY)
        self.notebook_pane_1 = wx.Panel(self.notebook, wx.ID_ANY)
        self.laser1_control_panel = LaserControlPanel(self.notebook_pane_1, wx.ID_ANY)
        self.notebook_pane_2 = wx.Panel(self.notebook, wx.ID_ANY)
        self.laser2_control_panel = LaserControlPanel(self.notebook_pane_2, wx.ID_ANY)
        self.notebook_pane_3 = wx.Panel(self.notebook, wx.ID_ANY)
        self.laser3_control_panel = LaserControlPanel(self.notebook_pane_3, wx.ID_ANY)
        self.notebook_pane_4 = wx.Panel(self.notebook, wx.ID_ANY)
        self.laser4_control_panel = LaserControlPanel(self.notebook_pane_4, wx.ID_ANY)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: LaserControlFrameGui.__set_properties
        self.SetTitle(_("Laser Current Waveform Controller"))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: LaserControlFrameGui.__do_layout
        sizer_main = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pane_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pane_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pane_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pane_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pane_1.Add(self.laser1_control_panel, 1, wx.EXPAND, 0)
        self.notebook_pane_1.SetSizer(sizer_pane_1)
        sizer_pane_2.Add(self.laser2_control_panel, 1, wx.EXPAND, 0)
        self.notebook_pane_2.SetSizer(sizer_pane_2)
        sizer_pane_3.Add(self.laser3_control_panel, 1, wx.EXPAND, 0)
        self.notebook_pane_3.SetSizer(sizer_pane_3)
        sizer_pane_4.Add(self.laser4_control_panel, 1, wx.EXPAND, 0)
        self.notebook_pane_4.SetSizer(sizer_pane_4)
        self.notebook.AddPage(self.notebook_pane_1, _("Laser 1"))
        self.notebook.AddPage(self.notebook_pane_2, _("Laser 2"))
        self.notebook.AddPage(self.notebook_pane_3, _("Laser 3"))
        self.notebook.AddPage(self.notebook_pane_4, _("Laser 4"))
        sizer_main.Add(self.notebook, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_main)
        sizer_main.Fit(self)
        self.Layout()
        # end wxGlade

# end of class LaserControlFrameGui