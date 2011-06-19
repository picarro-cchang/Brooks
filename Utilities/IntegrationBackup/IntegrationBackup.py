"""
File Name: IntegrationBackup.py
Purpose:
    Clean and back up files in the final stage of integration and automation process in manufacturing

File History:
    01-28-11 Alex  Created

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

import os
import sys
import wx
import threading
import subprocess
import time
import stat
        
STANDARD_BUTTON_COLOR = wx.Colour(237, 228, 199)
EXTENSIONS_TO_KEEP = ["ini", "py", "bat", "zip"]
BACKUP_FOLDER = "AutoIntegration"
DEFAULT_SOURCE = "C:\\Picarro\\G2000\\InstrConfig\\Integration"
DEFAULT_TARGET = "Z:\\"
PASSWORD = "bl52l21fbl52l21f"

def removeFiles(pathToClean, exceptionList):
    for root, dirs, files in os.walk(pathToClean):
        for filename in files:
            filepath = os.path.join(root,filename)
            if os.path.basename(filename).split('.')[-1] not in exceptionList:
                try:
                    print filepath
                    os.chmod(filepath, stat.S_IREAD | stat.S_IWRITE)
                    os.remove(filepath)
                except OSError,errorMsg:
                    self._writeToStatus('ERROR: %s' % (errorMsg))
                            
def removeEmptyDirs(rootPath):
    emptyDirFound = False
    for root, dirs, files in os.walk(rootPath):
        for dirname in dirs:
            dirpath = os.path.join(root, dirname)
            try:
                os.chmod(dirpath, stat.S_IREAD | stat.S_IWRITE)
                os.rmdir(dirpath)
                emptyDirFound = True
            except:
                pass
    return emptyDirFound
    
class IntegrationBackupFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Integration Backup Tool")
        self.SetBackgroundColour("#E0FFFF")
        self.labelTitle = wx.StaticText(self, -1, "Integration Backup Tool", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        
        # Menu bar
        self.frameMenubar = wx.MenuBar()
        self.iHelp = wx.Menu()
        self.frameMenubar.Append(self.iHelp,"Help")
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "Integration Backup Tool", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)
        
        # Other graphical components
        self.staticLine = wx.StaticLine(self, -1)
        self.labelFooter = wx.StaticText(self, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        self.textCtrlSourceDir = wx.TextCtrl(self, -1, DEFAULT_SOURCE, style = wx.TE_READONLY)
        self.textCtrlSourceDir.SetMinSize((450,20))
        self.textCtrlTargetDir = wx.TextCtrl(self, -1, DEFAULT_TARGET, style = wx.TE_READONLY)
        self.textCtrlTargetDir.SetMinSize((450,20))
        self.labelStatus = wx.StaticText(self, -1, "Status")
        self.labelStatus.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.textCtrlStatus = wx.TextCtrl(self, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH)
        self.textCtrlStatus.SetMinSize((625,100))
        
        # Buttons
        self.buttonSourceDir = wx.Button(self, -1, "Source Directory", style=wx.BU_EXACTFIT)             
        self.buttonTargetDir = wx.Button(self, -1, "Target Directory", style=wx.BU_EXACTFIT) 
        self.buttonStart = wx.Button(self, -1, "Start", style=wx.BU_EXACTFIT)
        self.buttonClose = wx.Button(self, -1, "Close", style=wx.BU_EXACTFIT)
        self.buttonSourceDir.SetMinSize((157, 25))
        self.buttonSourceDir.SetBackgroundColour(STANDARD_BUTTON_COLOR)
        self.buttonSourceDir.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonTargetDir.SetMinSize((157, 25))
        self.buttonTargetDir.SetBackgroundColour(STANDARD_BUTTON_COLOR)
        self.buttonTargetDir.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonStart.SetMinSize((157, 25))
        self.buttonStart.SetBackgroundColour(STANDARD_BUTTON_COLOR)
        self.buttonStart.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonClose.SetMinSize((157, 25))
        self.buttonClose.SetBackgroundColour(STANDARD_BUTTON_COLOR)
        self.buttonClose.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(0, 2)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)

        sizer_1.SetMinSize((550,100))
        sizer_1.Add(self.labelTitle, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        sizer_1.Add(self.staticLine, 0, wx.EXPAND|wx.BOTTOM, 5)
        
        grid_sizer_1.Add(self.buttonSourceDir, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.textCtrlSourceDir, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        
        grid_sizer_1.Add(self.buttonTargetDir, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.textCtrlTargetDir, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        
        sizer_2.Add(self.labelStatus, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_2.Add((-1,5))
        sizer_2.Add(self.textCtrlStatus, 0, wx.LEFT|wx.RIGHT, 10)
        
        sizer_3.Add(self.buttonStart, 0, wx.LEFT, 140)
        sizer_3.Add(self.buttonClose, 0, wx.LEFT, 30)
        
        sizer_1.Add(grid_sizer_1, 0, wx.BOTTOM, 10)
        sizer_1.Add(sizer_2, 0, wx.BOTTOM, 20)
        sizer_1.Add(sizer_3, 0, wx.BOTTOM, 20)
        sizer_1.Add(self.labelFooter, 0, wx.EXPAND| wx.BOTTOM, 5)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

class IntegrationBackup(IntegrationBackupFrame):
    def __init__(self, *args, **kwds):
        self.statusMessage = []
        IntegrationBackupFrame.__init__(self, *args, **kwds)
        self.bindEvents()
        sourceDir = self.textCtrlSourceDir.GetValue()
        if os.path.isdir(sourceDir):
            self.sourceDir = sourceDir
            self.sourceZipDir = os.path.join(sourceDir, "zip")
            self.buttonStart.Enable(True)
        else:
            self.sourceDir = ""
            self.sourceZipDir = ""
            self.textCtrlSourceDir.SetValue("")
            self.buttonSourceDir.SetBackgroundColour("red")
            self.buttonStart.Enable(False)

        targetDir = self.textCtrlTargetDir.GetValue()
        if os.path.isdir(targetDir):
            self.targetDir = os.path.join(targetDir, BACKUP_FOLDER)
            self.textCtrlTargetDir.SetValue("%s (\'%s\' folder will be created automatically)" % (self.targetDir, BACKUP_FOLDER))
            self.buttonStart.Enable(True)
        else:
            self.targetDir = ""
            self.textCtrlTargetDir.SetValue("")
            self.buttonTargetDir.SetBackgroundColour("red")
            self.buttonStart.Enable(False)
        self.sourceZipPath = ""
            
    def bindEvents(self):
        self.Bind(wx.EVT_BUTTON, self.onSourceDirButton, self.buttonSourceDir)    
        self.Bind(wx.EVT_BUTTON, self.onTargetDirButton, self.buttonTargetDir)
        self.Bind(wx.EVT_BUTTON, self.onStartButton, self.buttonStart)
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.buttonClose)
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        
    def onCloseButton(self, evt):
        self.Destroy()
        
    def onStartButton(self, evt):
        launchCoordinatorThread = threading.Thread(target = self._start)
        launchCoordinatorThread.setDaemon(True)
        launchCoordinatorThread.start()
        self.buttonStart.Enable(False)
        self.buttonSourceDir.Enable(False)
        self.buttonTargetDir.Enable(False)
        self.buttonClose.Enable(False)
        
    def onSourceDirButton(self, evt):
        d = wx.DirDialog(None,"Select the source integration directory", style=wx.DD_DEFAULT_STYLE,
                         defaultPath=self.sourceDir)
        if d.ShowModal() == wx.ID_OK:
            self.sourceDir = d.GetPath()
            self.sourceZipDir = os.path.join(sourceDir, "zip")
            self.textCtrlSourceDir.SetValue(self.sourceDir)
            self.buttonSourceDir.SetBackgroundColour(STANDARD_BUTTON_COLOR)
            self.buttonStart.Enable(True)

    def onTargetDirButton(self, evt):
        d = wx.DirDialog(None,"Select the target integration directory", style=wx.DD_DEFAULT_STYLE,
                         defaultPath=self.targetDir)
        if d.ShowModal() == wx.ID_OK:
            self.targetDir = os.path.join(d.GetPath(), BACKUP_FOLDER)
            self.textCtrlTargetDir.SetValue("%s (\'%s\' folder will be created automatically)" % (self.targetDir, BACKUP_FOLDER))
            self.buttonTargetDir.SetBackgroundColour(STANDARD_BUTTON_COLOR)
            self.buttonStart.Enable(True)
            
    def onAboutMenu(self, evt):
        d = wx.MessageDialog(None, "Copyright 1999-2011 Picarro Inc. All rights reserved.\n\nVersion: 1.0.0\n\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc. (http://www.picarro.com)", "About Integration Backup Tool", wx.OK)
        d.ShowModal()
        d.Destroy()
        
    def _writeToStatus(self, message):
        self.statusMessage.append("%s   %s\n" % (self._getTime(), message,))
        self.statusMessage = self.statusMessage[-20:]
        self.textCtrlStatus.SetValue("".join(self.statusMessage))
        
    def _getTime(self, format=0):
        if format == 0:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        else:
            return time.strftime("%Y%m%d%H%M%S", time.localtime())
            
    def _backupFiles(self):
        self._writeToStatus("Copying integration files from %s to %s..." % (self.sourceDir, self.targetDir))
        if not os.path.isdir(self.targetDir):
            try:
                os.makedirs(self.targetDir)
            except:
                self._writeToStatus("Failed to create folder to back up integration files")
                return
        subprocess.call(["xcopy", "/E", "/Y", "/I", self.sourceDir, self.targetDir])
        
    def _zipEncryptedDir(self):
        self._writeToStatus("Zipping integration files...")
        if not os.path.isdir(self.sourceZipDir):
            try:
                os.makedirs(self.sourceZipDir)
            except:
                self._writeToStatus("Failed to create folder to store encrypted zip file")
                return
        targetFilename = "IntegrationBackup-%s.zip" % self._getTime(1)
        self.sourceZipPath = os.path.join(self.sourceZipDir,targetFilename)
        subprocess.call(["7z", "a", "-p"+PASSWORD,
                         "-r", "-xr!zip", self.sourceZipPath, self.sourceDir+"\\*"])
                      
        self._writeToStatus("Password-protected ZIP file was created in %s" % self.sourceZipPath)
  
    def _removeFilesAndDirs(self):
        # Remove files with specified extensions
        self._writeToStatus("Removing integration files in %s except for file extensions in %s..." % (self.sourceDir, EXTENSIONS_TO_KEEP))
        removeFiles(self.sourceDir, EXTENSIONS_TO_KEEP)
        
        # Removre empty directories after file cleaning
        # Repeat this until all empty directories are removed
        self._writeToStatus("Removing empty directories in %s..." % (self.sourceDir,))
        newEmptyDirsExist = removeEmptyDirs(self.sourceDir)
        while newEmptyDirsExist:
            newEmptyDirsExist = removeEmptyDirs(self.sourceDir)   
        
    def _start(self):
        self._backupFiles()
        self._zipEncryptedDir()
        self._removeFilesAndDirs()
        self._writeToStatus("Integration backup process completed")
        
        self.buttonStart.Enable(True)
        self.buttonSourceDir.Enable(True)
        self.buttonTargetDir.Enable(True)
        self.buttonClose.Enable(True)
        

if __name__ == "__main__" :
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = IntegrationBackup(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()