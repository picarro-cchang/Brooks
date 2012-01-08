#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade HG on Wed Jan 04 16:00:45 2012

import wx

# begin wxGlade: extracode
# end wxGlade



class ConfigManagerGui(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ConfigManagerGui.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        # Menu Bar
        self.frame_1_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(11, "&Reload from disk\tF5", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(12, "&Save\tCtrl-S", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(13, "Save &As...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(14, "Save All", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(15, "E&xit\tCtrl-Q", "", wx.ITEM_NORMAL)
        self.frame_1_menubar.Append(wxglade_tmp_menu, "&File")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(21, "&Find\tCtrl-F", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(22, "&Replace\tCtrl-H", "", wx.ITEM_NORMAL)
        self.frame_1_menubar.Append(wxglade_tmp_menu, "&Edit")
        self.SetMenuBar(self.frame_1_menubar)
        # Menu Bar end
        self.frameMainStatusbar = self.CreateStatusBar(3, 0)
        self.windowSplitter = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.windowTree = wx.Panel(self.windowSplitter, -1)
        self.treeCtrlFiles = wx.TreeCtrl(self.windowTree, -1, style=wx.TR_HAS_BUTTONS|wx.TR_LINES_AT_ROOT|wx.TR_DEFAULT_STYLE|wx.SUNKEN_BORDER)
        self.windowEditors = wx.Panel(self.windowSplitter, -1)
        self.notebookEditors = wx.Notebook(self.windowEditors, -1, style=0)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.onReload, id=11)
        self.Bind(wx.EVT_MENU, self.onSave, id=12)
        self.Bind(wx.EVT_MENU, self.onSaveAs, id=13)
        self.Bind(wx.EVT_MENU, self.onSaveAll, id=14)
        self.Bind(wx.EVT_MENU, self.onExit, id=15)
        self.Bind(wx.EVT_MENU, self.onHelpFind, id=21)
        self.Bind(wx.EVT_MENU, self.onHelpReplace, id=22)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ConfigManagerGui.__set_properties
        self.SetTitle("Picarro Configuration Manager")
        self.SetSize((1000, 600))
        self.frameMainStatusbar.SetStatusWidths([10, 30, -1])
        # statusbar fields
        frameMainStatusbar_fields = ["", "Modified", "Configuration Manager"]
        for i in range(len(frameMainStatusbar_fields)):
            self.frameMainStatusbar.SetStatusText(frameMainStatusbar_fields[i], i)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ConfigManagerGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizerNotebook = wx.BoxSizer(wx.HORIZONTAL)
        sizerTree = wx.BoxSizer(wx.HORIZONTAL)
        sizerTree.Add(self.treeCtrlFiles, 1, wx.EXPAND, 0)
        self.windowTree.SetSizer(sizerTree)
        sizerNotebook.Add(self.notebookEditors, 1, wx.EXPAND, 0)
        self.windowEditors.SetSizer(sizerNotebook)
        self.windowSplitter.SplitVertically(self.windowTree, self.windowEditors, 240)
        sizer_1.Add(self.windowSplitter, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def onReload(self, event): # wxGlade: ConfigManagerGui.<event_handler>
        print "Event handler `onReload' not implemented!"
        event.Skip()

    def onSave(self, event): # wxGlade: ConfigManagerGui.<event_handler>
        print "Event handler `onSave' not implemented!"
        event.Skip()

    def onSaveAs(self, event): # wxGlade: ConfigManagerGui.<event_handler>
        print "Event handler `onSaveAs' not implemented!"
        event.Skip()

    def onSaveAll(self, event): # wxGlade: ConfigManagerGui.<event_handler>
        print "Event handler `onSaveAll' not implemented!"
        event.Skip()

    def onExit(self, event): # wxGlade: ConfigManagerGui.<event_handler>
        print "Event handler `onExit' not implemented!"
        event.Skip()

    def onHelpFind(self, event): # wxGlade: ConfigManagerGui.<event_handler>
        print "Event handler `onHelpFind' not implemented!"
        event.Skip()

    def onHelpReplace(self, event): # wxGlade: ConfigManagerGui.<event_handler>
        print "Event handler `onHelpReplace' not implemented!"
        event.Skip()

# end of class ConfigManagerGui


if __name__ == "__main__":
    appConfigManager = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frameMain = ConfigManagerGui(None, -1, "")
    appConfigManager.SetTopWindow(frameMain)
    frameMain.Show()
    appConfigManager.MainLoop()
