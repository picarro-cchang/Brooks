# DatViewerWx.py
#
# New DatViewer code that is based on wxPython instead of enthought libs.
#
# Making it version 3 since this is a new generation app. I'd made the initial
# DatViewer code version 2 since it never had a version number, just to distinguish
# it from the old version.
#
# Notes:
#
# Standard scipy import conventions:
#   import numpy as np
#   import numpy.ma as ma
#   import matplotlib as mpl
#   from matplotlib import pyplot as plt
#   import matplotlib.cbook as cbook
#   import matplotlib.collections as mcol
#   import matplotlib.patches as mpatches

import wx
import sys
import os
import zipfile
import pytz
from optparse import OptionParser
from DatViewerPrefs import DatViewerPrefs
from PlotControlPanel import PlotControlPanel
from PlotPanel import PlotPanel, PlotPanel2, MplPanel

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure


FULLAPPNAME = "Picarro Data File Viewer"
APPNAME = "DatViewer"
APPVERSION = "3.0.0"

# Putting prefs in a folder path that doesn't include the point release
# version so that an update doesn't abandon the old settings. The version
# can always be bumped if they aren't compatible.
CONFIGVERSION = "3.0"
APPCONFIGSPEC = "DatViewerPrefs.ini"
USERCONFIG = "DatViewerUserPrefs.ini"

g_logMsgLevel = 0   # should be 0 for check-in


def LogErrmsg(str):
    print >> sys.stderr, str


def LogMsg(level, str):
    if level <= g_logMsgLevel:
        print str


def GenerateUniqueName(window, nPlots, plotWindowsList):
    # generate the name to view it in the menu,
    # making sure it is unique
    name = ""

    if nPlots > 0:
        if nPlots == 1:
            name = "%s [1 frame]" % window.name
        else:
            name = "%s [%d frames]" % (window.name, int(nPlots))
    else:
        name = window.name

    # first see if the window name sans numbering is there
    found = False
    for item in plotWindowsList:
        if item.name == name:
            found = True
            break

    if found is True:
        # already there, will need to try numbering
        done = False
        ix = 2
        while done is False:
            found = False
            nameToTry = "%s (%d)" % (name, int(ix))

            for item in plotWindowsList:
                if item.name == nameToTry:
                    found = True
                    break

            if found is False:
                name = nameToTry
                done = True
            else:
                # already a match, try another name
                ix += 1

    return name


#################################################
## Class for handling the various plot windows
## in the Window menu
#
class PlotWindow(object):
    def __init__(self, window):
        self.window = window

        # cache the id for the window object
        self.id = window.id

        # the title is used in the Windows menu and should be unique
        # as should also the id
        self.name = self.window.title

        # cache the filename and folder
        self.filename = self.window.filename
        self.filedir = self.window.filedir

    def GetId(self):
        return self.id

    def GetName(self):
        return self.name

    def GetWindow(self):
        return self.window

    def GetFilename(self):
        return self.filename

    def GetFiledir(self):
        return self.filedir


