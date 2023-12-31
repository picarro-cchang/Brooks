# -*- coding: iso-8859-15 -*-
# generated by wxGlade HG on Sun Oct 30 16:28:27 2011

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
from Host.Common.GraphPanel import GraphPanel
# end wxGlade


class StreamDisplayPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: StreamDisplayPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.graph_panel_stream_display = GraphPanel(self, -1)
        self.panel_stream_display = wx.Panel(self, -1)
        self.label_data_source = wx.StaticText(self.panel_stream_display, -1, "Data Source")
        self.combo_box_data_source = wx.ComboBox(self.panel_stream_display, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.label_filter = wx.StaticText(self.panel_stream_display, -1, "Filter")
        self.combo_box_filter = wx.ComboBox(self.panel_stream_display, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_COMBOBOX, self.onDataSourceChange, self.combo_box_data_source)
        self.Bind(wx.EVT_COMBOBOX, self.onFilterChange, self.combo_box_filter)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: StreamDisplayPanelGui.__set_properties
        self.panel_stream_display.SetMinSize((200, -1))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: StreamDisplayPanelGui.__do_layout
        sizer_stream_display1 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_controls = wx.FlexGridSizer(2, 2, 5, 5)
        sizer_stream_display1.Add(self.graph_panel_stream_display, 1, wx.EXPAND, 0)
        grid_sizer_controls.Add(self.label_data_source, 0, wx.ALL, 5)
        grid_sizer_controls.Add(self.combo_box_data_source, 0, wx.ALL | wx.EXPAND, 5)
        grid_sizer_controls.Add(self.label_filter, 0, wx.ALL, 5)
        grid_sizer_controls.Add(self.combo_box_filter, 0, wx.ALL | wx.EXPAND, 5)
        self.panel_stream_display.SetSizer(grid_sizer_controls)
        grid_sizer_controls.AddGrowableCol(1)
        sizer_stream_display1.Add(self.panel_stream_display, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer_stream_display1)
        sizer_stream_display1.Fit(self)
        # end wxGlade

    def onDataSourceChange(self, event):  # wxGlade: StreamDisplayPanelGui.<event_handler>
        print "Event handler `onDataSourceChange' not implemented!"
        event.Skip()

    def onFilterChange(self, event):  # wxGlade: StreamDisplayPanelGui.<event_handler>
        print "Event handler `onFilterChange' not implemented!"
        event.Skip()


# end of class StreamDisplayPanelGui
