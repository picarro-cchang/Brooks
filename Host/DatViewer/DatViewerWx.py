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

g_logMsgLevel = 5


def LogErrmsg(str):
    print >> sys.stderr, str


def LogMsg(level, str):
    if level <= g_logMsgLevel:
        print str

#################################################
## Main UI
##


class Frame(wx.Frame):
    def __init__(self, parent, id, title):
        LogMsg(4, "Frame __init__")
        wx.Frame.__init__(self, parent, id, title)

        self.panel = wx.Panel(self)
        self.statusbar = self.CreateStatusBar()

        self.CreateMenus()

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
        menu = wx.Menu()
        # add View menu items here...
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

    def OnOpenH5(self, event):
        LogMsg(4, "OnOpenH5")

    def OnOpenZip(self, event):
        LogMsg(4, "OnOpenZip")

    def OnConcatFolder(self, event):
        LogMsg(4, "OnConcatFolder")

    def OnAbout(self, event):
        LogMsg(4, "OnAbout")

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
                      default=0, help=('set message logging level, '
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
