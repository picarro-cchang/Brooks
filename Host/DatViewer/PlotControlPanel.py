# PlotControlPanel.py
#
# Class of a panel of plot controls for DatViewer plots.
#
import wx


######################################
# A simple flex grid for the controls.
#
class PlotControlPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER

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

        meanLbl = wx.StaticText(self, -1, "Mean:")
        self.meanText = wx.TextCtrl(self, -1, "")

        stdDevLbl = wx.StaticText(self, -1, "Std. dev.:")
        self.stdDevText = wx.TextCtrl(self, -1, "")

        peak2PeakLbl = wx.StaticText(self, -1, "Peak to peak:")
        self.peak2PeakText = wx.TextCtrl(self, -1, "")

        nAvgLbl = wx.StaticText(self, -1, "N average:")
        self.nAvgText = wx.TextCtrl(self, -1, "")

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
        plotControlsSizer.Add((10, 10))  # some empty space

        """
        # checkboxes not in a sizer
        plotControlsSizer.Add((10, 10))  # some empty space
        plotControlsSizer.Add(autoscaleYChk, 0,
                              wx.ALIGN_LEFT)
        plotControlsSizer.Add((10, 10))  # some empty space
        #plotControlsSizer.Add((10, 10))  # some empty space

        plotControlsSizer.Add((10, 10))  # some empty space
        plotControlsSizer.Add(showPointsChk, 0,
                              wx.ALIGN_LEFT)
        plotControlsSizer.Add((10, 10))  # some empty space
        #plotControlsSizer.Add((10, 10))  # some empty space
        """

        plotControlsSizer.Add(meanLbl, 0,
                              wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        plotControlsSizer.Add(self.meanText, 0, wx.EXPAND)
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

        # only allow horizontal resize
        #plotControlsSizer.SetFlexibleDirection(wx.HORIZONTAL)
        #plotControlsSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_NONE)

        # size things up
        self.SetSizer(plotControlsSizer)

        plotControlsSizer.Fit(self)
        plotControlsSizer.SetSizeHints(self)


class TestClientData(object):
    def __init__(self, panelNum):
        self.panelNum = panelNum

    def GetPanelNum(self):
        return self.panelNum


class Subject(object):
    def __init__(self, *a, **kwds):
        self.listeners = {}
        self.nextListenerIndex = 0

    def addListener(self, listenerFunc):
        self.listeners[self.nextListenerIndex] = listenerFunc
        retVal = self.nextListenerIndex
        self.nextListenerIndex += 1
        return retVal

    def removeListener(self, listenerIndex):
        del self.listeners[listenerIndex]

    def update(self):
        for l in self.listeners:
            self.listeners[l](self)


"""
class PlotDisplayPanel(PlotDisplayPanelGui):
     def __init__(self, *a, **kwds):
        PlotDisplayPanelGui.__init__(self, *a, **kwds)
        self.model = Subject()
"""


class PlotControlPanel(PlotControlPanelGui):
    def __init__(self, *a, **kwds):
        PlotControlPanelGui.__init__(self, *a, **kwds)
        self.model = Subject()

        # pull settings for autoscale Y and show points from prefs
        fAutoscaleY = False
        fShowPoints = True

        self.model.settings = {"fAutoscaleY": fAutoscaleY,
                               "fShowPoints": fShowPoints,
                               "strDataSetName": "",
                               "strVarName": ""}

        self.model.changed = ""

        dataSetNameList = ["", "data A", "data B", "data C"]
        self.dataSetNameChoice.SetItems(dataSetNameList)
        self.dataSetNameChoice.SetSelection(0)

        varNameList = ["", "var1", "var2", "var3"]
        self.varNameChoice.SetItems(varNameList)
        self.varNameChoice.SetSelection(0)

        self.autoscaleYChk.SetValue(fAutoscaleY)
        self.showPointsChk.SetValue(fShowPoints)

        self.Bind(wx.EVT_CHOICE, self.OnChooseVar, self.varNameChoice)
        self.Bind(wx.EVT_CHOICE, self.OnChooseDataSet, self.dataSetNameChoice)

        self.Bind(wx.EVT_CHECKBOX, self.OnAutoscaleYChk, self.autoscaleYChk)
        self.Bind(wx.EVT_CHECKBOX, self.OnShowPointsChk, self.showPointsChk)

        self.Bind(wx.EVT_BUTTON, self.OnNAvgCalculate, self.calcNAvgBtn)

    def OnChooseVar(self, event):
        print "Selected var changed"
        #print "event=", event
        #print dir(event)
        ix = self.varNameChoice.GetSelection()
        varName = self.varNameChoice.GetStringSelection()
        print "  ix=%d  varName=%s" % (ix, varName)

        # Note: wx returns Unicode strings here, we might need to
        #       convert them to ASCII
        self.model.settings["strVarName"] = varName
        self.model.changed = "strVarName"
        self.model.update()

    def OnChooseDataSet(self, event):
        print "Selected data set changed"
        #print "event=", event
        #print dir(event)
        ix = self.dataSetNameChoice.GetSelection()
        dataSetName = self.dataSetNameChoice.GetStringSelection()
        print "  ix=%d  dataSetName=%s" % (ix, dataSetName)

        self.model.settings["strDataSetName"] = dataSetName
        self.model.changed = "strDataSetName"
        self.model.update()

    def OnAutoscaleYChk(self, event):
        print "Autoscale Y checkbox clicked"
        #print "event=", event
        #print dir(event)
        self.model.settings["fAutoscaleY"] = self.autoscaleYChk.GetValue()
        self.model.changed = "fAutoscaleY"
        self.model.update()

    def OnShowPointsChk(self, event):
        print "Show points checkbox clicked"
        #print "event=", event
        #print dir(event)
        self.model.settings["fShowPoints"] = self.showPointsChk.GetValue()
        self.model.changed = "fShowPoints"
        self.model.update()

    def OnNAvgCalculate(self, event):
        print "Calculate average button clicked"
        self.model.changed = "nAvgCalculate"
        self.model.update()


class ListenerWrapper(object):
    def __init__(self, index):
        self.index = index

    def plotControlsListener(self, model):
        print "plotControlsListener:"
        print "  index=", self.index
        print "  settings=", model.settings
        print "  changed=", model.changed

        """
        for key in model.settings:
            value = model.settings[key]
            print "  key=", key
            print "  value type =", type(value)
        """

        print ""


class TestFrame(wx.Frame):
    def __init__(self, nPanels=1):
        wx.Frame.__init__(self, None, -1, "Plot Control Frame")

        # TODO: pass whether to include the N average controls in the panel
        # fIncludeNavg = True
        self.panels = []
        self.listeners = []

        # Sizer to hold all of the plot controls
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        for ix in range(nPanels):
            panel = PlotControlPanel(self, wx.ID_ANY,
                                     style=wx.RAISED_BORDER,
                                     panelNum=ix)
            self.panels.append(panel)

            listenerWrapper = ListenerWrapper(ix)

            ixListener = panel.model.addListener(listenerWrapper.plotControlsListener)
            self.listeners.append(ixListener)

            # wrap a sizer around this panel
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(panel, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 15)
            #self.SetSizer(sizer)
            #panel.SetSizer(sizer)

            # add this panel sizer to the main sizer
            mainSizer.Add(sizer, 0, wx.TOP | wx.BOTTOM, 10)

        # fit the frame to the needs of the main sizer
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    """
    def OnCalcAverage(self, event):
        print "Calculate average button clicked"
        print "event=", event
        print dir(event)

        tcd = event.GetClientData()
        print "tcd=", tcd
        #print "panelNum=", tcd.GetPanelNum()

    def OnAutoscaleYChk(self, event):
        print "Autoscale Y checkbox clicked"
        print "event=", event
        print dir(event)

        tcd = event.GetClientData()
        print "tcd=", tcd

        co = event.GetClientObject()
        print "co=", co
        #print "State=", self.panel.autoscaleYChk.GetValue()

    def OnChooseVar(self, event):
        print "Selected var changed"
        print "event=", event
        print dir(event)
        print ""
        tcd = event.GetClientData()
        print "tcd=", tcd
        ix = self.panel.varNameChoice.GetSelection()
        varName = self.panel.varNameChoice.GetStringSelection()
        print "  ix=%d  varName=%s" % (ix, varName)
    """


class App(wx.App):
    def __init__(self, redirect=True, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = TestFrame(nPanels=3)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


def main():
    # wx.PySimpleApp() is being deprecated
    #app = wx.PySimpleApp()
    #TestFrame().Show()

    # Set this to False so output goes to cmd window it was run from
    # True opens a new cmd window for the output.
    redirect = False
    app = App(redirect=redirect)
    app.MainLoop()

if __name__ == "__main__":
    main()
