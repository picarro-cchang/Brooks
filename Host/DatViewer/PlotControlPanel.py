# PlotControlPanel.py
#
# Class of a panel of plot controls for DatViewer plots.
#
import wx
from PlotControlPanelGui import PlotControlPanelGui
#from PlotPanel import PlotPanel2


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
            # this doesn't work on Windows...
            #self.SetCursor(wx.StockCursor(wx.CURSOR_WATCH))

            # this does work, but apparently only on Windows
            # but it doesn't block the message queue so
            # clicking on other controls just queues them up
            #
            # I really need to put up a plexiglass (invisible window
            # that grabs all of the messages)
            wx.SetCursor(wx.StockCursor(wx.CURSOR_WATCH))
            import time
            time.sleep(5)

            # there is also a busy info dialog in wx
            # http://www.blog.pythonlibrary.org/2010/06/26/the-dialogs-of-wxpython-part-1-of-2/

            import random
            nAvg = random.random() * 25
            self.model.changed = "nAvg"
            self.model.settings["nAvg"] = nAvg
            wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            #self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

            self.model.update()

        # something changed in the controls
        # compute something or whatever
        # then update the controls
        # self.model.changed = <whatever needs to be updated>
        # self.model.settings = <values>
        # self.model.update()


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
    def __init__(self, nPanels=1, name="Test Frame", debug=False):
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

            # wrap a sizer around the panel with a margin
            controlsSizer = wx.BoxSizer(wx.VERTICAL)
            controlsSizer.Add(panel, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 15)

            # create a dummy plot (right now it just has a couple of buttons)
            plot = DummyPlot(self, wx.ID_ANY,
                             style=wx.RAISED_BORDER)
            self.plots.append(plot)

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

            mainSizer.AddGrowableRow(ix)

            mainSizer.Add(plotSizer, 0, wx.EXPAND)
            mainSizer.Add(controlsSizer)

            # for debugging it may be handy to have our own listeners registered
            # all they do is output text
            # put these first so we get the messages before anything else does
            if debug is True:
                listenerWrapper = ListenerWrapper(ix, name)
                panel.model.addListener(listenerWrapper.plotControlsListener)

                plotListenerWrapper = PlotListenerWrapper(ix, name)
                plot.model.addListener(plotListenerWrapper.plotListener)

            # register the plot panel's listener with the plot
            plot.model.addListener(panel.updateControls)

            # register the plot's listener with the plot controls
            panel.model.addListener(plot.updatePlot)

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
        debug = True
        self.frame = TestFrame(nPanels=3, name="Test Frame 1", debug=debug)
        self.frame.Show()
        self.SetTopWindow(self.frame)

        # create a second test frame to prove this works
        self.frame2 = TestFrame(nPanels=2, name="Test Frame 2", debug=debug)
        self.frame2.Show()

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
