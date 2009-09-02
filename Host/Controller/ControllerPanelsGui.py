#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Tue Sep 01 20:38:58 2009

import wx

# begin wxGlade: extracode
from Host.Common.GraphPanel import GraphPanel
from Host.Common.GraphPanel import GraphPanel
from Host.Common.GraphPanel import GraphPanel
from Host.Common.GuiWidgets import CheckIndicator

from Host.Common.GuiWidgets import CheckIndicator

# end wxGlade



class LaserPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: LaserPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.temperatureGraph = GraphPanel(self, -1)
        self.tecGraph = GraphPanel(self, -1)
        self.currentGraph = GraphPanel(self, -1)
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
        sizer_2.Add(self.clearButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_2.Add((20, 20), 1, 0, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        # end wxGlade

    def onClear(self, event): # wxGlade: LaserPanelGui.<event_handler>
        print "Event handler `onClear' not implemented!"
        event.Skip()

# end of class LaserPanelGui


class CommandLogPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: CommandLogPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.panel_2 = wx.Panel(self.panel_1, -1)
        self.streamFileCheckbox = wx.CheckBox(self.panel_1, -1, "Stream File")
        self.streamFileTextCtrl = wx.TextCtrl(self.panel_1, -1, "")
        self.panel_3 = wx.Panel(self, -1)
        self.panel_4 = wx.Panel(self, -1)
        self.panel_5 = wx.Panel(self, -1)
        self.panel_6 = wx.Panel(self, -1)
        self.panel_7 = wx.Panel(self, -1)
        self.logListCtrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.onStreamFileCheck, self.streamFileCheckbox)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: CommandLogPanelGui.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: CommandLogPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridSizer(2, 3, 0, 0)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(self.panel_2, 1, wx.EXPAND, 0)
        sizer_3.Add(self.streamFileCheckbox, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_3.Add(self.streamFileTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_2.Add(sizer_3, 0, wx.ALL|wx.EXPAND, 6)
        self.panel_1.SetSizer(sizer_2)
        grid_sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.panel_3, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.panel_4, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.panel_5, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.panel_6, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.panel_7, 1, wx.EXPAND, 0)
        sizer_1.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        sizer_1.Add(self.logListCtrl, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        # end wxGlade

    def onStreamFileCheck(self, event): # wxGlade: CommandLogPanelGui.<event_handler>
        print "Event handler `onStreamFileCheck' not implemented!"
        event.Skip()

# end of class CommandLogPanelGui


class HotBoxPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: HotBoxPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.temperatureGraph = GraphPanel(self, -1)
        self.tecGraph = GraphPanel(self, -1)
        self.heaterGraph = GraphPanel(self, -1)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.cavityTemperatureCheckbox = wx.CheckBox(self.panel_1, -1, "Cavity temperature")
        self.heatsinkTemperatureCheckbox = wx.CheckBox(self.panel_1, -1, "Heatsink temperature")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.cavityTemperatureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onWaveformSelectChanged, self.heatsinkTemperatureCheckbox)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: HotBoxPanelGui.__set_properties
        self.cavityTemperatureCheckbox.SetValue(1)
        self.heatsinkTemperatureCheckbox.SetValue(1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: HotBoxPanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.temperatureGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.tecGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.heaterGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 15)
        sizer_3.Add(self.cavityTemperatureCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_3.Add(self.heatsinkTemperatureCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, 0, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        # end wxGlade

    def onClear(self, event): # wxGlade: HotBoxPanelGui.<event_handler>
        print "Event handler `onClear' not implemented!"
        event.Skip()

    def onWaveformSelectChanged(self, event): # wxGlade: HotBoxPanelGui.<event_handler>
        print "Event handler `onWaveformSelectChanged' not implemented!"
        event.Skip()

# end of class HotBoxPanelGui


class RingdownPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: RingdownPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.sizer_4_staticbox = wx.StaticBox(self.panel_1, -1, "Loss Type")
        self.ringdownGraph = GraphPanel(self, -1)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.uncorrectedCheckBox = wx.CheckBox(self.panel_1, -1, "Uncorrected")
        self.correctedCheckBox = wx.CheckBox(self.panel_1, -1, "Corrected")
        self.graphTypeRadioBox = wx.RadioBox(self.panel_1, -1, "Select Graph Type", choices=["Loss vs Wavenumber", "Loss vs Time", "Loss vs Ratio 1", "Loss vs Ratio 2", "Ratio vs Wavenumber", "Tuner vs Wavenumber", "Tuner vs Time", "Tuner vs Ratio 1", "Tuner vs Ratio 2", "Wavenumber vs Time", "IL(fine) vs Wavenumber", "IL(fine) vs Time"], majorDimension=4, style=wx.RA_SPECIFY_ROWS)
        self.panel_2 = wx.Panel(self.panel_1, -1)

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
        sizer_4 = wx.StaticBoxSizer(self.sizer_4_staticbox, wx.VERTICAL)
        sizer_1.Add(self.ringdownGraph, 1, wx.EXPAND, 0)
        sizer_3.Add(self.clearButton, 0, wx.ALL, 10)
        sizer_4.Add(self.uncorrectedCheckBox, 0, wx.TOP|wx.BOTTOM, 3)
        sizer_4.Add(self.correctedCheckBox, 0, wx.TOP|wx.BOTTOM, 3)
        sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 0, wx.ALL|wx.EXPAND, 10)
        sizer_2.Add(self.graphTypeRadioBox, 0, wx.ALL, 10)
        sizer_2.Add(self.panel_2, 1, wx.EXPAND, 10)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        # end wxGlade

    def onClear(self, event): # wxGlade: RingdownPanelGui.<event_handler>
        print "Event handler `onClear' not implemented!"
        event.Skip()

    def onSelectLossType(self, event): # wxGlade: RingdownPanelGui.<event_handler>
        print "Event handler `onSelectLossType' not implemented!"
        event.Skip()

    def onSelectGraphType(self, event): # wxGlade: RingdownPanelGui.<event_handler>
        print "Event handler `onSelectGraphType' not implemented!"
        event.Skip()

# end of class RingdownPanelGui


class WarmBoxPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: WarmBoxPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.temperatureGraph = GraphPanel(self, -1)
        self.tecGraph = GraphPanel(self, -1)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.etalonTemperatureCheckbox = wx.CheckBox(self.panel_1, -1, "Etalon temperature")
        self.warmBoxTemperatureCheckbox = wx.CheckBox(self.panel_1, -1, "Warm box temperature")
        self.heatsinkTemperatureCheckbox = wx.CheckBox(self.panel_1, -1, "Heatsink temperature")

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
        sizer_2.Add(self.clearButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 15)
        sizer_3.Add(self.etalonTemperatureCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_3.Add(self.warmBoxTemperatureCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_3.Add(self.heatsinkTemperatureCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(sizer_3, 0, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        # end wxGlade

    def onClear(self, event): # wxGlade: WarmBoxPanelGui.<event_handler>
        print "Event handler `onClear' not implemented!"
        event.Skip()

    def onWaveformSelectChanged(self, event): # wxGlade: WarmBoxPanelGui.<event_handler>
        print "Event handler `onWaveformSelectChanged' not implemented!"
        event.Skip()

# end of class WarmBoxPanelGui


class WlmPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: WlmPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.photocurrentGraph = GraphPanel(self, -1)
        self.ratioGraph = GraphPanel(self, -1)
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
        sizer_2.Add(self.clearButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 15)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        # end wxGlade

    def onClear(self, event): # wxGlade: WlmPanelGui.<event_handler>
        print "Event handler `onClear' not implemented!"
        event.Skip()

# end of class WlmPanelGui


class PressurePanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: PressurePanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.sizer_16_staticbox = wx.StaticBox(self.panel_1, -1, "Solenoid valve states")
        self.pressureGraph = GraphPanel(self, -1)
        self.propValveGraph = GraphPanel(self, -1)
        self.clearButton = wx.Button(self.panel_1, wx.ID_CLEAR, "")
        self.ambientPressureCheckbox = wx.CheckBox(self.panel_1, -1, "Ambient pressure")
        self.cavityPressureCheckbox = wx.CheckBox(self.panel_1, -1, "Cavity pressure")
        self.inletValveCheckbox = wx.CheckBox(self.panel_1, -1, "Inlet valve")
        self.outletValveCheckbox = wx.CheckBox(self.panel_1, -1, "Outlet valve")
        self.valve1State = CheckIndicator(self.panel_1, -1, "Valve 1")
        self.valve2State = CheckIndicator(self.panel_1, -1, "Valve 2")
        self.valve3State = CheckIndicator(self.panel_1, -1, "Valve 3")
        self.valve4State = CheckIndicator(self.panel_1, -1, "Valve 4")
        self.valve5State = CheckIndicator(self.panel_1, -1, "Valve 5")
        self.valve6State = CheckIndicator(self.panel_1, -1, "Valve 6")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)
        self.Bind(wx.EVT_CHECKBOX, self.onPressureWaveformSelectChanged, self.ambientPressureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onPressureWaveformSelectChanged, self.cavityPressureCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onValveWaveformSelectChanged, self.inletValveCheckbox)
        self.Bind(wx.EVT_CHECKBOX, self.onValveWaveformSelectChanged, self.outletValveCheckbox)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: PressurePanelGui.__set_properties
        self.ambientPressureCheckbox.SetValue(1)
        self.cavityPressureCheckbox.SetValue(1)
        self.inletValveCheckbox.SetValue(1)
        self.outletValveCheckbox.SetValue(1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: PressurePanelGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_16 = wx.StaticBoxSizer(self.sizer_16_staticbox, wx.HORIZONTAL)
        grid_sizer_2 = wx.GridSizer(2, 3, 0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.pressureGraph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.propValveGraph, 1, wx.EXPAND, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 15)
        sizer_3.Add(self.ambientPressureCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_3.Add(self.cavityPressureCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(sizer_3, 0, wx.EXPAND, 0)
        sizer_4.Add(self.inletValveCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_4.Add(self.outletValveCheckbox, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
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
        # end wxGlade

    def onClear(self, event): # wxGlade: PressurePanelGui.<event_handler>
        print "Event handler `onClear' not implemented!"
        event.Skip()

    def onPressureWaveformSelectChanged(self, event): # wxGlade: PressurePanelGui.<event_handler>
        print "Event handler `onPressureWaveformSelectChanged' not implemented!"
        event.Skip()

    def onValveWaveformSelectChanged(self, event): # wxGlade: PressurePanelGui.<event_handler>
        print "Event handler `onValveWaveformSelectChanged' not implemented!"
        event.Skip()

# end of class PressurePanelGui


class StatsPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: StatsPanelGui.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.lossGraph = GraphPanel(self, -1)
        self.waveNumberGraph = GraphPanel(self, -1)
        self.ratio1Graph = GraphPanel(self, -1)
        self.ratio2Graph = GraphPanel(self, -1)
        self.startStopButton = wx.Button(self.panel_1, -1, "&Start")
        self.label_1 = wx.StaticText(self.panel_1, -1, "Ringdowns", style=wx.ALIGN_RIGHT)
        self.ringdownsTextCtrl = wx.TextCtrl(self.panel_1, -1, "")
        self.label_2 = wx.StaticText(self.panel_1, -1, "Mean loss (ppm/cm)", style=wx.ALIGN_RIGHT)
        self.meanLossTextCtrl = wx.TextCtrl(self.panel_1, -1, "")
        self.label_3 = wx.StaticText(self.panel_1, -1, "Shot-to-shot (%)", style=wx.ALIGN_RIGHT)
        self.shotToShotTextCtrl = wx.TextCtrl(self.panel_1, -1, "")
        self.label_4 = wx.StaticText(self.panel_1, -1, "Rate (rd/s)", style=wx.ALIGN_RIGHT)
        self.rateTextCtrl = wx.TextCtrl(self.panel_1, -1, "")
        self.label_5 = wx.StaticText(self.panel_1, -1, "Freq StdDev (MHz)", style=wx.ALIGN_RIGHT)
        self.freqStdDevTextCtrl = wx.TextCtrl(self.panel_1, -1, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onStartStop, self.startStopButton)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: StatsPanelGui.__set_properties
        self.startStopButton.SetDefault()
        self.ringdownsTextCtrl.SetMinSize((60, -1))
        self.ringdownsTextCtrl.Enable(False)
        self.meanLossTextCtrl.SetMinSize((60, -1))
        self.meanLossTextCtrl.Enable(False)
        self.shotToShotTextCtrl.SetMinSize((60, -1))
        self.shotToShotTextCtrl.Enable(False)
        self.rateTextCtrl.SetMinSize((60, -1))
        self.rateTextCtrl.Enable(False)
        self.freqStdDevTextCtrl.SetMinSize((60, -1))
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
        sizer_2.Add(self.startStopButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_2.Add(self.label_1, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.ringdownsTextCtrl, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.label_2, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.meanLossTextCtrl, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.label_3, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.shotToShotTextCtrl, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.label_4, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.rateTextCtrl, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.label_5, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.freqStdDevTextCtrl, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        # end wxGlade

    def onStartStop(self, event): # wxGlade: StatsPanelGui.<event_handler>
        print "Event handler `onStartStop' not implemented!"
        event.Skip()

# end of class StatsPanelGui


