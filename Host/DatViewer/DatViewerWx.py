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
from optparse import OptionParser
from DatViewerPrefs import DatViewerPrefs


FULLAPPNAME = "Picarro Data File Viewer"
APPNAME = "DatViewer"
APPVERSION = "3.0.0"

g_logMsgLevel = 5   # should be 0 for check-in


def LogErrmsg(str):
    print >> sys.stderr, str


def LogMsg(level, str):
    if level <= g_logMsgLevel:
        print str


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
        menuWindow = self.CreateWindowMenuItems()

        # Help menu
        menuHelp = self.CreateHelpMenuItems()

        # build the app menubar
        self.menubar = wx.MenuBar()
        self.menubar.Append(menuFile, "&File")
        self.menubar.Append(menuView, "&View")
        self.menubar.Append(menuWindow, "&Window")
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
                                  "New Time Series Plot (&2 Frames)...\t1",
                                  "Open a window with two frames to plot the current H5 data.")
        series3Item = menu.Append(ID_MENU_PLOTFRAMES_3,
                                  "New Time Series Plot (&3 Frames)...\t1",
                                  "Open a window with three viewerFramePos to plot the current H5 data.")

        menu.AppendSeparator()

        correlationItem = menu.Append(ID_MENU_PLOT_CORR,
                                      "&Correlation Plot...\tC",
                                      "Open a new window with a correlation plot of the current H5 data.")

        allenItem = menu.Append(ID_MENU_PLOT_ALLAN,
                                "&Allan Standard Deviation Plot...\tA",
                                "Open a new window with an Allan plot of the current H5 data.")

        # Bindings
        self.Bind(wx.EVT_MENU, self.NotImpl, series1Item)
        self.Bind(wx.EVT_MENU, self.NotImpl, series2Item)
        self.Bind(wx.EVT_MENU, self.NotImpl, series3Item)
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

    def NotImpl(self, event):
        wx.MessageBox("Feature not implemented!", "", wx.OK)

    def OnOpenH5(self, event):
        LogMsg(4, "OnOpenH5")

        # use last dir from prefs if it's valid
        defaultDir = self.prefs.lastH5OpenDir

        if not os.path.isdir(defaultDir):
            defaultDir = None

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
                self.prefs.lastH5OpenDir = self.h5File.GetFilepath()

                # update menus so choices to create plots are enabled
                self.UpdateMenus()

        d.Destroy()

    def OnOpenZip(self, event):
        LogMsg(4, "OnOpenZip")

        # use last dir from prefs if it's valid
        defaultDir = self.prefs.lastZipOpenDir

        if not os.path.isdir(defaultDir):
            defaultDir = None

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
            fname = os.path.splitext(zipname)[0] + ".h5"

            defaultDir = self.prefs.lastZipOpenSaveH5Dir

            print "defaultDir='%s'" % defaultDir

            if not os.path.isdir(defaultDir):
                defaultDir = ""

            # give the user a chance to change it and warn about overwrites
            fd = wx.FileDialog(None, "Output H5 file",
                               defaultDir=defaultDir,
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR,
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

        # update last dir in prefs
        self.prefs.lastZipOpenDir = os.path.split(zipname)[0]
        self.prefs.lastZipOpenSaveH5Dir = os.path.split(fname)[0]

        # update menus so choices to create plots are enabled
        self.UpdateMenus()

    def OnConcatFolder(self, event):
        LogMsg(4, "OnConcatFolder")

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
        self.prefs = DatViewerPrefs(APPNAME, APPVERSION, fPrefsReset=False)
        self.prefs.LoadPrefs()
        LogMsg(4, "Prefs loaded")

        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        LogMsg(4, "OnInit")
        self.frame = AppFrame(parent=None,
                              id=-1,
                              title=FULLAPPNAME,
                              prefs=self.prefs)

        # TODO: throw up a splash screen while the app loads

        # set app size and position
        self.frame.SetSize(self.prefs.viewerFrameSize)

        if self.prefs.viewerFramePos.x != -1 and self.prefs.viewerFramePos.y != -1:
            self.frame.SetPosition(self.prefs.viewerFramePos)

        # events we want to handle
        self.frame.Bind(wx.EVT_SIZE, self.OnResizeApp)
        self.frame.Bind(wx.EVT_MOVE, self.OnResizeApp)

        self.frame.Show()
        self.SetTopWindow(self.frame)
        #LogErrmsg("A pretend error message")

        return True

    def OnResizeApp(self, event):
        LogMsg(5, "OnResizeApp")

        # update app size and position information in prefs
        self.prefs.viewerFrameSize = self.frame.GetSize()
        self.prefs.viewerFramePos = self.frame.GetPosition()

        LogMsg(5, "  appSize=(%d, %d)" % (self.prefs.viewerFrameSize.width, self.prefs.viewerFrameSize.height))
        LogMsg(5, "  appPos=(%d, %d)" % (self.prefs.viewerFramePos.x, self.prefs.viewerFramePos.y))

        clientSize = self.frame.GetClientSize()
        LogMsg(5, "  clientSize=(%d, %d)" % (clientSize.width, clientSize.height))

        # must update the panel size to the new client size
        self.frame.panel.SetSize(clientSize)

    def OnExit(self):
        LogMsg(4, "OnExit")

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
