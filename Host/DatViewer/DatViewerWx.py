# DatViewerWx.py
#
# New DatViewer code that is based on wxPython instead of enthought libs.
#
# Making it version 3 since this is a new generation app. I'd made the initial
# DatViewer code version 2 since it never had a version number, just to distinguish
# it from the old version.

import wx
import sys
from optparse import OptionParser
from DatViewerPrefs import DatViewerPrefs


FULLAPPNAME = "Picarro Data File Viewer"
APPNAME = "DatViewer"
APPVERSION = "3.0.0"


def LogErrmsg(str):
    print >> sys.stderr, str


def LogMsg(str):
    print str

#################################################
## Main UI
##


class Frame(wx.Frame):
    def __init__(self, parent, id, title):
        #print "Frame __init__"
        LogMsg("Frame __init__")
        wx.Frame.__init__(self, parent, id, title)

        self.panel = wx.Panel(self)
        self.statusbar = self.CreateStatusBar()

        self.CreateMenus()

    def CreateMenus(self):

        # File menu
        menuFile = wx.Menu()
        openH5Item = menuFile.Append(-1,
                                     "&Open H5...\tCtrl+O",
                                     "Open an H5 file to plot its data.")
        menuFile.AppendSeparator()
        openZipItem = menuFile.Append(-1,
                                      "Concatenate &ZIP to H5...\tZ",
                                      "Concatenate all H5 files in a ZIP into a single H5 file.")
        concatFolderItem = menuFile.Append(-1,
                                           "Concatenate &folder to H5...\tF",
                                           "Concatenate all H5 and zipped H5 files within a folder into a single H5 file.")
        menuFile.AppendSeparator()

        # more File menu items go here...

        exitAppItem = menuFile.Append(-1,
                                      "E&xit",
                                      "Quit the H5 Data File Viewer.")

        self.Bind(wx.EVT_MENU, self.OnOpenH5, openH5Item)
        self.Bind(wx.EVT_MENU, self.OnOpenZip, openZipItem)
        self.Bind(wx.EVT_MENU, self.OnConcatFolder, concatFolderItem)

        self.Bind(wx.EVT_MENU, self.OnExitApp, exitAppItem)

        # View menu
        menuView = wx.Menu()

        # Window menu
        menuWindow = wx.Menu()

        # Help menu
        menuHelp = wx.Menu()
        aboutItem = menuHelp.Append(-1,
                                    "About...",
                                    "Show information about the H5 Data File Viewer.")

        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

        # build the menubar
        self.menubar = wx.MenuBar()
        self.menubar.Append(menuFile, "&File")
        self.menubar.Append(menuView, "&View")
        self.menubar.Append(menuWindow, "&Window")
        self.menubar.Append(menuHelp, "&Help")
        self.SetMenuBar(self.menubar)

    def OnOpenH5(self, event):
        print "OnOpenH5"

    def OnOpenZip(self, event):
        print "OnOpenZip"

    def OnConcatFolder(self, event):
        print "OnConcatFolder"

    def OnAbout(self, event):
        print "OnAbout"

    def OnExitApp(self, event):
        print "OnExitApp"
        self.Close()


class App(wx.App):
    def __init__(self, redirect=True, filename=None):
        #print "App __init__"
        LogMsg("App __init__")

        LogMsg("Loading prefs")

        # TODO: Figure out how to reset the prefs from the UI
        #       Haven't entered the main loop so can't look for Ctrl+Shift
        #       held down. Other possibilities:
        #          1. command line option
        #          2. menu choice to reset prefs at next startup, saves in
        #             user prefs and resets flag
        self.prefs = DatViewerPrefs(APPNAME, APPVERSION, fPrefsReset=False)
        self.prefs.LoadPrefs()
        LogMsg("Prefs loaded")

        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        print "OnInit"
        self.frame = Frame(parent=None,
                           id=-1,
                           title=FULLAPPNAME)

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
        #print >> sys.stderr, "A pretend error message"
        LogErrmsg("A pretend error message")

        return True

    def OnResizeApp(self, event):
        LogMsg("OnResizeApp")

        # update app size and position information for next startup
        self.prefs.viewerFrameSize = self.frame.GetSize()
        self.prefs.viewerFramePos = self.frame.GetPosition()

        #print "  appSize=", self.prefs.viewerFrameSize
        #print "  appPos=", self.prefs.viewerFramePos

    def OnExit(self):
        #print "OnExit"
        LogMsg("OnExit")

        # save off prefs
        LogMsg("Saving prefs")
        self.prefs.SavePrefs()
        LogMsg("Prefs saved")


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

    options, _ = parser.parse_args()

    return options


def main():
    options = ParseOptions()

    if options.version is True:
        print APPVERSION
        return

    redirect = options.redirect
    outputFile = options.outputFile

    print "redirect=", redirect

    # force redirect if outputting console to a file
    if outputFile is not None:
        redirect = True

    app = App(redirect=redirect, filename=outputFile)

    print "before MainLoop"
    app.MainLoop()
    print "after MainLoop"


if __name__ == '__main__':
    main()
