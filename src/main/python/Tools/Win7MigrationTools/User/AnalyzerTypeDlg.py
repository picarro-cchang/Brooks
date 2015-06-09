# AnalyzerTypeDlg.py
#
# Prompt the user for the analyzer type

import wx
import os


analyzerType = ""

def getAnalyzerList(path):
    skipList = ["addons"]

    dirList = os.listdir(path)
    analyzerList = []

    for d in dirList:
        if d.lower() in skipList:
            continue

        ad = os.path.join(path, d)
        if os.path.isdir(ad):
            analyzerList.append(d)

    # sort the list
    analyzerList.sort()
    return analyzerList


class MiniFrame(wx.MiniFrame):
    def __init__(self, installerPath):
        wx.MiniFrame.__init__(self, None, -1, 'Analyzer Type', 
                size=(300, 255))
        panel = wx.Panel(self, -1, size=(300, 255))

        wx.StaticText(panel, -1, "Select your analyzer type from the list and click OK:", (20, 10))

        # use folder names for the list of analyzers
        analyzerList = getAnalyzerList(installerPath)
        analyzerList.insert(0, "")  # prepend empty string as first item
        self.listBox = wx.ListBox(panel, -1, (80, 40), (80, 120), analyzerList, wx.LB_SINGLE)
        self.listBox.SetSelection(0)

        okButton = wx.Button(panel, -1, "OK", pos=(40, 185))
        cancelButton = wx.Button(panel, -1, "Cancel", pos=(165, 185))

        # bindings
        self.Bind(wx.EVT_BUTTON, self.OnOK, okButton)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancelButton)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnOK(self, event):
        global analyzerType
        sel = self.listBox.GetStringSelection()
        print sel
        analyzerType = sel
        self.Close(True)

    def OnCancel(self, event):
        self.Close(True)

    def OnCloseWindow(self, event):
        self.Destroy()


def analyzerTypeDlg(installerPath):
    app = wx.PySimpleApp()
    MiniFrame(installerPath).Show()
    app.MainLoop()

    return analyzerType


if __name__ == '__main__':
    # for testing build a list from the network folder path
    installerPath = r"S:\CRDS\CRD Engineering\Software\G2000\Installer\g2000_win7"

    app = wx.PySimpleApp()
    MiniFrame(installerPath).Show()
    app.MainLoop() 
