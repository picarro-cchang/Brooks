# PlotControlPanelGui.py
#
import wx


class PlotControlPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # ensure tab support
        if "style" in kwds:
            kwds["style"] |= wx.TAB_TRAVERSAL
        else:
            kwds["style"] = wx.TAB_TRAVERSAL

        # extract args intended only for this class
        if "panelNum" in kwds:
            self.panelNum = kwds["panelNum"]
            del kwds["panelNum"]
        else:
            self.panelNum = 0

        wx.Panel.__init__(self, *args, **kwds)

        # Create the controls
        dataSetNameLbl = wx.StaticText(self, wx.ID_ANY, "Data set name:")
        self.dataSetNameChoice = wx.Choice(self, -1)

        varNameLbl = wx.StaticText(self, -1, "Var name:")
        self.varNameChoice = wx.Choice(self, -1)

        self.autoscaleYChk = wx.CheckBox(self, -1, "Autoscale Y")
        self.showPointsChk = wx.CheckBox(self, -1, "Show points")

        transformLbl = wx.StaticText(self, -1, "Transform:")
        self.transformText = wx.TextCtrl(self, -1, "")

        # these text controls are all read-only, they are filled in when the plot is updated
        meanLbl = wx.StaticText(self, -1, "Mean:")
        self.meanText = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)

        stdDevLbl = wx.StaticText(self, -1, "Std. dev.:")
        self.stdDevText = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)

        peak2PeakLbl = wx.StaticText(self, -1, "Peak to peak:")
        self.peak2PeakText = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)

        nAvgLbl = wx.StaticText(self, -1, "N average:")
        self.nAvgText = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)

        self.calcNAvgBtn = wx.Button(self, -1, "Calculate")

        # Do the layout

        # plotControlsSizer is a grid that holds everything
        plotControlsSizer = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
        plotControlsSizer.AddGrowableCol(1)

        plotControlsSizer.Add(dataSetNameLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        plotControlsSizer.Add(self.dataSetNameChoice, 0, wx.EXPAND)
        plotControlsSizer.Add((10, 10))  # some empty space

        plotControlsSizer.Add(varNameLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        plotControlsSizer.Add(self.varNameChoice, 0, wx.EXPAND)
        plotControlsSizer.Add((10, 10))  # some empty space

        # the checkboxes are wrapped in a vertical box sub-sizer
        checkBoxSizer = wx.BoxSizer(wx.VERTICAL)
        checkBoxSizer.Add(self.autoscaleYChk)
        checkBoxSizer.Add(self.showPointsChk)

        # center the checkboxes in the middle column
        # or we could left align it (like it was without this sizer)
        plotControlsSizer.Add((10, 10))  # some empty space
        plotControlsSizer.Add(checkBoxSizer, 0,
                              wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)  # some empty space
        plotControlsSizer.Add((20, 20))  # some empty space

        plotControlsSizer.Add(transformLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        plotControlsSizer.Add(self.transformText, 0, wx.EXPAND)
        plotControlsSizer.Add((10, 10))  # some empty space

        # put a little extra vertical space above this next
        # group of controls
        topBorder = 10
        plotControlsSizer.Add(meanLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.TOP,
                              topBorder)
        plotControlsSizer.Add(self.meanText, 0,
                              wx.EXPAND | wx.TOP,
                              topBorder)
        plotControlsSizer.Add((10, 10))  # some empty space

        plotControlsSizer.Add(stdDevLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        plotControlsSizer.Add(self.stdDevText, 0, wx.EXPAND)
        plotControlsSizer.Add((10, 10))  # some empty space

        plotControlsSizer.Add(peak2PeakLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        plotControlsSizer.Add(self.peak2PeakText, 0, wx.EXPAND)
        plotControlsSizer.Add((10, 10))  # some empty space

        plotControlsSizer.Add(nAvgLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        plotControlsSizer.Add(self.nAvgText, 0, wx.EXPAND)
        plotControlsSizer.Add(self.calcNAvgBtn, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)

        # attemptto not disallow resize outer window any smaller so
        # controls not cut off, but didn't work
        #plotControlsSizer.Fit(self)
        #plotControlsSizer.SetSizeHints(self)

        # outer sizer adds a margin around everything
        self.outerSizer = wx.BoxSizer(wx.VERTICAL)
        self.outerSizer.Add(plotControlsSizer, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 10)

        # only allow horizontal resize
        #plotControlsSizer.SetFlexibleDirection(wx.HORIZONTAL)
        #plotControlsSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_NONE)

        # size things up
        self.SetSizer(self.outerSizer)

        self.outerSizer.Fit(self)
        self.outerSizer.SetSizeHints(self)