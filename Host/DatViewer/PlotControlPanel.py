# PlotControlPanel.py
#
# Class of a panel of plot controls for DatViewer plots.
#
import wx


######################################
# A simple flex grid for the controls.
#
class PlotControlPanelFlexGrid(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
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


class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Plot Control Frame")

        # TODO: pass whether to include the N average controls in the panel
        # fIncludeNavg = True
        self.panel = PlotControlPanelFlexGrid(self, wx.ID_ANY, style=wx.RAISED_BORDER)

        # populate dropdowns and init other controls in the panel

        # InsertItems worked on my Macbook Pro but not on Windows -- WTF??
        # On Windows it's SetItems.
        dataSetNameList = ["data A", "data B", "data C"]
        #self.panel.dataSetNameChoice.InsertItems(dataSetNameList, 0)
        self.panel.dataSetNameChoice.SetItems(dataSetNameList)
        self.panel.dataSetNameChoice.SetSelection(0)

        # useful for debugging -- print out the function names available
        """
        print "type(self.panel.dataSetNameChoice)=", type(self.panel.dataSetNameChoice)
        choiceFcns = dir(self.panel.dataSetNameChoice)
        print choiceFcns

        with open("ChoiceFcns.txt", 'w') as fp:
            for f in choiceFcns:
                print >>fp, f
        """

        varNameList = ["var1", "var2", "var3"]
        #self.panel.varNameChoice.InsertItems(varNameList, 0)
        self.panel.varNameChoice.SetItems(varNameList)
        self.panel.varNameChoice.SetSelection(0)

        # SetString() is for replacing an existing choice
        #self.panel.varNameChoice.SetString(0, "replaced var1")

        self.Bind(wx.EVT_CHOICE, self.OnChooseVar, self.panel.varNameChoice)

        # check the Autoscale Y checkbox and bind
        self.panel.autoscaleYChk.SetValue(True)
        self.Bind(wx.EVT_CHECKBOX, self.OnAutoscaleYChk, self.panel.autoscaleYChk)

        # init a text box value
        self.panel.meanText.SetValue("1.0")

        self.Bind(wx.EVT_BUTTON, self.OnCalcAverage, self.panel.calcNAvgBtn)

        # wrap a sizer around the panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 15)
        self.SetSizer(sizer)

    def OnCalcAverage(self, event):
        print "Calculate average button clicked"

    def OnAutoscaleYChk(self, event):
        print "Autoscale Y checkbox clicked"
        print "State=", self.panel.autoscaleYChk.GetValue()

    def OnChooseVar(self, event):
        print "Selected var changed"
        ix = self.panel.varNameChoice.GetSelection()
        varName = self.panel.varNameChoice.GetStringSelection()
        print "  ix=%d  varName=%s" % (ix, varName)


class App(wx.App):
    def __init__(self, redirect=True, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = TestFrame()
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
