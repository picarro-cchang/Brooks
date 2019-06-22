#!/usr/bin/env python
# -*- coding: ISO-8859-15 -*-
#
# generated by wxGlade 0.7.2 on Fri Feb 24 15:41:24 2017
#

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
from Host.Common.GraphPanel import GraphPanel
from Host.Common.GraphPanel import GraphPanel
from Host.Common.GraphPanel import GraphPanel
from Host.Common.GuiWidgets import CheckIndicator
# end wxGlade


class LaserPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: LaserPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.temperatureGraph = GraphPanel(self, wx.ID_ANY)
        self.tecGraph = GraphPanel(self, wx.ID_ANY)
        self.currentGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: LaserPanelGui.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: LaserPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.temperatureGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.tecGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.currentGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        sizer_2.Add((20, 20), 1, 0, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: LaserPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

# end of class LaserPanelGui

class CommandLogPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: CommandLogPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.startEngineButton = wx.Button(self.panel_1, wx.ID_ANY, "Start Engine")
        self.laser1State = CheckIndicator(self.panel_1, wx.ID_ANY, "Laser 1")
        self.laser2State = CheckIndicator(self.panel_1, wx.ID_ANY, "Laser 2")
        self.laser3State = CheckIndicator(self.panel_1, wx.ID_ANY, "Laser 3")
        self.laser4State = CheckIndicator(self.panel_1, wx.ID_ANY, "Laser 4/SOA")
        self.warmBoxState = CheckIndicator(self.panel_1, wx.ID_ANY, "Warm Box")
        self.hotBoxState = CheckIndicator(self.panel_1, wx.ID_ANY, "Hot Box")
        self.streamFileCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Stream File")
        self.streamFileTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.loadCalibrationButton = wx.Button(self.panel_2, wx.ID_ANY, "Load Calibration")
        self.label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "Warm Box")
        self.warmBoxCalFileTextCtrl = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
        self.label_2 = wx.StaticText(self.panel_2, wx.ID_ANY, "Hot Box")
        self.hotBoxCalFileTextCtrl = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
        self.panel_3 = wx.Panel(self, wx.ID_ANY)
        self.startAcquisitionButton = wx.Button(self.panel_3, wx.ID_ANY, "Start Acquisition")
        self.label_3 = wx.StaticText(self.panel_3, wx.ID_ANY, "Sequence")
        self.seqTextCtrl = wx.TextCtrl(self.panel_3, wx.ID_ANY, "")
        self.logListCtrl = wx.ListCtrl(self, wx.ID_ANY, style=wx.BORDER_SUNKEN | wx.LC_REPORT)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onStartEngine, self.startEngineButton)
        self.Bind(wx.EVT_CHECKBOX, self.onStreamFileCheck, self.streamFileCheckbox)
        self.Bind(wx.EVT_BUTTON, self.onLoadCalibration, self.loadCalibrationButton)
        self.Bind(wx.EVT_BUTTON, self.onStartAcquisition, self.startAcquisitionButton)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: CommandLogPanelGui.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: CommandLogPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_11 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Log"), wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_9 = wx.BoxSizer(wx.VERTICAL)
        sizer_10 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_3 = wx.FlexGridSizer(2, 2, 5, 5)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.GridSizer(3, 2, 0, 0)
        sizer_4.Add(self.startEngineButton, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_1.Add(self.laser1State, 1, wx.BOTTOM | wx.TOP, 5)
        grid_sizer_1.Add(self.laser2State, 1, wx.BOTTOM | wx.TOP, 5)
        grid_sizer_1.Add(self.laser3State, 1, wx.BOTTOM | wx.TOP, 5)
        grid_sizer_1.Add(self.laser4State, 1, wx.BOTTOM | wx.TOP, 5)
        grid_sizer_1.Add(self.warmBoxState, 1, wx.BOTTOM | wx.TOP, 5)
        grid_sizer_1.Add(self.hotBoxState, 1, wx.BOTTOM | wx.TOP, 5)
        sizer_4.Add(grid_sizer_1, 0, wx.EXPAND | wx.LEFT, 10)
        sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)
        sizer_5.Add(self.streamFileCheckbox, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(self.streamFileTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_3.Add(sizer_5, 0, wx.ALL | wx.EXPAND, 6)
        self.panel_1.SetSizer(sizer_3)
        sizer_2.Add(self.panel_1, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 25)
        sizer_6.Add(self.loadCalibrationButton, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_3.Add(self.label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.warmBoxCalFileTextCtrl, 0, wx.EXPAND, 0)
        grid_sizer_3.Add(self.label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.hotBoxCalFileTextCtrl, 0, wx.EXPAND, 0)
        grid_sizer_3.AddGrowableCol(1)
        sizer_6.Add(grid_sizer_3, 1, wx.EXPAND, 0)
        self.panel_2.SetSizer(sizer_6)
        sizer_2.Add(self.panel_2, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 25)
        sizer_9.Add(self.startAcquisitionButton, 1, wx.ALL | wx.EXPAND, 5)
        sizer_10.Add(self.label_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 0)
        sizer_10.Add(self.seqTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_9.Add(sizer_10, 0, wx.EXPAND, 6)
        self.panel_3.SetSizer(sizer_9)
        sizer_2.Add(self.panel_3, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 25)
        sizer_1.Add(sizer_2, 0, wx.EXPAND | wx.TOP, 20)
        sizer_11.Add(self.logListCtrl, 1, wx.EXPAND, 0)
        sizer_1.Add(sizer_11, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onStartEngine(self, event):  # wxGlade: CommandLogPanelGui.<event_handler>
        print "Event handler 'onStartEngine' not implemented!"
        event.Skip()

    def onStreamFileCheck(self, event):  # wxGlade: CommandLogPanelGui.<event_handler>
        print "Event handler 'onStreamFileCheck' not implemented!"
        event.Skip()

    def onLoadCalibration(self, event):  # wxGlade: CommandLogPanelGui.<event_handler>
        print "Event handler 'onLoadCalibration' not implemented!"
        event.Skip()

    def onStartAcquisition(self, event):  # wxGlade: CommandLogPanelGui.<event_handler>
        print "Event handler 'onStartAcquisition' not implemented!"
        event.Skip()

# end of class CommandLogPanelGui

class HotBoxPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: HotBoxPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.temperatureGraph = GraphPanel(self, wx.ID_ANY)
        self.tecGraph = GraphPanel(self, wx.ID_ANY)
        self.heaterGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.cavityTemperatureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity Temperature")
        self.heatsinkTemperatureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Heatsink temperature")
        self.dasTemperatureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "DAS temperature")
        self.cavityTemperatureCheckbox_1 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity temperature 1")
        self.cavityTemperatureCheckbox_2 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity temperature 2")
        self.cavityTemperatureCheckbox_3 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity temperature 3")
        self.cavityTemperatureCheckbox_4 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity temperature 4")
        self.cavity2TemperatureCheckbox_1 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity2 temperature 1")
        self.cavity2TemperatureCheckbox_2 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity2 temperature 2")
        self.cavity2TemperatureCheckbox_3 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity2 temperature 3")
        self.cavity2TemperatureCheckbox_4 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity2 temperature 4")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavityTemperatureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.heatsinkTemperatureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.dasTemperatureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavityTemperatureCheckbox_1)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavityTemperatureCheckbox_2)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavityTemperatureCheckbox_3)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavityTemperatureCheckbox_4)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavity2TemperatureCheckbox_1)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavity2TemperatureCheckbox_2)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavity2TemperatureCheckbox_3)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavity2TemperatureCheckbox_4)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: HotBoxPanelGui.__set_properties
        self.cavityTemperatureCheckbox.SetValue(1)
        self.heatsinkTemperatureCheckbox.SetValue(1)
        self.dasTemperatureCheckbox.SetValue(1)
        self.cavityTemperatureCheckbox_1.SetValue(1)
        self.cavityTemperatureCheckbox_2.SetValue(1)
        self.cavityTemperatureCheckbox_3.SetValue(1)
        self.cavityTemperatureCheckbox_4.SetValue(1)
        self.cavity2TemperatureCheckbox_1.SetValue(1)
        self.cavity2TemperatureCheckbox_2.SetValue(1)
        self.cavity2TemperatureCheckbox_3.SetValue(1)
        self.cavity2TemperatureCheckbox_4.SetValue(1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: HotBoxPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3_copy = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.temperatureGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.tecGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.heaterGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        sizer_3.Add(self.cavityTemperatureCheckbox, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.heatsinkTemperatureCheckbox, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.dasTemperatureCheckbox, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_3_copy.Add(self.cavityTemperatureCheckbox_1, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3_copy.Add(self.cavityTemperatureCheckbox_2, 0, wx.BOTTOM | wx.FIXED_MINSIZE | wx.LEFT | wx.TOP, 5)
        sizer_3_copy.Add(self.cavityTemperatureCheckbox_3, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3_copy.Add(self.cavityTemperatureCheckbox_4, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3_copy.Add(self.cavity2TemperatureCheckbox_1, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3_copy.Add(self.cavity2TemperatureCheckbox_2, 0, wx.BOTTOM | wx.FIXED_MINSIZE | wx.LEFT | wx.TOP, 5)
        sizer_3_copy.Add(self.cavity2TemperatureCheckbox_3, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3_copy.Add(self.cavity2TemperatureCheckbox_4, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_2.Add(sizer_3_copy, 1, 0, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, 0, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: HotBoxPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

    def onWaveformSelectChanged(self, event):  # wxGlade: HotBoxPanelGui.<event_handler>
        print "Event handler 'onWaveformSelectChanged' not implemented!"
        event.Skip()

# end of class HotBoxPanelGui

class RingdownPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: RingdownPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.ringdownGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.uncorrectedCheckBox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Uncorrected")
        self.correctedCheckBox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Corrected")
        self.graphTypeRadioBox = wx.RadioBox(self.panel_1, wx.ID_ANY, "Select Graph Type", choices=["Loss vs Wavenumber", "Loss vs Time", "Loss vs Ratio 1", "Loss vs Ratio 2", "Ratio vs Wavenumber", "Tuner vs Wavenumber", "Tuner vs Time", "Tuner vs Ratio 1", "Tuner vs Ratio 2", "PZT vs Wavenumber", "PZT vs Time", "PZT vs Ratio 1", "PZT vs Ratio 2", "Wavenumber vs Time", "IL(fine) vs Wavenumber", "IL(fine) vs Time", "Loss vs IL(fine)"], majorDimension=4, style=wx.RA_SPECIFY_ROWS)
        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        self.Bind(wx.EVT_CHECKBOX, self.onSelectLossType, self.uncorrectedCheckBox)
        self.Bind(wx.EVT_CHECKBOX, self.onSelectLossType, self.correctedCheckBox)
        self.Bind(wx.EVT_RADIOBOX, self.onSelectGraphType, self.graphTypeRadioBox)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: RingdownPanelGui.__set_properties
        self.uncorrectedCheckBox.SetValue(1)
        self.graphTypeRadioBox.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: RingdownPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.StaticBoxSizer(wx.StaticBox(self.panel_1, wx.ID_ANY, "Loss Type"), wx.VERTICAL)
        sizer_1.Add(self.ringdownGraph, 1, wx.EXPAND, 0)
        sizer_3.Add(self.clearButton, 0, wx.ALL, 10)
        sizer_4.Add(self.uncorrectedCheckBox, 0, wx.BOTTOM | wx.TOP, 3)
        sizer_4.Add(self.correctedCheckBox, 0, wx.BOTTOM | wx.TOP, 3)
        sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 0, wx.ALL | wx.EXPAND, 10)
        sizer_2.Add(self.graphTypeRadioBox, 0, wx.ALL, 10)
        sizer_2.Add(self.panel_2, 1, wx.EXPAND, 10)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: RingdownPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

    def onSelectLossType(self, event):  # wxGlade: RingdownPanelGui.<event_handler>
        print "Event handler 'onSelectLossType' not implemented!"
        event.Skip()

    def onSelectGraphType(self, event):  # wxGlade: RingdownPanelGui.<event_handler>
        print "Event handler 'onSelectGraphType' not implemented!"
        event.Skip()

# end of class RingdownPanelGui

class WarmBoxPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: WarmBoxPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.temperatureGraph = GraphPanel(self, wx.ID_ANY)
        self.tecGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.etalonTemperatureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Etalon temperature")
        self.warmBoxTemperatureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Warm box temperature")
        self.heatsinkTemperatureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Heatsink temperature")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.etalonTemperatureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.warmBoxTemperatureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.heatsinkTemperatureCheckbox)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: WarmBoxPanelGui.__set_properties
        self.etalonTemperatureCheckbox.SetValue(1)
        self.warmBoxTemperatureCheckbox.SetValue(1)
        self.heatsinkTemperatureCheckbox.SetValue(1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: WarmBoxPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.temperatureGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.tecGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        sizer_3.Add(self.etalonTemperatureCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.warmBoxTemperatureCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.heatsinkTemperatureCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_2.Add(sizer_3, 0, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: WarmBoxPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

    def onWaveformSelectChanged(self, event):  # wxGlade: WarmBoxPanelGui.<event_handler>
        print "Event handler 'onWaveformSelectChanged' not implemented!"
        event.Skip()

# end of class WarmBoxPanelGui

class FilterHeaterPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: FilterHeaterPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.temperatureGraph = GraphPanel(self, wx.ID_ANY)
        self.heaterGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: FilterHeaterPanelGui.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: FilterHeaterPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.temperatureGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.heaterGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: FilterHeaterPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

# end of class FilterHeaterPanelGui

class ProcessedLossPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ProcessedLossPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.processedLossGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.processedLoss1Checkbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Processed Loss 1")
        self.processedLoss2Checkbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Processed Loss 2")
        self.processedLoss3Checkbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Processed Loss 3")
        self.processedLoss4Checkbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Processed Loss 4")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        self.Bind(wx.EVT_CHECKBOX, self.onProcessedLossChanged, self.processedLoss1Checkbox)
        self.Bind(wx.EVT_CHECKBOX, self.onProcessedLossChanged, self.processedLoss2Checkbox)
        self.Bind(wx.EVT_CHECKBOX, self.onProcessedLossChanged, self.processedLoss3Checkbox)
        self.Bind(wx.EVT_CHECKBOX, self.onProcessedLossChanged, self.processedLoss4Checkbox)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ProcessedLossPanelGui.__set_properties
        self.processedLoss1Checkbox.SetValue(1)
        self.processedLoss2Checkbox.SetValue(1)
        self.processedLoss3Checkbox.SetValue(1)
        self.processedLoss4Checkbox.SetValue(1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ProcessedLossPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.processedLossGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        sizer_3.Add(self.processedLoss1Checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.processedLoss2Checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.processedLoss3Checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.processedLoss4Checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_2.Add(sizer_3, 0, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: ProcessedLossPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

    def onProcessedLossChanged(self, event):  # wxGlade: ProcessedLossPanelGui.<event_handler>
        print "Event handler 'onProcessedLossChanged' not implemented!"
        event.Skip()

# end of class ProcessedLossPanelGui

class WlmPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: WlmPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.photocurrentGraph = GraphPanel(self, wx.ID_ANY)
        self.ratioGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: WlmPanelGui.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: WlmPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.photocurrentGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.ratioGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: WlmPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

# end of class WlmPanelGui

class PressurePanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: PressurePanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.pressureGraph = GraphPanel(self, wx.ID_ANY)
        self.propValveGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.ambientPressureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Ambient pressure")
        self.cavityPressureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity pressure")
        self.ambient2PressureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Ambient2 pressure")
        self.cavity2PressureCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Cavity2 pressure")
        self.flowRateCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Flow Rate")
        self.inletValveCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Inlet valve")
        self.outletValveCheckbox = wx.CheckBox(self.panel_1, wx.ID_ANY, "Outlet valve")
        self.valve1State = CheckIndicator(self.panel_1, wx.ID_ANY, "Valve 1")
        self.valve2State = CheckIndicator(self.panel_1, wx.ID_ANY, "Valve 2")
        self.valve3State = CheckIndicator(self.panel_1, wx.ID_ANY, "Valve 3")
        self.valve4State = CheckIndicator(self.panel_1, wx.ID_ANY, "Valve 4")
        self.valve5State = CheckIndicator(self.panel_1, wx.ID_ANY, "Valve 5")
        self.valve6State = CheckIndicator(self.panel_1, wx.ID_ANY, "Valve 6")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        self.Bind(wx.EVT_CHECKBOX, self.onPressureWaveformSelectChanged, self.ambientPressureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onPressureWaveformSelectChanged, self.cavityPressureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onPressureWaveformSelectChanged, self.ambient2PressureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onPressureWaveformSelectChanged, self.cavity2PressureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onPressureWaveformSelectChanged, self.flowRateCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onValveWaveformSelectChanged, self.inletValveCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onValveWaveformSelectChanged, self.outletValveCheckbox)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: PressurePanelGui.__set_properties
        self.cavityPressureCheckbox.SetValue(1)
        self.cavity2PressureCheckbox.SetValue(1)
        self.inletValveCheckbox.SetValue(1)
        self.outletValveCheckbox.SetValue(1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: PressurePanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_16 = wx.StaticBoxSizer(wx.StaticBox(self.panel_1, wx.ID_ANY, "Solenoid valve states"), wx.HORIZONTAL)
        grid_sizer_2 = wx.GridSizer(2, 3, 0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.pressureGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.propValveGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        sizer_3.Add(self.ambientPressureCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.cavityPressureCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.ambient2PressureCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.cavity2PressureCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_3.Add(self.flowRateCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_2.Add(sizer_3, 0, wx.EXPAND, 0)
        sizer_4.Add(self.inletValveCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_4.Add(self.outletValveCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 5)
        sizer_2.Add(sizer_4, 0, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        grid_sizer_2.Add(self.valve1State, 1, wx.EXPAND, 0)
        grid_sizer_2.Add(self.valve2State, 1, wx.EXPAND, 0)
        grid_sizer_2.Add(self.valve3State, 1, wx.EXPAND, 0)
        grid_sizer_2.Add(self.valve4State, 1, wx.EXPAND, 0)
        grid_sizer_2.Add(self.valve5State, 1, wx.EXPAND, 0)
        grid_sizer_2.Add(self.valve6State, 1, wx.EXPAND, 0)
        sizer_16.Add(grid_sizer_2, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_16, 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: PressurePanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

    def onPressureWaveformSelectChanged(self, event):  # wxGlade: PressurePanelGui.<event_handler>
        print "Event handler 'onPressureWaveformSelectChanged' not implemented!"
        event.Skip()

    def onValveWaveformSelectChanged(self, event):  # wxGlade: PressurePanelGui.<event_handler>
        print "Event handler 'onValveWaveformSelectChanged' not implemented!"
        event.Skip()

# end of class PressurePanelGui

class StatsPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: StatsPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.lossGraph = GraphPanel(self, wx.ID_ANY)
        self.waveNumberGraph = GraphPanel(self, wx.ID_ANY)
        self.ratio1Graph = GraphPanel(self, wx.ID_ANY)
        self.ratio2Graph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.startStopButton = wx.Button(self.panel_1, wx.ID_ANY, "&Start")
        self.label_ringdowns = wx.StaticText(self.panel_1, wx.ID_ANY, "Ringdowns", style=wx.ALIGN_CENTER)
        self.ringdownsTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.label_mean_loss = wx.StaticText(self.panel_1, wx.ID_ANY, "Mean loss\n(ppm/cm)", style=wx.ALIGN_CENTER)
        self.meanLossTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.label_sdev_loss = wx.StaticText(self.panel_1, wx.ID_ANY, "Loss stddev\n(ppb/cm)", style=wx.ALIGN_CENTER)
        self.stdLossTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.label_shot_to_shot = wx.StaticText(self.panel_1, wx.ID_ANY, "Shot-to-shot\n(%)", style=wx.ALIGN_CENTER)
        self.shotToShotTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.label_rate = wx.StaticText(self.panel_1, wx.ID_ANY, "Rate\n(rd/s)", style=wx.ALIGN_CENTER)
        self.rateTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.label_sensitivity = wx.StaticText(self.panel_1, wx.ID_ANY, "Sensitivity\n(ppb/cm/sqrt(Hz))", style=wx.ALIGN_CENTER)
        self.sensitivityTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.label_freq_std_dev = wx.StaticText(self.panel_1, wx.ID_ANY, "Freq StdDev\n(MHz)", style=wx.ALIGN_CENTER)
        self.freqStdDevTextCtrl = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onStartStop, self.startStopButton)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: StatsPanelGui.__set_properties
        self.startStopButton.SetMinSize((40, -1))
        self.startStopButton.SetDefault()
        self.ringdownsTextCtrl.SetMinSize((35, -1))
        self.ringdownsTextCtrl.Enable(False)
        self.meanLossTextCtrl.SetMinSize((40, -1))
        self.meanLossTextCtrl.Enable(False)
        self.stdLossTextCtrl.SetMinSize((40, -1))
        self.stdLossTextCtrl.Enable(False)
        self.shotToShotTextCtrl.SetMinSize((40, -1))
        self.shotToShotTextCtrl.Enable(False)
        self.rateTextCtrl.SetMinSize((40, -1))
        self.rateTextCtrl.Enable(False)
        self.sensitivityTextCtrl.SetMinSize((40, -1))
        self.sensitivityTextCtrl.Enable(False)
        self.freqStdDevTextCtrl.SetMinSize((40, -1))
        self.freqStdDevTextCtrl.Enable(False)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: StatsPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.GridSizer(2, 2, 0, 0)
        grid_sizer_1.Add(self.lossGraph, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.waveNumberGraph, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.ratio1Graph, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.ratio2Graph, 1, wx.EXPAND, 0)
        sizer_1.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        sizer_2.Add(self.startStopButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        sizer_2.Add(self.label_ringdowns, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.ringdownsTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_2.Add(self.label_mean_loss, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.meanLossTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_2.Add(self.label_sdev_loss, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.stdLossTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_2.Add(self.label_shot_to_shot, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.shotToShotTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_2.Add(self.label_rate, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.rateTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_2.Add(self.label_sensitivity, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.sensitivityTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_2.Add(self.label_freq_std_dev, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.freqStdDevTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def onStartStop(self, event):  # wxGlade: StatsPanelGui.<event_handler>
        print "Event handler 'onStartStop' not implemented!"
        event.Skip()

# end of class StatsPanelGui

class AccelerometerPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: AccelerometerPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.accelxGraph = GraphPanel(self, wx.ID_ANY)
        self.accelyGraph = GraphPanel(self, wx.ID_ANY)
        self.accelzGraph = GraphPanel(self, wx.ID_ANY)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: AccelerometerPanelGui.__set_properties
        self.SetSize((472, 320))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: AccelerometerPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.accelxGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.accelyGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.accelzGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        sizer_2.Add((20, 15), 1, 0, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, 0, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def onClear(self, event):  # wxGlade: AccelerometerPanelGui.<event_handler>
        print "Event handler 'onClear' not implemented!"
        event.Skip()

# end of class AccelerometerPanelGui