#################################################
## Class for handling H5 file plots
##
#  Best if this class implemented in a separate file
#  then other apps could import it for plotting H5 data
#
class SeriesFrame(wx.Frame):
    def __init__(self, *a, **k):
        LogMsg(4, "SeriesFrame __init__")

        # parent arg is required
        self.parent = k["parent"]

        # set style from prefs
        style = k.get("style", wx.DEFAULT_FRAME_STYLE)

        if self.parent.prefs.config["UILayout"]["showViewerFrameInTaskbar"] is False:
            style |= wx.FRAME_NO_TASKBAR
            print "don't show frame in taskbar"

        wx.Frame.__init__(self, wx.GetApp().TopWindow, -1,
                          'SeriesFrame', style=style, size=(550, 350))

        # parse args
        self.tz = k.get("tz", pytz.timezone("UTC"))
        self.h5File = k.get("h5File", None)
        self.nPlots = k.get("nViewers", 1)
        self.onCloseCallback = k.get("onCloseCallback", None)

        # TODO: error if there is no H5 file

        # set the name to the filename and a unique ID
        self.filename = self.h5File.GetFilename()
        self.filedir = self.h5File.GetFilepath()
        self.id = wx.NewId()

        # object name is also the filename
        self.name = self.h5File.GetFilename()

        self.title = GenerateUniqueName(self, self.nPlots, self.parent.plotWindows)
        #self.SetTitle("".join(["Viewing [", self.name, "]"]))
        self.SetTitle(self.title)

        self.panels = []
        self.plots = []

        # use settings from prefs
        fAutoscaleY = self.parent.prefs.config["UISettings"]["fAutoscaleY"]
        fShowPoints = self.parent.prefs.config["UISettings"]["fShowPoints"]

        # whatever color is set here doesn't seem to matter
        #self.SetBackgroundColour(wx.NamedColour("white"))

        # sizer which wraps around everything
        #mainSizer = wx.FlexGridSizer(rows=self.nPlots, cols=2)
        #mainSizer.AddGrowableCol(0)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        for ix in range(self.nPlots):
            # plot panel name isn't exposed in the UI but useful for debugging
            panelName = "%s - %d" % (self.title, ix)

            panel = PlotControlPanel(self, wx.ID_ANY,
                                     style=wx.SUNKEN_BORDER,
                                     panelNum=ix,
                                     panelName=panelName,
                                     fAutoscaleY=fAutoscaleY,
                                     fShowPoints=fShowPoints)
            
            self.panels.append(panel)

            # wrap a sizer around the panel with a margin
            controlsSizer = wx.BoxSizer(wx.VERTICAL)
            controlsSizer.Add(panel, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM, 20)

            panelSize = controlsSizer.GetMinSize()
            print "panelSize=", panelSize

            """
            # TODO: get size to use from prefs if it isn't -1 (initial value)

            # for now I'll use the panel size for initial sizing of the plot

            figure = Figure()
            #axes = figure.add_subplot(111)
            figure.add_subplot(111)
            canvas = FigureCanvas(self, -1, figure)

            canvas.SetSize(panelSize)
            self.plots.append(canvas)

            fWrapPlotWithSizer = True

            if fWrapPlotWithSizer is True:
                plotSizer = wx.BoxSizer(wx.VERTICAL)
                plotSizer.Add(canvas, 1, wx.LEFT | wx.LEFT | wx.TOP | wx.GROW, 15)
                mainSizer.Add(plotSizer, 0, wx.EXPAND)
                mainSizer.AddGrowableRow(ix)
                mainSizer.Add(plotSizer, 0, wx.EXPAND)
                mainSizer.Add(controlsSizer)

            else:
                mainSizer.AddGrowableRow(ix)
                mainSizer.Add(canvas, 0, wx.EXPAND)
                mainSizer.Add(controlsSizer)
            """

            # initialize the canvas size
            # TODO: get the size from prefs
            canvasSize = wx.Size(panelSize.width * 2, panelSize.height)

            # create the plot
            #plot = PlotPanel(self, wx.ID_ANY,
            plot = MplPanel(self, wx.ID_ANY,
                            #style=wx.SUNKEN_BORDER,
                            canvasSize=canvasSize)

            # This doesn't work, I need to get it to recalc size
            # somehow...
            #plot.canvas.SetSize(panelSize)
            #plot.sizer.SetSizeHints(plot)
            #plot.Fit()

            """
            plotSizer = wx.BoxSizer(wx.VERTICAL)
            plotSizer.Add(plot, 0, wx.LEFT | wx.TOP | wx.EXPAND, 20)
            plot.SetSize(panelSize)

            mainSizer.AddGrowableRow(ix)
            mainSizer.Add(plotSizer, 1, wx.EXPAND)
            mainSizer.Add(controlsSizer)
            """

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(plot, 1, flag=wx.EXPAND)
            #sizer.Add(panel, 0)
            sizer.Add(controlsSizer, 0, flag=wx.ALIGN_CENTER_VERTICAL)

            mainSizer.Add(sizer, 1, flag=wx.EXPAND)

            ##mainSizer.AddGrowableRow(ix)
            #mainSizer.Add(plot, 1, wx.EXPAND)
            ##mainSizer.Add(controlsSizer, 0)
            #mainSizer.Add(panel, 0)

        # fit the frame to the needs of the main sizer
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

        # Add a menu?

        # TODO: Each plot needs its own toolbar...
        if self.parent.prefs.config["UILayout"]["plotWindowToolbar"] is True:
            self.add_toolbar()

        # events we want to handle
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_SIZE, self.OnResizeFrame)
        self.Bind(wx.EVT_MOVE, self.OnResizeFrame)

        self.Show()

    def add_toolbar(self):
        # TODO: subclass the toolbar so we can customize it
        # for info on customizing the toolbar (removing buttons, etc.)
        #    http://dalelane.co.uk/blog/?p=778#more-778
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        if wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    def OnPaint(self, event):
        LogMsg(4, "SeriesFrame OnPaint")
        self.canvas.draw()

    def OnResizeFrame(self, event):
        LogMsg(5, "SeriesFrame::OnResizeFrame")

        frameSize = self.GetSize()
        framePos = self.GetPosition()

        LogMsg(5, "  frameSize=(%d, %d)" % (frameSize.width, frameSize.height))
        LogMsg(5, "  framePos=(%d, %d)" % (framePos.x, framePos.y))

        # execute handlers in the superclass
        # this is important - else the resize isn't handled
        # by the sizers at all...
        event.Skip()

        # update plot size and position information in prefs
        # just look at the size of the first plot canvas
        """
        appSize = self.frame.GetSize()
        appPos = self.frame.GetPosition()
        self.prefs.config["UILayout"]["viewerFrameSize"] = appSize
        self.prefs.config["UILayout"]["viewerFramePos"] = appPos

        LogMsg(5, "  appSize=(%d, %d)" % (appSize.width, appSize.height))
        LogMsg(5, "  appPos=(%d, %d)" % (appPos.x, appPos.y))

        clientSize = self.frame.GetClientSize()
        LogMsg(5, "  clientSize=(%d, %d)" % (clientSize.width, clientSize.height))

        # must update the panel size to the new client size
        self.frame.panel.SetSize(clientSize)
        """

    def OnCloseWindow(self, event):
        # user clicked the Close box
        LogMsg(4, "SeriesFrame::OnCloseWindow")

        # let parent app know we're being closed so it can do necessary
        # cleanup (e.g. remove this plot from the Windows menu, etc.)
        if self.onCloseCallback is not None:
            self.onCloseCallback(self.id, self.title)
        else:
            LogMsg(0, "SeriesFrame: onCloseCallback not registered!")

        self.Destroy()


