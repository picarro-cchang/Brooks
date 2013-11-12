# PlotPanel.py
#
# The panel that contains the plot and canvas
import wx

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
#from FigureInteraction import FigureInteraction
#from threading import RLock


class MplPanel(wx.Panel):
    '''
    Panel containing a matplotlib graph with a navigation toolbar for use with wxGlade
    '''


    def __init__(self, *args, **kwds):
        '''
        Constructor
        '''
        fCanvasSize = False
        if "canvasSize" in kwds:
            canvasSize = kwds["canvasSize"]
            del kwds["canvasSize"]
            fCanvasSize = True

        wx.Panel.__init__(self, *args, **kwds)

        self.figure = Figure()
        self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, wx.ID_ANY, self.figure)
#        self.toolbar = NavigationToolbar2Wx(self.canvas)
#        self.toolbar.Realize()

        if fCanvasSize is True:
            self.canvas.SetSize(canvasSize)

        # Not sure what this is for, was in Sze's code
        #self.fi = FigureInteraction(self.figure,RLock())

        self.sizer = wx.BoxSizer(wx.VERTICAL)
#        self.sizer.Add(self.toolbar,0,wx.LEFT | wx.EXPAND)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.EXPAND)
        self.SetAutoLayout(True)
#        self.toolbar.Show()
        self.SetSizer(self.sizer)
        self.sizer.SetSizeHints(self)
        self.Fit()


class PlotPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        if "style" in kwds:
            kwds["style"] |= wx.CLIP_CHILDREN
        else:
            kwds["style"] = wx.CLIP_CHILDREN

        wx.Panel.__init__(self, *args, **kwds)

        self.figure = Figure()
        #axes = figure.add_subplot(111)
        self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)

        # hard-code min size for now
        minSize = wx.Size(354, 284)
        #minSize = wx.Size(800, 900)

        self.canvas.SetMinSize(minSize)


class PlotPanel2(wx.Panel):
    def __init__(self, *args, **kwds):
        if "style" in kwds:
            kwds["style"] |= wx.CLIP_CHILDREN
        else:
            kwds["style"] = wx.CLIP_CHILDREN

        wx.Panel.__init__(self, *args, **kwds)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.figure = Figure()
        #axes = figure.add_subplot(111)
        self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)

        # hard-code min size for now
        minSize = wx.Size(354, 284)
        #minSize = wx.Size(800, 900)

        self.canvas.SetMinSize(minSize)

        # to set the size of a sizer
        #sizer.SetDimension(x, y, width, height)

        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)

        # doesn't work for either sizer or canvas or self
        #self.SetMinSize(minSize)
        #self.SetSize(minSize)


class TestFrame(wx.Frame):
    def __init__(self, nPanels=1, name="Test Plot Frame", debug=False):
        wx.Frame.__init__(self, None, -1, name)

        plot = MplPanel(self, wx.ID_ANY,
                        style=wx.RAISED_BORDER)


class App(wx.App):
    def __init__(self, redirect=True, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        debug = True
        self.frame = TestFrame(nPanels=3, name="Test Frame 1", debug=debug)
        self.frame.Show()
        self.SetTopWindow(self.frame)

        # create a second test frame to prove this works
        #self.frame2 = TestFrame(nPanels=2, name="Test Frame 2", debug=debug)
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
