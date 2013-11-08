# PlotControlPanel.py
#
# Class of a panel of plot controls for DatViewer plots.
#
import wx


class DummyPlot(wx.Panel):
    def __init__(self, *args, **kwds):
        # extract args intended only for this class
        if "plotName" in kwds:
            name = kwds["plotName"]
            del kwds["plotName"]
        else:
            name = "DummyPlot"

        wx.Panel.__init__(self, *args, **kwds)

        self.model = Subject(name=name)
        self.model.settings = {"mean": "",
                               "stdDev": "",
                               "peakToPeak": "",
                               "nAvg": ""}

        self.model.changed = ""

        self.test1Btn = wx.Button(self, -1, "Test 1")
        self.test2Btn = wx.Button(self, -1, "Test 2")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.test1Btn)
        sizer.Add(self.test2Btn)

        self.SetSizer(sizer)
        sizer.Fit(self)
        sizer.SetSizeHints(self)

    def updatePlot(self, modelControls):
        #print "updatePlot:"
        #print "  settings=", modelControls.settings
        #print "  changed=", modelControls.changed
        #print ""

        # sample code for updating controls
        if modelControls.changed == "nAvgCalculate":
            # calculate the N average and update it
            # assume this operation can take a while
            # change to a busy cursor
            #
            # this doesn't work...
            #self.SetCursor(wx.StockCursor(wx.CURSOR_WATCH))

            # this does work, but apparently only on Windows
            wx.SetCursor(wx.StockCursor(wx.CURSOR_WATCH))
            import time
            time.sleep(5)

            import random
            nAvg = random.random() * 25
            self.model.changed = "nAvg"
            self.model.settings["nAvg"] = nAvg
            self.model.update()
            #self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

        # something changed in the controls
        # compute something or whatever
        # then update the controls
        # self.model.changed = <whatever needs to be updated>
        # self.model.settings = <values>
        # self.model.update()


######################################
# A simple flex grid for the controls.
#
class PlotControlPanelGui(wx.Panel):
    def __init__(self, *args, **kwds):
        # set/override style arg
        kwds["style"] = wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER

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

        # outer sizer adds a margin around everything
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        outerSizer.Add(plotControlsSizer, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 10)

        # only allow horizontal resize
        #plotControlsSizer.SetFlexibleDirection(wx.HORIZONTAL)
        #plotControlsSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_NONE)

        # size things up
        self.SetSizer(outerSizer)

        outerSizer.Fit(self)
        outerSizer.SetSizeHints(self)


class TestClientData(object):
    def __init__(self, panelNum):
        self.panelNum = panelNum

    def GetPanelNum(self):
        return self.panelNum


class Subject(object):
    def __init__(self, *a, **kwds):
        if "name" in kwds:
            self.name = kwds["name"]
        else:
            self.name = "unknown"

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

        # get the panel name if it's there
        if "panelName" in kwds:
            panelName = kwds["panelName"]
            del kwds["panelName"]
        else:
            panelName = ""

        # get the panel number if it's there
        if "panelNum" in kwds:
            panelNum = kwds["panelNum"]
            del kwds["panelNum"]
        else:
            panelNum = -1

        PlotControlPanelGui.__init__(self, *a, **kwds)
        self.model = Subject(name=panelName)

        # TODO: Use settings for autoscale Y and show points from prefs
        fAutoscaleY = False
        fShowPoints = True

        self.model.settings = {"fAutoscaleY": fAutoscaleY,
                               "fShowPoints": fShowPoints,
                               "strDataSetName": "",
                               "strVarName": ""}

        self.model.changed = ""

        # Create a listener for plot updates. The creator of this object needs to register
        # 
        self.listenerWrapper = ListenerWrapper(panelNum, panelName)

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
        # varName = str(varName)
        self.model.settings["strVarName"] = varName
        self.model.changed = "strVarName"
        self.model.update()

    def OnChooseDataSet(self, event):
        print "Selected data set changed"
        #print "event=", event
        #print dir(event)
        ix = self.dataSetNameChoice.GetSelection()
        dataSetName = self.dataSetNameChoice.GetStringSelection()

        # could convert this to ASCII
        #dataSetName = str(dataSetName)
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

    def updateControls(self, plotModel):
        # called by the plot when there are controls to update
        #print "plotModel.settings=", plotModel.settings
        #print "plotModel.changed=", plotModel.changed

        # update appropriate controls with the new values here...
        # self.meanText.SetValue()
        # self.stdDevText.SetValue()
        # self.peak2PeakText.SetValue()
        # self.nAvgText.SetValue()

        if plotModel.changed == "nAvg":
            self.nAvgText.SetValue(str(plotModel.settings["nAvg"]))