#################################################
## Class for handling H5 files
##

class H5File(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.split(filepath)[1]
        self.dirname = os.path.split(filepath)[0]

        # This should validate that the filepath is a valid H5 file
        # Need either a validation function or return an error code if not

    def GetFilename(self):
        return self.filename

    def GetFilepath(self):
        return self.dirname


# A class to hold some GUI stuff
class GuiDatViewer(object):
    def __init__(self, filenameTextCtrl=None, dirnameTextCtrl=None):
        self.filenameTextCtrl = filenameTextCtrl
        self.dirnameTextCtrl = dirnameTextCtrl

    def GetFilenameTextCtrl(self):
        return self.filenameTextCtrl

    def GetDirnameTextCtrl(self):
        return self.dirnameTextCtrl


#################################################
## Main UI
##

# IDs for some menu items
ID_MENU_PLOTFRAMES_1 = wx.NewId()
ID_MENU_PLOTFRAMES_2 = wx.NewId()
ID_MENU_PLOTFRAMES_3 = wx.NewId()
ID_MENU_PLOT_CORR = wx.NewId()
ID_MENU_PLOT_ALLAN = wx.NewId()

mainMenuItems = [ID_MENU_PLOTFRAMES_1,
                 ID_MENU_PLOTFRAMES_2,
                 ID_MENU_PLOTFRAMES_3,
                 ID_MENU_PLOT_CORR,
                 ID_MENU_PLOT_ALLAN]


class AppFrame(wx.Frame):
    def __init__(self, parent, id, title, prefs):
        LogMsg(4, "Frame __init__")
        wx.Frame.__init__(self, parent, id, title)

        self.h5File = None
        self.prefs = prefs

        self.plotWindows = []

        # create the panel, status bar, and menus
        self.panel = wx.Panel(self)
        self.statusbar = self.CreateStatusBar()
        self.CreateMenus()

        # add the controls to the panel
        topLabel = wx.StaticText(self.panel,
                                 -1,
                                 "Current H5 File")

        topLabel.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))

        # filename and dirname text controls are read-only
        filenameLabel = wx.StaticText(self.panel, -1, "Filename:")
        filename = wx.TextCtrl(self.panel, -1, "",
                               style=wx.TE_READONLY,
                               size=(200, -1))

        dirLabel = wx.StaticText(self.panel, -1, "Folder:")
        dirname = wx.TextCtrl(self.panel, -1, "", style=wx.TE_READONLY)

        # do the layout
        # mainSizer is the top level that manages everything (vertical)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(topLabel, 0, wx.ALL, 15)
        #mainSizer.Add(wx.StaticLine(self.panel), 0,
        #              wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        # filenameSizer is a grid that holds the filename info
        filenameSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        filenameSizer.AddGrowableCol(1)
        filenameSizer.Add(filenameLabel, 0,
                          wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        filenameSizer.Add(filename, 0, wx.EXPAND)
        filenameSizer.Add(dirLabel, 0,
                          wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        filenameSizer.Add(dirname, 0, wx.EXPAND)

        # add the filenameSizer to the mainSizer
        mainSizer.Add(filenameSizer, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, 15)

        # set the sizer for the panel
        self.panel.SetSizer(mainSizer)

        # fit the frame to the needs of the sizer, frame is automatically resized
        mainSizer.Fit(self)

        # Also prevent the frame from getting any smaller than this size
        mainSizer.SetSizeHints(self)

        # Save off important GUI controls
        self.gdv = GuiDatViewer(filenameTextCtrl=filename, dirnameTextCtrl=dirname)

        # Update menu items
        self.UpdateMenus()

    def CreateMenus(self):
        menuFile = self.CreateFileMenuItems()

        # View menu
        menuView = self.CreateViewMenuItems()

        # Window menu
        #
        # We need to hang onto to this menu handle so we can
        # dynamically update it
        self.menuWindow = self.CreateWindowMenuItems()

        # Help menu
        menuHelp = self.CreateHelpMenuItems()

        # build the app menubar
        self.menubar = wx.MenuBar()
        self.menubar.Append(menuFile, "&File")
        self.menubar.Append(menuView, "&View")
        self.menubar.Append(self.menuWindow, "&Window")
        self.menubar.Append(menuHelp, "&Help")
        self.SetMenuBar(self.menubar)

    def CreateFileMenuItems(self):
        menu = wx.Menu()
        openH5Item = menu.Append(-1,
                                 "&Open H5...\tCtrl+O",
                                 "Open an H5 file to plot its data.")
        menu.AppendSeparator()
        openZipItem = menu.Append(-1,
                                  "Concatenate &ZIP to H5...\tZ",
                                  "Concatenate all H5 files in a ZIP into a single H5 file.")
        concatFolderItem = menu.Append(-1,
                                       "Concatenate &folder to H5...\tF",
                                       "Concatenate all H5 and zipped H5 files within a folder into a single H5 file.")
        menu.AppendSeparator()

        # more File menu items go here...

        exitAppItem = menu.Append(wx.ID_EXIT,
                                  "E&xit",
                                  "Quit the H5 Data File Viewer.")

        # Bindings
        self.Bind(wx.EVT_MENU, self.OnOpenH5, openH5Item)
        self.Bind(wx.EVT_MENU, self.OnOpenZip, openZipItem)
        self.Bind(wx.EVT_MENU, self.OnConcatFolder, concatFolderItem)
        self.Bind(wx.EVT_MENU, self.OnExitApp, exitAppItem)

        return menu

    def CreateViewMenuItems(self):
        # These menu items have known IDs (generated at run-time) so
        # they can be disabled until a valid H5 filename is set
        menu = wx.Menu()
        series1Item = menu.Append(ID_MENU_PLOTFRAMES_1,
                                  "New Time Series Plot (&1 Frame)...\t1",
                                  "Open a window with one frame to plot the current H5 data.")
        series2Item = menu.Append(ID_MENU_PLOTFRAMES_2,
                                  "New Time Series Plot (&2 Frames)...\t2",
                                  "Open a window with two frames to plot the current H5 data.")
        series3Item = menu.Append(ID_MENU_PLOTFRAMES_3,
                                  "New Time Series Plot (&3 Frames)...\t3",
                                  "Open a window with three viewerFramePos to plot the current H5 data.")

        menu.AppendSeparator()

        correlationItem = menu.Append(ID_MENU_PLOT_CORR,
                                      "&Correlation Plot...\tC",
                                      "Open a new window with a correlation plot of the current H5 data.")

        allenItem = menu.Append(ID_MENU_PLOT_ALLAN,
                                "&Allan Standard Deviation Plot...\tA",
                                "Open a new window with an Allan plot of the current H5 data.")

        # Bindings
        self.Bind(wx.EVT_MENU, self.onSeries1, series1Item)
        self.Bind(wx.EVT_MENU, self.onSeries2, series2Item)
        self.Bind(wx.EVT_MENU, self.onSeries3, series3Item)
        self.Bind(wx.EVT_MENU, self.NotImpl, correlationItem)
        self.Bind(wx.EVT_MENU, self.NotImpl, allenItem)

        return menu

    def CreateWindowMenuItems(self):
        # Window menu typically is empty at startup
        menuWindow = wx.Menu()
        return menuWindow

    def CreateHelpMenuItems(self):
        menuHelp = wx.Menu()
        aboutItem = menuHelp.Append(wx.ID_ABOUT,
                                    "About...",
                                    "Show information about the H5 Data File Viewer.")

        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
        return menuHelp

    def UpdateMenus(self):
        fEnable = False
        if self.h5File is not None:
            fEnable = True

        for item in mainMenuItems:
            self.menubar.Enable(item, fEnable)

    # update menu items in Windows menu
    # first clear the menu and then add all of the menu items
    def UpdateWindowMenu(self):
        windowItemsList = self.menuWindow.GetMenuItems()

        #print "windowItemsList=", windowItemsList
        #print "  item count=", self.menuWindow.GetMenuItemCount()

        for item in windowItemsList:
            self.menuWindow.RemoveItem(item)

        # populate with the current plot windows
        for plotWindow in self.plotWindows:
            #print "  plotWindow=", plotWindow
            statusMsg = "Open '%s' and bring it to the top." % plotWindow.GetName()
            #print "  name=%s", plotWindow.GetName()
            #print "  id=", plotWindow.GetId()
            windowItem = self.menuWindow.Append(plotWindow.GetId(),
                                                plotWindow.GetName(),
                                                statusMsg)

            self.Bind(wx.EVT_MENU, self.OnSelectPlotWindow, windowItem)

    def UpdateAppFrame(self):
        # update stuff in the app that isn't a menu
        # update the name in the title bar if it has changed
        name = FULLAPPNAME
        if self.h5File is not None:
            name = " ".join([FULLAPPNAME, " - ", self.h5File.GetFilename()])

        self.SetTitle(name)

    def NotImpl(self, event):
        wx.MessageBox("Feature not implemented!", "", wx.OK)

    def onSeries(self, h5File, nFrames):
        LogMsg(2, "onSeries")
        if not h5File:
            wx.MessageBox("Please open or convert a file first")
            return

        window = SeriesFrame(nViewers=nFrames,
                             h5File=h5File,
                             parent=self,
                             onCloseCallback=self.OnCloseSeriesFrame)

        # add this to the plot window list and update the Window menu
        plotWindow = PlotWindow(window)
        self.plotWindows.append(plotWindow)
        self.UpdateWindowMenu()

        #window = SeriesWindow(nViewers=nFrames, tz=info.object.tz, parent=info.object)
        #window.set(dataFile=info.object.dataFile)
        #window.traits_view.set(title=info.object.dataFile)
        #window.edit_traits(view=window.traits_view, context=window.cDict)

    def onSeries1(self, event):
        LogMsg(2, "onSeries1")
        return self.onSeries(self.h5File, 1)

    def onSeries2(self, event):
        return self.onSeries(self.h5File, 2)
        
    def onSeries3(self, event):
        return self.onSeries(self.h5File, 3)

    def OnCloseSeriesFrame(self, id, windowName):
        LogMsg(4, "OnCloseSeriesFrame: id=%d  name=%s" % (int(id), windowName))

        # find this item in the plotWindows list and delete it
        found = False
        for plotWindow in self.plotWindows:
            if id == plotWindow.id:
                # sanity check
                assert windowName == plotWindow.name

                found = True
                self.plotWindows.remove(plotWindow)
                break

        # we should have found the menu item
        assert found is True

        # update the Windows menu
        self.UpdateWindowMenu()

    def OnOpenH5(self, event):
        LogMsg(4, "OnOpenH5")

        # use last dir from prefs if it's valid
        defaultDir = self.prefs.config["FileManagement"]["lastH5OpenDir"]

        if not os.path.isdir(defaultDir):
            defaultDir = ""

        d = wx.FileDialog(None, "Open HDF5 file",
                          defaultDir=defaultDir,
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                          wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            self.h5File = H5File(d.GetPath())

            if self.h5File is not None:
                # update the filename and path controls
                self.gdv.GetFilenameTextCtrl().SetValue(self.h5File.GetFilename())
                self.gdv.GetDirnameTextCtrl().SetValue(self.h5File.GetFilepath())

                # update last dir in prefs used to open an H5 file
                self.prefs.config["FileManagement"]["lastH5OpenDir"] = self.h5File.GetFilepath()

                # update menus so choices to create plots are enabled
                self.UpdateMenus()

                self.UpdateAppFrame()

        d.Destroy()

    def OnOpenZip(self, event):
        LogMsg(4, "OnOpenZip")

        # use last dir from prefs if it's valid
        defaultDir = self.prefs.config["FileManagement"]["lastZipOpenDir"]

        if not os.path.isdir(defaultDir):
            defaultDir = ""

        # prompt user for a ZIP file to open
        d = wx.FileDialog(None, "Open ZIP HD5 archive to concatenate",
                          defaultDir=defaultDir,
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                          wildcard="zip files (*.zip)|*.zip")

        # input ZIP filepath and output H5 filepath
        zipname = None
        fname = None

        if d.ShowModal() == wx.ID_OK:
            zipname = d.GetPath()

        d.Destroy()

        if zipname is None:
            return

        # prompt user for an output H5 filename and path
        if os.path.splitext(zipname)[1] == ".zip" and zipfile.is_zipfile(zipname):
            # use the .zip filename to initialize a .h5 output filename
            # path is same as the .zip archive
            fname = os.path.splitext(zipname)[0] + ".h5"    # change to .h5 extension
            fname = os.path.split(fname)[1]                 # extract just the filename

            defaultDir = self.prefs.config["FileManagement"]["lastZipOpenSaveH5Dir"]

            if not os.path.isdir(defaultDir):
                defaultDir = ""

            # I don't think I should use wx.FD_CHANGE_DIR in the style setting.
            # What that does is change the working directory to the selected dir.
            # Probably not what is wanted.

            # give the user a chance to change it and warn about overwrites
            fd = wx.FileDialog(None, "Output H5 file",
                               defaultDir=defaultDir,
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                               defaultFile=fname,
                               wildcard="h5 files (*.h5)|*.h5")

            if fd.ShowModal() == wx.ID_OK:
                fname = fd.GetPath()

                # see if we can open the output file for writing
                # if we can't, it is probably in use
                try:
                    # I can't make this fail even if the file is open for writing
                    # in another python shell. Maybe I need to use tables.openFile()
                    # here just like the original code.
                    # TODO: Create a class to handle ZIP to H5.
                    #       Load it up here and validate before continuing.
                    fp = open(fname, "w")
                    fp.close()
                except:
                    wx.MessageBox("Cannot open %s. File may be in use." % fname)
                    fname = None

            else:
                # reset so we bail after cleanup
                fname = None

            fd.Destroy()

        # done if nothing to do or error occurred above
        if fname is None:
            return

        LogMsg(2, "OnOpenZip: zipname='%s'" % zipname)
        LogMsg(2, "OnOpenZip: fname='%s'" % fname)

        # create the HD5 archive from the zip

        # If it's not valid should we clear the current
        # H5 file object? There will be an error
        # dialog popped anyway...

        # update last dirs in prefs
        self.prefs.config["FileManagement"]["lastZipOpenDir"] = os.path.split(zipname)[0]
        self.prefs.config["FileManagement"]["lastZipOpenSaveH5Dir"] = os.path.split(fname)[0]

        # update menus so choices to create plots are enabled
        self.UpdateMenus()

    def OnConcatFolder(self, event):
        # TODO: Add a pref for a workaround for the Windows select folder dialog
        #       to use the file open dialog instead, with a dummy filename
        #       set to something like "Filename will be ignored". See this thread:
        #       http://stackoverflow.com/questions/31059/how-do-you-configure-an-openfiledialog-to-select-folders
        #
        #       Write a function to handle folder selection with an argument for
        #       whether to use this hack or not. Is this a problem on the Mac?
        LogMsg(4, "OnConcatFolder")

    def OnSelectPlotWindow(self, event):
        LogMsg(4, "OnSelectPlotWindow")
        id = event.GetId()

        for plotWindow in self.plotWindows:
            if id == plotWindow.GetId():
                # open this window if minimized and put it on top
                window = plotWindow.GetWindow()

                if window.IsIconized():
                    window.Iconize(False)
                window.SetFocus()
                #window.Show()
                window.Raise()
                break

    def OnAbout(self, event):
        LogMsg(4, "OnAbout")

        verFormatStr = "%s\n\n" \
                       "Version:\t%s\n" \
                       "\n" \
                       "Web site:\t\twww.picarro.com\n" \
                       "Technical support:\t408-962-3900\n" \
                       "Email:\t\ttechsupport@picarro.com\n" \
                       "\n" \
                       "Copyright (c) 2005 - 2013, Picarro Inc.\n"
        verMsg = verFormatStr % (FULLAPPNAME, APPVERSION)
        wx.MessageBox(verMsg, APPNAME, wx.OK)

    def OnExitApp(self, event):
        LogMsg(4, "OnExitApp")
        self.Close()


class App(wx.App):
    def __init__(self, redirect=True, filename=None):
        LogMsg(4, "App __init__")

        LogMsg(4, "Loading prefs")

        # TODO: Figure out how to reset the prefs from the UI
        #       Haven't entered the main loop so can't look for Ctrl+Shift
        #       held down. Other possibilities:
        #          1. command line option
        #          2. menu choice to reset prefs at next startup, saves in
        #             user prefs and resets flag
        self.prefs = DatViewerPrefs(APPNAME, CONFIGVERSION,
                                    defaultConfigSpec=APPCONFIGSPEC,
                                    defaultUserPrefsFilename=USERCONFIG,
                                    fPrefsReset=False)
        self.prefs.LoadPrefs()
        LogMsg(4, "Prefs loaded")

        # translate prefs that are special types (e.g., wx.Size, wx.Point)
        self.TranslatePrefsAfterLoad()

        self.DumpPrefs()

        wx.App.__init__(self, redirect, filename)

    def TranslatePrefsAfterLoad(self):
        # these are for prefs whose types are unsupported by configobj
        # app size
        sizeTmp = self.prefs.config["UILayout"]["viewerFrameSize"]
        sizeTmp = wx.Size(sizeTmp[0], sizeTmp[1])
        self.prefs.config["UILayout"]["viewerFrameSize"] = sizeTmp

        # app position
        posTmp = self.prefs.config["UILayout"]["viewerFramePos"]
        posTmp = wx.Point(posTmp[0], posTmp[1])
        self.prefs.config["UILayout"]["viewerFramePos"] = posTmp

        # plot size
        #
        # ...for 1 plot in the viewer
        sizeTmp = self.prefs.config["UILayout"]["plotSize_1"]
        sizeTmp = wx.Size(sizeTmp[0], sizeTmp[1])
        self.prefs.config["UILayout"]["plotSize_1"] = sizeTmp

        # ...for 2 plots in the viewer
        sizeTmp = self.prefs.config["UILayout"]["plotSize_2"]
        sizeTmp = wx.Size(sizeTmp[0], sizeTmp[1])
        self.prefs.config["UILayout"]["plotSize_2"] = sizeTmp

        # ...for 3 plots in the viewer
        sizeTmp = self.prefs.config["UILayout"]["plotSize_3"]
        sizeTmp = wx.Size(sizeTmp[0], sizeTmp[1])
        self.prefs.config["UILayout"]["plotSize_3"] = sizeTmp

    def TranslatePrefsBeforeSave(self):
        # convert these prefs back to a list
        sizeTmp = self.prefs.config["UILayout"]["viewerFrameSize"]
        sizeTmp = [sizeTmp.width, sizeTmp.height]
        self.prefs.config["UILayout"]["viewerFrameSize"] = sizeTmp

        posTmp = self.prefs.config["UILayout"]["viewerFramePos"]
        posTmp = [posTmp.x, posTmp.y]
        self.prefs.config["UILayout"]["viewerFramePos"] = posTmp

        sizeTmp = self.prefs.config["UILayout"]["plotSize_1"]
        sizeTmp = [sizeTmp.width, sizeTmp.height]
        self.prefs.config["UILayout"]["plotSize_1"] = sizeTmp

        sizeTmp = self.prefs.config["UILayout"]["plotSize_2"]
        sizeTmp = [sizeTmp.width, sizeTmp.height]
        self.prefs.config["UILayout"]["plotSize_2"] = sizeTmp

        sizeTmp = self.prefs.config["UILayout"]["plotSize_3"]
        sizeTmp = [sizeTmp.width, sizeTmp.height]
        self.prefs.config["UILayout"]["plotSize_3"] = sizeTmp

    def DumpPrefs(self):
        print "lastZipOpenDir='%s'" % self.prefs.config["FileManagement"]["lastZipOpenDir"]
        pass

    def OnInit(self):
        LogMsg(4, "App::OnInit")
        self.frame = AppFrame(parent=None,
                              id=-1,
                              title=FULLAPPNAME,
                              prefs=self.prefs)

        # TODO: throw up a splash screen while the app loads

        # set app size and position
        self.frame.SetSize(self.prefs.config["UILayout"]["viewerFrameSize"])

        posTmp = self.prefs.config["UILayout"]["viewerFramePos"]
        if posTmp.x != -1 and posTmp.y != -1:
            self.frame.SetPosition(posTmp)

        # events we want to handle
        self.frame.Bind(wx.EVT_SIZE, self.OnResizeApp)
        self.frame.Bind(wx.EVT_MOVE, self.OnResizeApp)

        self.frame.Show()
        self.SetTopWindow(self.frame)
        #LogErrmsg("A pretend error message")

        return True

    def OnResizeApp(self, event):
        LogMsg(5, "App::OnResizeApp")

        # update app size and position information in prefs
        appSize = self.frame.GetSize()
        appPos = self.frame.GetPosition()
        self.prefs.config["UILayout"]["viewerFrameSize"] = appSize
        self.prefs.config["UILayout"]["viewerFramePos"] = appPos

        LogMsg(5, "  appSize=(%d, %d)" % (appSize.width, appSize.height))
        LogMsg(5, "  appPos=(%d, %d)" % (appPos.x, appPos.y))

        clientSize = self.frame.GetClientSize()
        LogMsg(5, "  clientSize=(%d, %d)" % (clientSize.width, clientSize.height))

        # must update the panel size to the new client size
        self.frame.panel.SetSize(clientSize)

    def OnExit(self):
        LogMsg(4, "App::OnExit")

        # we must translate certain prefs before persisting them
        self.TranslatePrefsBeforeSave()

        # save off prefs
        LogMsg(4, "Saving prefs")
        self.prefs.SavePrefs()
        LogMsg(4, "Prefs saved")


def ParseOptions():
    usage = """
%prog [options]

Picarro H5 file viewer and converter.
"""

    parser = OptionParser(usage=usage)

    parser.add_option('-v', '--version', dest='version', action='store_true',
                      default=None, help=('report version number for this application'))

    parser.add_option('-r', '--redirect', dest='redirect', action='store_true',
                      default=False, help=('redirect output to a separate console window, '
                                           'useful for debugging'))

    parser.add_option('-o', '--outfile', dest='outputFile', action='store', type='string',
                      default=None, help=('output filename for console output, '
                                          'useful for debugging'))

    parser.add_option('-l', '--loglevel', dest='loglevel', action='store', type='int',
                      default=g_logMsgLevel, help=('set message logging level, '
                                                   '0=highest  5=lowest (noisy)'))

    options, _ = parser.parse_args()

    return options


def main():
    global g_logMsgLevel

    options = ParseOptions()

    if options.version is True:
        print APPVERSION
        return

    redirect = options.redirect
    outputFile = options.outputFile
    g_logMsgLevel = options.loglevel

    # force logging
    #g_logMsgLevel = int(5)

    LogMsg(4, "redirect=%d" % redirect)

    # force redirect if outputting console to a file
    if outputFile is not None:
        redirect = True

    app = App(redirect=redirect, filename=outputFile)

    LogMsg(4, "before MainLoop")
    app.MainLoop()
    LogMsg(4, "after MainLoop")


if __name__ == '__main__':
    main()