# this is really a plot controls listener, should rename this class
class ListenerWrapper(object):
    def __init__(self, index, name):
        self.index = index
        self.name = name

    def plotControlsListener(self, model):
        # Called when the user changes something in the plot controls.
        # The listener recipient is the plot.
        print "plotControlsListener:"
        print "  name=", self.name
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


class PlotListenerWrapper(object):
    def __init__(self, index, name):
        self.index = index
        self.name = name

    def plotListener(self, model):
        # Called when the plot computes something that needs to
        # be updated in the plot controls (mean, std. dev., etc.).
        # The listener recipient is the plot controls.
        print "plotListener:"
        print "  name=", self.name
        print "  index=", self.index
        print "  settings=", model.settings
        print "  changed=", model.changed
        print ""


class TestFrame(wx.Frame):
    def __init__(self, nPanels=1, name="Test Frame"):
        wx.Frame.__init__(self, None, -1, name)

        # TODO: pass whether to include the N average controls in the panel
        # fIncludeNavg = True

        # Don't know if we really need to track these or not
        self.panels = []
        self.plots = []
        self.listeners = []
        self.plotListeners = []

        # Sizer to hold all of the plot controls
        #mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer = wx.FlexGridSizer(rows=nPanels, cols=2)
        mainSizer.AddGrowableCol(0)

        for ix in range(nPanels):
            # plot panel name isn't exposed in the UI but useful for debugging
            panelName = "%s - %d" % (name, ix)

            panel = PlotControlPanel(self, wx.ID_ANY,
                                     style=wx.RAISED_BORDER,
                                     panelNum=ix,
                                     panelName=panelName)
            self.panels.append(panel)

            """
            # create a listener for this plot control panel and register our callback
            listenerWrapper = ListenerWrapper(ix, name)

            ixListener = panel.model.addListener(listenerWrapper.plotControlsListener)
            self.listeners.append(ixListener)
            """

            # wrap a sizer around the panel with a margin
            controlsSizer = wx.BoxSizer(wx.VERTICAL)
            controlsSizer.Add(panel, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 15)

            # create a dummy plot (right now it just has a couple of buttons)
            plot = DummyPlot(self, wx.ID_ANY,
                             style=wx.RAISED_BORDER)
            self.plots.append(plot)

            """
            # the plot control panel also listens to plot updates so register it
            controlsListenerWrapper = PlotListenerWrapper(ix, name)
            ixPlotListener = plot.model.addListener(controlsListenerWrapper.plotListener)
            self.plotListeners.append(ixPlotListener)
            """

            # wrap a sizer around this plot with a margin
            plotSizer = wx.BoxSizer(wx.VERTICAL)
            plotSizer.Add(plot, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 15)

            """
            # wrap the plot sizer and its controls sizer in a sizer
            plotAndControlsSizer = wx.FlexGridSizer(rows=1, cols=2, hgap=15, vgap=15)
            plotAndControlsSizer.AddGrowableCol(0)
            plotAndControlsSizer.Add(plotSizer)
            plotAndControlsSizer.Add(controlsSizer)

            # add the plot and controls sizer to the main sizer
            mainSizer.Add(plotAndControlsSizer, 0, wx.TOP | wx.BOTTOM, 10)
            """

            mainSizer.Add(plotSizer)
            mainSizer.Add(controlsSizer)

            # register the plot panel's listener with the plot
            plot.model.addListener(panel.updateControls)

            # register the plot's listener with the plot controls
            panel.model.addListener(plot.updatePlot)

            # for debugging it may be handy to have our own listeners registered
            # all they do is output text
            listenerWrapper = ListenerWrapper(ix, name)
            panel.model.addListener(listenerWrapper.plotControlsListener)

            controlsListenerWrapper = PlotListenerWrapper(ix, name)
            plot.model.addListener(controlsListenerWrapper.plotListener)

        # fit the frame to the needs of the main sizer
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

        # testing idle mode
        #self.Bind(wx.EVT_IDLE, self.OnIdle)

    def OnIdle(self, event):
        import time
        timestr = time.strftime("%Y%m%d-%H:%M:%S")
        print "OnIdle  ", timestr, "  ", time.clock()


class App(wx.App):
    def __init__(self, redirect=True, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = TestFrame(nPanels=3, name="Test Frame 1")
        self.frame.Show()
        self.SetTopWindow(self.frame)

        # create a second test frame to prove this works
        #self.frame2 = TestFrame(nPanels=2, name="Test Frame 2")
        #self.frame2.Show()

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
